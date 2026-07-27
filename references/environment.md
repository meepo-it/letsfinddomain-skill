# Environment variables

Everything is configured through environment variables. Nothing is hardcoded,
and no credential ever needs to be committed.

## How the scripts read configuration

In priority order:

1. Variables already exported in your shell
2. A `.env` file in the repo root

A real shell variable always wins over `.env`, so you can override a single
value for one command without editing files:

```bash
DOMAIN_FINDER_MAX_PRICE=15 python3 scripts/check-domains.py --tlds com snapkit
```

Setup:

```bash
cp .env.example .env
$EDITOR .env
```

`.env` is listed in `.gitignore`. Keep it that way.

## Required: one availability provider

You need exactly one. Spaceship is the recommended default; the other two exist
so nobody is blocked by an account requirement.

### `SPACESHIP_API_KEY` + `SPACESHIP_API_SECRET` — recommended

Batch of 20 domains per request, free with any Spaceship account, no minimum
balance and no IP allowlist.

1. Sign up at <https://www.spaceship.com/>
2. Open the [API Manager](https://www.spaceship.com/application/api-manager/)
3. Create an API key — you get a key and a secret, both needed
4. Paste both into `.env`

The secret is shown once. If you lose it, generate a new pair.

### `NAMESILO_API_KEY` — alternative

Single key, free with any NameSilo account, accepts a comma-separated list of
domains.

Get it from the [API Manager](https://www.namesilo.com/account/api-manager).

### `DOMAIN_FINDER_ALLOW_RDAP` — no account at all

Set to `1` to enable the keyless RDAP fallback, which queries the public
registry data protocol directly. Useful for trying the skill out before
committing to an account.

**Read the caveat before relying on it.** RDAP cannot answer for every TLD —
notably `.io` and `.co` publish no RDAP server. For those the script reports
`no RDAP for this TLD` rather than guessing, because the failure mode would
otherwise be a *false available*. Details in
[`providers.md`](providers.md#rdap-no-credentials).

RDAP is also one HTTP request per domain, so it is much slower than the batch
providers on a long candidate list.

## Optional: pricing

**You do not need to configure anything for prices to work.** Porkbun publishes
its full TLD price list at a public endpoint that requires no credentials, and
the scripts use it by default, cached on disk for a day.

Those are Porkbun's list prices. They are accurate, current, and a good
reference — but your registrar's prices will differ by a dollar or two.

### `DOMAIN_FINDER_PRICE_SOURCE`

`porkbun` (default) · `dynadot` · `none`

Set to `none` to skip price lookups entirely (equivalent to passing
`--no-price`). Set to `dynadot` if you buy at Dynadot and want its exact
per-domain quotes, including premium pricing.

### `DYNADOT_API_KEY`

Only needed when `DOMAIN_FINDER_PRICE_SOURCE=dynadot`. Get it from
[Account → API Settings](https://www.dynadot.com/account/domain/setting/api.html).

Note the tradeoff: Dynadot quotes **one domain per request** and returns the
price as an English sentence that has to be parsed, so it is far slower than
Porkbun's single bulk call. Its advantage is exact per-domain premium quotes.

## Optional: defaults

These set defaults only. Every one can be overridden per command, and leaving
them unset means "no constraint" — the skill will not silently filter anything.

| Variable | Default | Effect |
|---|---|---|
| `DOMAIN_FINDER_DEFAULT_TLDS` | `com` | TLDs attached to bare names when `--tlds` is omitted |
| `DOMAIN_FINDER_MAX_PRICE` | unset | Hide available domains above this first-year price (USD) |
| `DOMAIN_FINDER_PRICE_TTL` | `86400` | Seconds to cache the Porkbun price list |

## Optional: rate limiting

Request budgets are enforced across separate runs and parallel processes.
[`rate-limits.md`](rate-limits.md) explains why that matters and how it works;
these are the knobs.

| Variable | Default | Effect |
|---|---|---|
| `DOMAIN_FINDER_CACHE_TTL` | `3600` | Availability cache lifetime in seconds. `0` disables |
| `DOMAIN_FINDER_SPACESHIP_LIMIT` | `25` | Requests per window (Spaceship documents 30) |
| `DOMAIN_FINDER_SPACESHIP_WINDOW` | `30` | Window length in seconds |
| `DOMAIN_FINDER_NAMESILO_LIMIT` | `20` | Requests per window |
| `DOMAIN_FINDER_NAMESILO_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_RDAP_LIMIT` | `60` | Requests per window |
| `DOMAIN_FINDER_RDAP_WINDOW` | `60` | Window length in seconds |

Lower the limits if another tool shares the key. Raising them above the
provider's documented figure only moves the throttling to their servers.

## Verifying your setup

```bash
python3 scripts/check-domains.py example.com
```

Expected: a table showing `example.com` as `taken`.

| Symptom | Cause |
|---|---|
| `No availability provider configured` | No credentials found — check `.env` exists and is in the repo root |
| `Spaceship error: ...401...` | Key/secret wrong, or secret truncated on paste |
| Everything reports `lookup failed` | Network or DNS problem, not a credential problem |
| `.io` shows `no RDAP for this TLD` | Expected on the RDAP fallback — configure a real provider |

## Security notes

- The scripts never write credentials to disk. `.cache/` holds only the public
  Porkbun price list, the public IANA RDAP TLD list, request timestamps for the
  rate limiter, and cached availability answers — no secrets.
- `.gitignore` covers `.env`, `*.key`, `*.secret`, and `ENV.md`.
- Availability and pricing lookups are read-only. Nothing here can spend money,
  transfer a domain, or change DNS.
- If you fork this repo and add write-capable endpoints, use a separate,
  scope-limited API key — not the one you use for lookups.
