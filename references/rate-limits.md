# Rate limits

Every registrar API is rate limited, and the way this skill gets used makes it
easy to hit those limits without noticing. This document explains what the
limits are, what the tooling does about them, and how to tune it.

## Why this needs real handling

The naive approach — sleep between batches inside one run — protects nothing,
because of how the skill is actually used:

- **An agent calls the script many times per session.** Generate 30 candidates,
  check, refine, check again, widen the TLD list, check again. Each of those is
  a *separate process*. An in-process sleep in run #1 knows nothing about the
  budget that run #2 is about to spend.
- **Agents run in parallel.** Fan out four subagents exploring four naming
  directions and you get four processes hammering the same API key at once.
- **The key may not be exclusively yours.** Another tool, a cron job, or a
  teammate can be spending the same account's budget concurrently.
- **A 429 in the middle of a run is not a failure to swallow.** A domain whose
  lookup failed is *not* confirmed available, and must never be presented as if
  it were.

## What the tooling does

### Persistent sliding-window limiter

Request timestamps are written to `.cache/ratelimit-<provider>.json`. Before
every request the script prunes timestamps older than the window, and if the
budget is already spent it sleeps until the oldest one ages out.

Because the window lives on disk rather than in memory, budget spent by one
invocation is still spent as far as the next invocation is concerned.

### Advisory file locking

The state file is guarded with `flock`. Parallel processes take turns on
read-modify-write, so six concurrent agents cannot each read "0 requests used"
and collectively fire six requests.

Verified behaviour with a budget of 3 requests per 15 seconds and six processes
launched simultaneously: three proceed immediately (spaced by the minimum
interval), the rest block until the window rolls over.

### Shared cooldown on 429

When a provider returns 429, the script writes a `cooldown_until` timestamp
into the shared state. Every other process — including ones started later —
parks until it expires. One worker getting throttled slows everyone down, which
is the correct behaviour; the alternative is the rest of the fleet continuing to
hammer an API that just said stop.

`Retry-After` is honoured when present. Otherwise backoff is exponential
(2s, 4s, 8s, 16s, capped at 60s) with random jitter so parallel workers
desynchronise instead of retrying in lockstep.

### Result cache

Availability results are cached in `.cache/availability.json` for one hour by
default. Overlapping re-checks — extremely common in an iterative naming
session — cost zero requests. Cached rows are labelled `cached` in the output so
nothing is silently stale.

Measured effect on a 50-domain re-check: 26.8s → 0.16s, 3 requests → 0.

Only `available` and `taken` are cached. Failures are never cached, so a
transient error does not poison later runs.

### Honest failure reporting

Domains whose lookup failed are reported separately:

```
> 3 domain(s) could not be resolved and are NOT confirmed available: foo.com, bar.io, baz.dev
```

They are excluded from `--available-only`, and the script exits with status `3`
so a caller can distinguish partial success from success.

### Cost preview

`--plan` shows the request count and time estimate without spending anything:

```console
$ python3 scripts/check-domains.py --plan --tlds com,ai,io,dev,app,xyz,net,org,co,me alpha beta gamma delta epsilon
provider:        spaceship
domains:         50 (0 cached, 50 to query)
requests:        3
budget:          25 requests / 30s
estimated time:  1s
```

Use it before a large sweep.

## Provider budgets

| Provider | Documented limit | Default used here | Domains per request |
|---|---|---|---|
| Spaceship | 30 requests / user / 30s | **25 / 30s** | 20 |
| NameSilo | not precisely published | **20 / 60s** (conservative) | ~20 (comma-separated) |
| RDAP (rdap.org) | shared public proxy, unpublished | **60 / 60s**, min 1s apart | 1 |
| Porkbun pricing | unpublished; called once/day | cached 24h | all TLDs at once |

The Spaceship default is deliberately below the documented 30 so that a second
tool sharing the key does not push the account over.

The RDAP figure is not a published limit — it is a politeness budget. `rdap.org`
is free infrastructure run for everyone's benefit; one request per second is the
least we can do.

## Tuning

| Variable | Default | Meaning |
|---|---|---|
| `DOMAIN_FINDER_SPACESHIP_LIMIT` | `25` | Max requests per window |
| `DOMAIN_FINDER_SPACESHIP_WINDOW` | `30` | Window length in seconds |
| `DOMAIN_FINDER_NAMESILO_LIMIT` | `20` | Max requests per window |
| `DOMAIN_FINDER_NAMESILO_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_RDAP_LIMIT` | `60` | Max requests per window |
| `DOMAIN_FINDER_RDAP_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_CACHE_TTL` | `3600` | Availability cache lifetime, seconds. `0` disables |

Lower the limits if you share a key. Raising them above what the provider
documents will simply move the throttling from this script to their servers,
where it costs you a 429 instead of a short sleep.

## Practical guidance

**Batch generously in a single call.** One call with 60 domains costs 3 requests.
Sixty calls with one domain each cost 60. Always pass the whole candidate list
at once:

```bash
# good — 3 requests
python3 scripts/check-domains.py --tlds com,ai,io alpha beta gamma delta ...

# bad — one request per domain, and 20x the wall-clock time
for d in alpha beta gamma; do python3 scripts/check-domains.py "$d.com"; done
```

**Narrow the TLD list before widening the name list.** Ten names across ten TLDs
is 100 domains. If the user only wants `.com`, checking the other nine is pure
waste.

**Don't disable the cache to "be safe".** An hour-old availability answer is
almost always still correct, and the label tells the user when a row came from
cache. If you genuinely need a fresh answer right before purchase, re-check that
single domain with `--no-cache`.

**Expect RDAP to be slow.** It is one request per domain with a one-second floor,
so 50 domains takes roughly a minute. It exists so people can try the skill
without an account, not as a production path.
