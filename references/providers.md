# Domain provider APIs

A survey of registrar and registry APIs that can answer "is this domain
available, and what does it cost" — what each requires, what it actually
returns, and where the traps are.

**Verification legend**

- ✅ **Verified live** — I called the endpoint and confirmed the behaviour described.
- 🔶 **Endpoint verified, response not** — the endpoint exists and the auth
  requirement was confirmed, but a valid credential was needed to see the full
  response shape.
- 📄 **Documentation only** — not called; taken from official docs. Treat as
  a starting point, not gospel.

Reviewed July 2026 against the official documentation linked below. Registrar
API policies change; re-check before relying on an eligibility claim.

---

## Summary

| Provider | Batch | Price in response | Account barrier | Status |
|---|---|---|---|---|
| **Spaceship** | 20/req | premium only | none | ✅ |
| **Porkbun** (pricing) | all TLDs | ✅ TLD list | **none — public** | ✅ |
| **Porkbun** (availability) | 1/req | ✅ registration | free account | ✅ |
| **NameSilo** | comma list via `/apibatch` | 📄 yes | free account | 🔶 |
| **Dynadot** | **1/req** | ✅ per-domain, as prose | free account | ✅ |
| **RDAP** | 1/req | ✗ | **none** | ✅ |
| **Namecheap** | 50/req | premium only | API access + IPv4 allowlist | ✅ |
| **Name.com** | 50/req | ✅ registration + renewal | free account | ✅ |
| **GoDaddy** | **50/req (client cap)** | ✅ registration; renewal via reference source | PAT | ✅ |
| **Cloudflare Registrar** | 20/req | ✅ supported extensions | account + billing setup | ✅ |
| **Gandi** | 1/req, async | unclear | free account | researched, not wired |
| **IONOS** | — | — | — | no stable public check API found |
| **Domainr** | 1/req | ✗ | free tier via RapidAPI | 🔶 |
| **Hostinger MCP** | 1 name × N TLDs | ✗ | Hostinger account | 🔶 |

**Implemented in this repo:** Spaceship, NameSilo, GoDaddy, Name.com,
Namecheap, Dynadot, Porkbun, Cloudflare Registrar, and optional RDAP for
availability. Porkbun and Dynadot also remain available as pricing sources.
Gandi, IONOS, Domainr, and Hostinger MCP are documented research leads but are
not selected automatically because their current API shape or account model is
less suitable for this read-only batch workflow.

---

## Spaceship

*Implemented — the recommended default.*

The best availability-per-request ratio with no account barrier.

```
POST https://spaceship.dev/api/v1/domains/available
X-Api-Key:    <key>
X-Api-Secret: <secret>
Content-Type: application/json

{"domains": ["example.com", "example.ai", "example.io"]}
```

```json
{"domains": [
  {"domain": "google.com",     "result": "taken",     "premiumPricing": []},
  {"domain": "zqxjkbwrm.com",  "result": "available", "premiumPricing": []}
]}
```

- **Batch:** 20 domains per request (hard limit)
- **Rate limit:** 30 requests per user per 30 seconds
- **Barrier:** none — free account, no minimum balance, no IP allowlist
- **Keys:** <https://www.spaceship.com/application/api-manager/>

### Gotchas

- `result` is `available` / **`taken`**. Not `unavailable`.
- `premiumPricing` is an **empty array** for ordinary domains, not a missing
  field. Don't test with `if "premiumPricing" in item`.
- **There is no ordinary-domain pricing.** I probed `/v1/domains/pricing`,
  `/v1/tlds/{tld}`, `/v1/tlds/{tld}/pricing` and `/v1/domains/{domain}/pricing`
  — all either 404 or resolve `pricing` as a domain-name path parameter.
  `/v1/domains/{domain}` returns `Domain not found for User`, i.e. it only
  covers domains you already own. Price has to come from elsewhere.

---

## Porkbun

*Implemented for availability and pricing.*

### Pricing — public, no credentials

```
POST https://api.porkbun.com/api/json/v3/pricing/get
```

No key, no account, no auth header at all. Returns **907 TLDs** with
registration, renewal and transfer prices.

```json
{"status": "SUCCESS", "pricing": {
  "com": {"registration": "11.08", "renewal": "11.08", "transfer": "11.08"},
  "ai":  {"registration": "82.70", "renewal": "82.70", "transfer": "165.09"},
  "io":  {"registration": "28.12", "renewal": "51.80", "transfer": "51.80"},
  "xyz": {"registration": "2.04",  "renewal": "12.98", "transfer": "12.98"}
}}
```

This solves the pricing gap with zero configuration, and it exposes the thing
that actually costs people money: **the renewal cliff**. `.xyz` is $2.04 the
first year and $12.98 every year after — a 6.4x jump. `.io` nearly doubles.
A tool that only shows first-year prices is actively misleading, so this repo
shows both and flags jumps above 1.5x.

Caveat: these are Porkbun's list prices. Your registrar will differ by a dollar
or two. They are a reference, not a quote.

### Availability — requires a key

```
POST https://api.porkbun.com/api/json/v3/domain/checkDomain/{domain}
```

One domain per request. Set `PORKBUN_API_KEY` and `PORKBUN_SECRET_API_KEY` from
[Account → API Access](https://porkbun.com/account/api). It returns a current
registration price; renewal is filled from the selected reference source when
the endpoint does not provide one.

---

## NameSilo

*Implemented as the alternative availability provider.*

```
GET https://www.namesilo.com/apibatch/checkRegisterAvailability
      ?version=1&type=json&key=<key>&domains=example.com,example.net
```

- **Batch:** comma-separated list
- **Automated traffic:** NameSilo requires batch use to go through `/apibatch`;
  using the standard `/api` URI for repetitive traffic can trigger limiting or
  suspension. See the [official batch policy](https://www.namesilo.com/support/v2/articles/account-options/api-automated-batch).
- **Rate:** no fixed public number; this skill uses one in-flight request and a
  conservative 20 requests/60 seconds budget.
- **Barrier:** free account, single API key, no IP allowlist
- **Key:** <https://www.namesilo.com/account/api-manager>
- **Response:** `reply.code` `300` means success; results split into
  `available` / `unavailable` / `invalid` buckets

Verified that the endpoint exists and rejects a bad key with
`{"code":"110","detail":"Invalid API Key (Permission denied)"}`. The exact
success-response shape and whether a `price` attribute is returned per domain
were **not** verified — I had no NameSilo account. The parser in
`check-domains.py` handles the documented shape and degrades to `unknown`
rather than guessing.

---

## Dynadot

*Implemented for availability and as the optional exact-pricing source.*

```
GET https://api.dynadot.com/api3.json
      ?key=<key>&command=search&domain0=example.com&show_price=1&currency=USD
```

```json
{"SearchResponse": {"ResponseCode": "0", "SearchResults": [{
  "DomainName": "example.com", "Available": "yes",
  "Price": "Registration Price: 10.88 in USD and Renewal price: 10.88 in USD and Domain is not a Premium Domain"
}]}}
```

### Gotchas

- **Account tier matters.** Dynadot documents Regular (1 thread, 60/min), Bulk
  (5 threads, 600/min), Super Bulk (35 threads, 6000/min), and Premium Bulk
  (25 threads, 6000/min). The checker defaults to the Regular-safe one-thread,
  one-second path rather than assuming a higher tier.
- **The price is an English sentence**, not structured fields. You have to
  regex the numbers out of it.
- `ResponseCode` is `0` for success and `-1` for failure — note that `0` is
  success here, which is the opposite of the usual convention.

Its redeeming feature is exact per-domain quotes including premium pricing,
which the TLD price list cannot give you.

For availability, the script sends one `domain0` per request so the result and
price mapping stays deterministic across account tiers. Higher-tier users can
raise the client budget explicitly after reviewing the official limits.

---

## RDAP (no credentials)

*Implemented as the keyless fallback.*

The IETF replacement for WHOIS. Every gTLD registry is required to run one.

```
GET https://rdap.org/domain/example.com
```

- **404** → no registration record → available
- **200** → registered → taken

`rdap.org` is a public proxy that resolves the right registry server for you
using the IANA bootstrap file.

### The trap that makes this dangerous

**A TLD with no RDAP server also returns 404.** That is indistinguishable from
"available" unless you check first. Verified:

| Domain | Reality | rdap.org |
|---|---|---|
| `openai.com` | registered | 200 ✅ |
| `claude.ai` | registered | 200 ✅ |
| `vercel.app` | registered | 200 ✅ |
| **`github.io`** | **registered** | **404 ← false "available"** |
| **`google.co`** | **registered** | **404 ← false "available"** |

`.io` and `.co` publish no RDAP server. The IANA bootstrap file
(<https://data.iana.org/rdap/dns.json>) lists **1200** TLDs that do; anything
outside that list cannot be answered.

`check-domains.py` fetches the bootstrap list, caches it for a week, and
reports `no RDAP for this TLD` for uncovered TLDs instead of guessing. **Any
RDAP-based checker that skips this step will tell you `github.io` is available.**

Also note: RDAP answers "is there a registration record", which is not exactly
"can I buy this". Reserved, blocked, and premium names can show as available.

---

## Namecheap

*Implemented — useful when the account already has API access enabled.*

```
GET https://api.namecheap.com/xml.response
      ?ApiUser=..&ApiKey=..&UserName=..&ClientIp=..
      &Command=namecheap.domains.check&DomainList=a.com,b.com
```

- **Batch:** up to 50 domains per call
- **Response:** XML, not JSON
- **Setup:** Profile → Tools → Business & Dev Tools → Manage Namecheap API
  Access, enable API access, and allowlist the machine's IPv4 address.
- **Prices:** premium registration and renewal prices are returned; ordinary
  domains do not include a direct quote, so the selected reference source is
  used for those.

The IP allowlist makes this a poor default for laptops with changing public IPs.

---

## GoDaddy

*Implemented — bulk availability and first-year quotes.*

```text
POST https://api.godaddy.com/v1/domains/available
Authorization: Bearer <personal-access-token>
["example.com", "example.net"]
```

Create a Personal Access Token in the [GoDaddy Developer Portal](https://developer.godaddy.com/en/docs/api-users/auth/how-to)
and give it the `domains.domain:read` scope. The v1 bulk response includes
`available`, `domain`, and the first-year `price`. The checker caps batches at
50 names and uses the TLD price source for renewal reference data. GoDaddy's
rate-limit headers are treated as authoritative because their published window
values can change.

---

## Name.com

*Implemented — direct registration and renewal quotes.*

```
POST https://api.name.com/core/v1/domains:checkAvailability
{"domainNames": ["example.com"], "purchaseType": "registration"}
```

Basic-auth with username + API token. The documented maximum is 50 names per
request. Results include `purchasable`, `premium`, `purchasePrice`, and
`renewalPrice`. Create the token in [Account Settings → API Tokens](https://www.name.com/account/settings/api).

---

## Gandi

Gandi has a documented `domain.available()` XML-RPC method, but it is
asynchronous: callers must start a check and poll its task result. I did not
find a current, stable REST endpoint that combines availability with a direct
renewal quote, so it is intentionally not wired into this standard-library
script. See the [Gandi RPC domain usage documentation](https://doc.rpc.gandi.net/domain/usage.html)
if Gandi is your registrar.

---

## Domainr

```
GET https://api.domainr.com/v2/status?domain=example.com&client_id=<id>
```

Confirmed live that it exists and returns `401 Unauthorized` without a key.
Distributed through RapidAPI with a free tier.

Its distinguishing feature is a much richer status vocabulary than
available/taken — `undelegated`, `premium`, `marketed`, `reserved`,
`disallowed`, `tld` and more. Useful when you care *why* a name is
unavailable, or want to surface aftermarket listings. It does not quote
registration prices.

---

## Hostinger MCP

Not an HTTP API but an official MCP server, so an agent can call it directly
with no code:

```
domains_checkDomainAvailabilityV1(domain="snapkit", tlds=["com","ai","io"],
                                  with_alternatives=false)
```

- **Shape:** one bare name × many TLDs (the inverse of Spaceship's many-names
  batching)
- **Rate limit:** 10 requests/minute — tight
- `with_alternatives=true` returns suggestions, but only when exactly one TLD
  is given
- Requires a Hostinger account token; returned `Unauthenticated` in my test

Worth knowing about if you are already in the Hostinger ecosystem. The 10/min
ceiling makes it unsuitable for large sweeps.

---

## Cloudflare Registrar

*Implemented, but not the best default for a general naming sweep.*

```http
POST https://api.cloudflare.com/client/v4/accounts/{account_id}/registrar/domain-check
Authorization: Bearer <api-token>
{"domains": ["example.com"]}
```

- **Batch:** up to 20 domains per request
- **Response:** `registrable`, reason, registration cost, renewal cost, and
  tier for supported extensions
- **Setup:** Cloudflare account ID, Registrar-scoped API token, billing profile,
  default payment method, registrant contact, and registration agreement
- **Limit:** Cloudflare's Registrar API is beta and only exposes extensions it
  can register; premium registration is not supported through this API

For unsupported extensions the script reports `not supported by this provider`,
never `available`.

---

## Not wired: other researched platforms

- **Gandi** — official availability exists as an asynchronous XML-RPC method;
  no simple stable REST + renewal-price path was verified for this script.
- **IONOS** — no stable public availability API path was verified in the
  official material reviewed.
- **Domainr** — useful status taxonomy through RapidAPI, but no registrar price
  and a separate API account; not ideal for a purchase-oriented answer.
- **Hostinger** — official MCP availability tool, not a standard REST provider;
  its 10 requests/minute limit is tight for large sweeps.
- **Google Domains** — shut down; the business was sold to Squarespace in 2023.
- **Scraping registrar search pages** — brittle, usually against the terms of
  service, and unnecessary given how many free APIs exist.

---

## Adding a provider

A provider is one function with a fixed signature:

```python
def check_yourprovider(domains: list[str], limiter, quiet: bool) -> dict:
    """Return {domain: {"status": "available"|"taken"|"unknown"|"error",
                        "premium": bool}}"""
```

1. Write the function in `scripts/check-domains.py`, using
   `request_json(..., limiter=limiter)` for every call so it inherits rate
   limiting, retries and 429 backoff for free.
2. Register it in the `PROVIDERS` dict and in `pick_provider()`.
3. Add its budget to `RATE_LIMITS` as `(max_requests, window_seconds, min_interval)`.
4. Add its batch size to `requests_needed()` so `--plan` estimates correctly.
5. Document the credential in `.env.example` and
   [`environment.md`](environment.md).

Two rules that matter more than the code:

- **Never map an ambiguous response to `available`.** Use `unknown`. A false
  `taken` costs the user a good name; a false `available` costs them a
  purchase attempt and their trust in the tool.
- **Report what you couldn't resolve.** Silence reads as "all clear".
