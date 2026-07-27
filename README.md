# domain-finder-skill

**English** · [简体中文](README.zh-CN.md)

A Claude Code skill for finding domain names you can actually register:
generate candidates, check availability in bulk, and see both the first-year
and the renewal price before you commit.

```console
$ python3 scripts/check-domains.py --tlds com,ai,io,dev,xyz zqxjkbwrm
  checking 5 domain(s) via spaceship in 1 request(s)…
| Domain          | Status    | Reg. (1st yr) | Renewal | Note                        |
|-----------------|-----------|---------------|---------|-----------------------------|
| zqxjkbwrm.com   | available | $11.08        | $11.08  |                             |
| zqxjkbwrm.ai    | available | $82.70        | $82.70  |                             |
| zqxjkbwrm.io    | available | $28.12        | $51.80  | renewal 1.8x the first year |
| zqxjkbwrm.dev   | available | $8.75         | $12.87  |                             |
| zqxjkbwrm.xyz   | available | $2.04         | $12.98  | renewal 6.4x the first year |
```

That last column is the point. `.xyz` looks like a $2 domain and is a $13
domain.

## Why this exists

Most domain checkers get one of these wrong:

- **They show you a promo price.** A `.xyz` at $2.04 renewing at $12.98 is a 6.4x
  jump. This shows both columns and flags the cliff.
- **They lie about availability.** RDAP-based checkers report `github.io` as
  available, because `.io` publishes no RDAP server and "no server" is
  indistinguishable from "no record" if you don't check first. This checks first,
  and says *unsupported* rather than guessing.
- **They ignore rate limits.** An agent runs the checker many times per session,
  sometimes in parallel. An in-process sleep protects none of those runs from
  each other. This persists its request budget to disk under a lock.
- **They have opinions about your name.** No length rules, no price ceilings, no
  TLD ranking here. Those are yours.

## Requirements

Python 3.8+. No third-party packages — standard library only.

## Install

```bash
git clone https://github.com/meepo-it/domain-finder-skill.git
cd domain-finder-skill
cp .env.example .env
```

Put a Spaceship API key and secret in `.env` — free account, no minimum
balance, no IP allowlist:

```bash
SPACESHIP_API_KEY=your_key
SPACESHIP_API_SECRET=your_secret
```

Verify:

```bash
python3 scripts/check-domains.py example.com   # should report: taken
```

No account handy? `DOMAIN_FINDER_ALLOW_RDAP=1` enables a keyless fallback — but
read [the caveat](references/providers.md#rdap-no-credentials) first, because it
cannot answer for `.io` or `.co`.

Alternatives and full details: [`references/environment.md`](references/environment.md).

### Use it as a Claude Code skill

```bash
ln -s "$(pwd)" ~/.claude/skills/domain-finder
```

Then ask Claude for domain ideas and it will pick the skill up. `SKILL.md` is
the entry point.

## Usage

```bash
# specific domains
python3 scripts/check-domains.py acme.com acme.io

# bare names crossed with TLDs
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgehub

# only what's registrable, under budget
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20

# preview request cost before a big sweep
python3 scripts/check-domains.py --plan --tlds com,ai,io,dev $(cat names.txt)

# machine-readable
python3 scripts/check-domains.py --json acme.com
```

### Generate candidates

```bash
python3 scripts/gen-names.py --roots snap,clip,vault,pix --suffixes ify,ly,kit \
  --max-len 6 | python3 scripts/check-domains.py --tlds com --available-only
```

```console
$ python3 scripts/gen-names.py --roots mock,clip,blur --prefixes up,re,un \
    --patterns prefix+root --max-len 8
upmock  upclip  upblur
remock  reclip  reblur
unmock  unclip  unblur
```

Patterns: `root+suffix`, `prefix+root`, `prefix+root+suffix`, `root+root`,
`blend` (overlap two roots — `design` + `ignite` → `designite`).

More constraint-to-command mappings — "only .com", "max 6 characters",
"ending in -ify", "under $20" — in
[`references/query-recipes.md`](references/query-recipes.md).

## Options

| Flag | Effect |
|---|---|
| `--tlds com,ai,io` | TLDs to attach to bare names. Default `com` |
| `--available-only` | Only print registrable domains |
| `--max-price N` | Hide available domains above this first-year price (USD) |
| `--no-price` | Skip the price lookup |
| `--no-cache` | Ignore cached results and re-query |
| `--plan` | Show request count and time estimate, then exit |
| `--json` | JSON output |
| `--quiet` | Suppress progress messages |

Exit codes: `0` all resolved · `1` no valid input · `2` no provider configured ·
`3` partial — some lookups failed and are **not** confirmed available.

## How it works

| Concern | Source | Credentials |
|---|---|---|
| Availability | Spaceship (20 domains/request) | free account |
| — alternative | NameSilo | free account |
| — fallback | RDAP via `rdap.org` | **none** |
| Pricing | Porkbun's public TLD price list — 907 TLDs | **none** |
| — optional | Dynadot, exact per-domain quotes | free account |

Data sources are pluggable and pricing works out of the box, because Porkbun
publishes its whole price list at an endpoint that needs no authentication.

Eleven providers were surveyed — what each requires, what it actually returns,
and which ones have traps — in
[`references/providers.md`](references/providers.md).

## Rate limiting

The part most tools skip. Briefly:

- **Budgets persist to disk**, so a request spent by one run is spent as far as
  the next run is concerned.
- **`flock` guards the state**, so parallel agents take turns instead of each
  reading "0 used" and firing at once.
- **A 429 parks every process**, via a shared cooldown, honouring `Retry-After`
  with exponential backoff and jitter.
- **Results are cached for an hour**, so overlapping re-checks cost nothing.
  A 50-domain re-check: 26.8s → 0.16s, 3 requests → 0.
- **Failures are reported, never swallowed.** A domain that failed to resolve is
  not "available".

Reasoning, measurements and tuning knobs:
[`references/rate-limits.md`](references/rate-limits.md).

## Documentation

| File | Contents |
|---|---|
| [`SKILL.md`](SKILL.md) | Skill entry point — the workflow Claude follows |
| [`references/environment.md`](references/environment.md) | Every variable, where each credential comes from |
| [`references/providers.md`](references/providers.md) | Registrar API survey, verified behaviour, traps |
| [`references/rate-limits.md`](references/rate-limits.md) | Limits, what the tooling does, how to tune |
| [`references/query-recipes.md`](references/query-recipes.md) | Constraints → exact commands |
| [`references/naming-guide.md`](references/naming-guide.md) | Word roots, affixes, combination patterns |

## Scope

Read-only. This checks availability and prices; it does not buy, transfer, or
change DNS. Purchases happen at your registrar under your own account.

Availability is a lookup, not a guarantee. Registry reservations, premium
pricing, and trademark disputes are all outside what any API reports. Re-check
with `--no-cache` immediately before buying.

## Contributing

Adding a provider is one function plus a dict entry — see
[Adding a provider](references/providers.md#adding-a-provider). Two rules there
matter more than the code:

- Never map an ambiguous response to `available`. Use `unknown`.
- Report what you could not resolve. Silence reads as "all clear".

Corrections to the provider survey are especially welcome — registrar API
policies change, and the eligibility rules in that table are the part most
likely to go stale.

## License

MIT
