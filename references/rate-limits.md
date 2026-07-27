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

### Advisory file locking and in-flight gates

The state file is guarded with `flock`. Parallel processes take turns on
read-modify-write, so six concurrent agents cannot each read "0 requests used"
and collectively fire six requests.

Verified behaviour with a budget of 3 requests per 15 seconds and six processes
launched simultaneously: three proceed immediately (spaced by the minimum
interval), the rest block until the window rolls over.

The checker also holds `.cache/inflight-<provider>.lock` for the duration of
each HTTP request. The implementation is sequential inside one run and allows
only one in-flight request per provider across processes. This is intentional:
the provider rules below describe account/thread limits, not a license to run
`gather()` against every registrar at once. Dynadot explicitly documents a
one-thread regular account, and the other providers do not publish a general
concurrency guarantee.

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
availability requests: 3
budget:          25 requests / 30s
estimated time:  1s
```

Use it before a large sweep.

## Provider policies

The first column is what the provider currently documents. “Tool default” is a
deliberately lower client budget, not a claim about the provider's quota. If a
provider exposes response headers, those headers and `Retry-After` win at
runtime. Sources are official documentation and were checked on 2026-07-27.

| Provider | Official rule | Tool default / concurrency | Batch shape |
|---|---|---|---|
| Spaceship | 30 requests/user/30s; single-domain endpoint also caps 5/domain/300s | 25/30s; 1 in flight | 20 domains/request |
| NameSilo | No fixed number published; automated batch traffic must use `/apibatch` | 20/60s; 1 in flight | 20 domains/request, `/apibatch` |
| GoDaddy | Per-credential window; current rate-limit guide reports 600 per ~23-minute window and says values can change; other reference pages still say 60/min | 540/1380s; 1 in flight; honor server headers | 50 domains/request via v1 bulk endpoint |
| Name.com | 20 requests/s and 3,000 requests/hour account-wide | 20/60s; 1 in flight | 50 domains/request |
| Namecheap | 50/min, 700/hour, 8,000/day across the whole key | 45/60s; 1 in flight | 50 domains/request |
| Dynadot | Regular: 1 thread, 60/min; Bulk: 5 threads, 600/min; Super Bulk: 35 threads, 6,000/min | Regular-safe default: 55/60s, 1s gap, 1 in flight | one search request/domain |
| Porkbun | Some endpoints are rate limited; no universal number published; use `X-RateLimit-*` and reset data | 60/60s; 1 in flight | one domain/request |
| Cloudflare API / Registrar | 1,200/5m per user/account token, 200/s per IP; Registrar check max 20 domains/request | 180/60s; 1 in flight | 20 domains/request |
| RDAP (`rdap.org`) | No shared public quota guaranteed | 60/60s, 1s gap; 1 in flight | one domain/request |
| Porkbun pricing | Endpoint-specific limits; fetched once and cached | shared Porkbun gate; cached 24h | all TLDs in one request |

Official references:

- [Spaceship API](https://docs.spaceship.dev/) — availability limit and 1–20 domain batch.
- [NameSilo automated batch policy](https://www.namesilo.com/support/v2/articles/account-options/api-automated-batch) — `/apibatch` requirement.
- [GoDaddy rate-limit guide](https://developer.godaddy.com/en/docs/api-users/rate-limits) and [bulk availability endpoint](https://developer.godaddy.com/en/docs/references/rest/domains/v1/find-domains).
- [Name.com Core API overview](https://docs.name.com/api/v1/overview) and [FAQ](https://docs.name.com/resources/faq).
- [Namecheap API FAQ](https://www.namecheap.com/support/knowledgebase/article.aspx/9739/63/api-faq/).
- [Dynadot API command list](https://www.dynadot.com/domain/api-commands).
- [Porkbun API documentation](https://porkbun.com/api/json/v3/documentation/interactive).
- [Cloudflare API 429 limits](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/4xx-client-error/error-429/) and [Registrar domain check](https://developers.cloudflare.com/api/resources/registrar/methods/check).

The RDAP figure is not a published limit; it is a politeness budget for shared
public infrastructure. “Unknown” or “lookup failed” remains unresolved and is
never presented as available.

## Tuning

| Variable | Default | Meaning |
|---|---|---|
| `DOMAIN_FINDER_SPACESHIP_LIMIT` | `25` | Max requests per window |
| `DOMAIN_FINDER_SPACESHIP_WINDOW` | `30` | Window length in seconds |
| `DOMAIN_FINDER_NAMESILO_LIMIT` | `20` | Max requests per window |
| `DOMAIN_FINDER_NAMESILO_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_GODADDY_LIMIT` | `540` | Max requests per window; server headers are authoritative |
| `DOMAIN_FINDER_GODADDY_WINDOW` | `1380` | Conservative approximation of the current ~23-minute window |
| `DOMAIN_FINDER_NAMECOM_LIMIT` | `20` | Max requests per window |
| `DOMAIN_FINDER_NAMECOM_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_NAMECHEAP_LIMIT` | `45` | Max requests per window; below the official 50/min |
| `DOMAIN_FINDER_NAMECHEAP_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_RDAP_LIMIT` | `60` | Max requests per window |
| `DOMAIN_FINDER_RDAP_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_DYNADOT_LIMIT` | `55` | Regular-account-safe budget; bulk tiers may override |
| `DOMAIN_FINDER_DYNADOT_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_PORKBUN_LIMIT` | `60` | Max requests per window |
| `DOMAIN_FINDER_PORKBUN_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_CLOUDFLARE_LIMIT` | `180` | Client budget below the global 1200/5m token limit |
| `DOMAIN_FINDER_CLOUDFLARE_WINDOW` | `60` | Window length in seconds |
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
