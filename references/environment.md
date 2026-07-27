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

For the user-facing 1/2/3 setup walkthroughs with screenshots, use the provider
guides in [`docs/providers/`](../docs/providers/). This file remains the complete
configuration reference, including every environment variable and fallback.

## Required: one availability provider

You need exactly one. Spaceship is the default availability provider and the
simplest batch option; the others are useful when you already buy domains from
that registrar. The script chooses the first configured provider in this order,
so Spaceship wins whenever its two variables are present:

`Spaceship → NameSilo → GoDaddy → Name.com → Namecheap → Dynadot → Porkbun → Cloudflare → RDAP`

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
domains. Automated/repetitive requests use the `/apibatch` endpoint; this is a
NameSilo policy requirement, not an optional optimization.

Get it from the [API Manager](https://www.namesilo.com/account/api-manager).

### `GODADDY_PAT` — GoDaddy

GoDaddy's v1 availability endpoint accepts an array of domains. The checker
uses batches of up to 50 to avoid spending one request per candidate. The bulk
response gives the first-year quote; renewal reference data comes from the
selected price source. GoDaddy's server `RateLimit-*` headers are honored.

1. Sign in to the [GoDaddy Developer Portal](https://developer.godaddy.com/)
2. Open **API Users → Personal Access Tokens**
3. Choose **Generate Token** and grant the `domains.domain:read` scope
4. Copy the token immediately; GoDaddy displays it once
5. Set `GODADDY_PAT` in `.env`

The script only calls the read endpoint; it cannot purchase or modify domains.

### `NAMECOM_USERNAME` + `NAMECOM_API_TOKEN` — Name.com

Name.com supports up to 50 domains per request and returns `purchasable`,
premium status, registration price, and renewal price.

1. Sign in to [Name.com](https://www.name.com/)
2. Open **Account Settings → API Tokens**
3. Create a token at <https://www.name.com/account/settings/api>
4. Set `NAMECOM_USERNAME` and `NAMECOM_API_TOKEN` in `.env`

### Namecheap — XML API and IPv4 allowlist

Namecheap supports up to 50 domains per availability request, but setup is more
involved than the providers above.

1. Open **Profile → Tools → Business & Dev Tools → Manage Namecheap API Access**
2. Enable API access and confirm the account password
3. Add the public IPv4 address of the machine running the skill to the allowlist
4. Copy the API username and key into `NAMECHEAP_API_USER`,
   `NAMECHEAP_USERNAME`, and `NAMECHEAP_API_KEY`
5. Put the same allowlisted IPv4 in `NAMECHEAP_CLIENT_IP`

The official API page is
[Namecheap API introduction](https://www.namecheap.com/support/api/intro/).
Namecheap returns XML. Standard domains do not include a direct price in this
method; premium domains do. The default Porkbun or optional Dynadot pricing
source can fill ordinary reference prices.

### `DYNADOT_API_KEY` — Dynadot

Dynadot's `search` command supports one domain per request for regular accounts
and can include a current price sentence.

1. Sign in to [Dynadot](https://www.dynadot.com/)
2. Open **Account Control Panel → Tools → API**
3. Create or copy the API key
4. Set `DYNADOT_API_KEY` in `.env`

The setup page and command reference are in the
[Dynadot API documentation](https://www.dynadot.com/domain/api-commands).

### `PORKBUN_API_KEY` + `PORKBUN_SECRET_API_KEY` — Porkbun

Porkbun's availability check is one domain per request and returns a current
registration price. Its public TLD price list needs no key and remains the
default reference-price source.

1. Sign in to [Porkbun](https://porkbun.com/)
2. Open [Account → API Access](https://porkbun.com/account/api)
3. Create an API key pair and copy the secret immediately
4. Set `PORKBUN_API_KEY` and `PORKBUN_SECRET_API_KEY` in `.env`

### `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` — Cloudflare Registrar

Cloudflare supports up to 20 domains per check and returns registrability and
registration/renewal costs where supported. Its Registrar API is beta and only
covers extensions Cloudflare can register. The account also needs a billing
profile, default payment method, default registrant contact, and registration
agreement before the Registrar API can be used.

1. Open the Cloudflare dashboard and copy the **Account ID** for the account
2. Open **My Profile → API Tokens → Create Token**
3. Create a token with the Registrar permissions described in the
   [Cloudflare Registrar API guide](https://developers.cloudflare.com/registrar/registrar-api/)
4. Set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` in `.env`

For a general-purpose naming sweep, Spaceship, Name.com, or GoDaddy is usually
less restrictive.

### `DOMAIN_FINDER_ALLOW_RDAP` — optional trial fallback

Set to `1` to enable the keyless RDAP fallback, which queries the public
registry data protocol directly. This is useful for trying the skill out, but
is not the recommended production path: RDAP reports registration records, not
guaranteed purchasability, and does not provide premium or checkout pricing.

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
| `DOMAIN_FINDER_PRICE_TTL` | `86400` | Seconds to cache price data |

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
| `DOMAIN_FINDER_GODADDY_LIMIT` | `540` | Headroom below the current ~600/23m window; headers win |
| `DOMAIN_FINDER_GODADDY_WINDOW` | `1380` | Conservative window in seconds |
| `DOMAIN_FINDER_NAMECOM_LIMIT` | `20` | Conservative client-side request budget |
| `DOMAIN_FINDER_NAMECOM_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_NAMECHEAP_LIMIT` | `45` | Below the official 50/min key limit |
| `DOMAIN_FINDER_NAMECHEAP_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_RDAP_LIMIT` | `60` | Requests per window |
| `DOMAIN_FINDER_RDAP_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_DYNADOT_LIMIT` | `55` | Regular-account-safe availability/pricing budget |
| `DOMAIN_FINDER_DYNADOT_WINDOW` | `60` | Dynadot window in seconds; one request is spaced 1s apart |
| `DOMAIN_FINDER_PORKBUN_LIMIT` | `60` | Conservative client-side request budget |
| `DOMAIN_FINDER_PORKBUN_WINDOW` | `60` | Window length in seconds |
| `DOMAIN_FINDER_CLOUDFLARE_LIMIT` | `180` | Below the global 1200/5m token limit |
| `DOMAIN_FINDER_CLOUDFLARE_WINDOW` | `60` | Window length in seconds |

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
