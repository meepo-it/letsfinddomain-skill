# domain-finder-skill

**English** · [简体中文](README.zh-CN.md)

Find domain names you can actually register. Generate candidates, check
availability in bulk, and see the **renewal** price — not just the promo price.

Works with Claude Code, Codex, Cursor, Copilot, Gemini CLI, Aider, Windsurf and
Zed. Or just use it from your terminal.

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

That last column is the point. `.xyz` looks like a $2 domain. It's a $13 domain.

## Contents

- [Quick start](#quick-start)
- [Install for your AI tool](#install-for-your-ai-tool)
- [Common tasks](#common-tasks)
- [Command reference](#command-reference)
- [What it's built on](#what-its-built-on)
- [Design notes](#design-notes)
- [Documentation](#documentation)
- [Scope and limits](#scope-and-limits)
- [Contributing](#contributing)

## Quick start

Needs Python 3.8+. No third-party packages.

**1. Clone**

```bash
git clone https://github.com/meepo-it/domain-finder-skill.git
cd domain-finder-skill
cp .env.example .env
```

**2. Add a key**

Sign up at [Spaceship](https://www.spaceship.com/) — free, no minimum balance,
no IP allowlist — and create a key in the
[API Manager](https://www.spaceship.com/application/api-manager/). Put both
values in `.env`:

```bash
SPACESHIP_API_KEY=your_key
SPACESHIP_API_SECRET=your_secret
```

**3. Verify**

```bash
python3 scripts/check-domains.py example.com     # → taken
```

That's it.

<details>
<summary>Don't want to sign up for anything?</summary>

Set `DOMAIN_FINDER_ALLOW_RDAP=1` in `.env` to use a keyless fallback that
queries registry data directly.

It cannot answer for `.io` or `.co` — those registries publish no RDAP server —
and it's one request per domain, so it's slow. Fine for trying things out.
[Details](references/providers.md#rdap-no-credentials).

</details>

Other providers (NameSilo, Dynadot) and every configuration option:
[`references/environment.md`](references/environment.md).

## Install for your AI tool

Clone the repo somewhere your project can reach — these examples assume
`tools/domain-finder-skill/`.

### Claude Code

Symlink it into your skills directory. It loads on demand, so it costs no
context until it's used:

```bash
ln -s "$PWD/tools/domain-finder-skill" ~/.claude/skills/domain-finder
```

Then just ask for domain ideas. Entry point is [`SKILL.md`](SKILL.md).

### Codex, Gemini CLI, Aider, Windsurf, Zed

These read [`AGENTS.md`](AGENTS.md), the cross-tool standard. Append the
pointer snippet to your project's `AGENTS.md`:

```bash
cat tools/domain-finder-skill/install/agents-snippet.md >> AGENTS.md
```

Appends as-is, nothing to edit. For a global install instead of per-project,
append it to `~/.codex/AGENTS.md`.

### Cursor

Copy the ready-made rule. It uses `alwaysApply: false` with a description, so
Cursor pulls it in only when the conversation is about naming — no permanent
context cost:

```bash
mkdir -p .cursor/rules
cp tools/domain-finder-skill/install/domain-finder.mdc .cursor/rules/
```

Cursor also reads `AGENTS.md`, so the snippet above works too. The rule file
gives you finer control over when it activates.

### GitHub Copilot

```bash
mkdir -p .github
cat tools/domain-finder-skill/install/agents-snippet.md >> .github/copilot-instructions.md
```

### Anything else

The scripts are ordinary CLI tools. Point your agent at
[`AGENTS.md`](AGENTS.md) and it has everything it needs.

## Common tasks

**Check specific domains**

```bash
python3 scripts/check-domains.py acme.com acme.io acme.dev
```

**Cross names with TLDs**

```bash
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgehub
```

**Only show what's registrable, under budget**

```bash
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20
```

**Generate candidates, then check them**

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

Patterns: `root+suffix` · `prefix+root` · `prefix+root+suffix` · `root+root` ·
`blend` (overlaps two roots — `design` + `ignite` → `designite`).

**Preview cost before a big sweep**

```bash
python3 scripts/check-domains.py --plan --tlds com,ai,io,dev $(cat names.txt)
```

```console
provider:        spaceship
domains:         50 (0 cached, 50 to query)
requests:        3
budget:          25 requests / 30s
estimated time:  1s
```

More constraint-to-command mappings — "only .com", "max 6 characters", "ending
in -ify", "under $20" — in
[`references/query-recipes.md`](references/query-recipes.md).

## Command reference

### `check-domains.py`

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

Reading the status column:

| Value | Meaning |
|---|---|
| `available` | No registration record — registrable |
| `taken` | Registered |
| `no RDAP for this TLD` | The keyless fallback can't answer. **Not a "no"** |
| `lookup failed` | Errored after retries. **Not confirmed available** |
| `unknown` | Unexpected provider response |

Exit codes: `0` all resolved · `1` no valid input · `2` no provider configured ·
`3` partial — some lookups failed and are **not** confirmed available.

### `gen-names.py`

| Flag | Effect |
|---|---|
| `--roots snap,clip` | Word roots (required) |
| `--prefixes up,re` | Prefixes |
| `--suffixes ify,ly` | Suffixes |
| `--patterns root+suffix,blend` | Which combinations to emit |
| `--min-len N` / `--max-len N` | Length filter |
| `--no-filter` | Skip the pronounceability filter |

## What it's built on

| Concern | Source | Credentials |
|---|---|---|
| Availability | Spaceship — 20 domains/request | free account |
| — alternative | NameSilo | free account |
| — fallback | RDAP via `rdap.org` | **none** |
| Pricing | Porkbun's public TLD price list — 907 TLDs | **none** |
| — optional | Dynadot — exact per-domain quotes | free account |

Pricing works with zero configuration because Porkbun publishes its entire
price list at an endpoint that requires no authentication.

Eleven providers were surveyed, each tested where possible — what they require,
what they actually return, which ones have traps:
[`references/providers.md`](references/providers.md).

## Design notes

Three things this handles that similar tools usually don't.

<details>
<summary><b>Renewal prices, not just promo prices</b></summary>

A `.xyz` costs $2.04 the first year and $12.98 every year after — a 6.4x jump.
`.io` nearly doubles. Showing only the first-year price is actively misleading,
so both columns are always present and jumps above 1.5x get flagged in the
`Note` column.

</details>

<details>
<summary><b>The RDAP trap that makes free checkers lie</b></summary>

RDAP-based checkers commonly report `github.io` as **available**. Here's why:

| Domain | Reality | rdap.org returns |
|---|---|---|
| `openai.com` | registered | 200 ✅ |
| `vercel.app` | registered | 200 ✅ |
| **`github.io`** | **registered** | **404 ← reads as "available"** |
| **`google.co`** | **registered** | **404 ← reads as "available"** |

A TLD with no RDAP server returns 404 — identical to "no registration record".
`.io` and `.co` publish none.

This repo fetches the IANA bootstrap list (1200 TLDs with RDAP), caches it for
a week, and reports `no RDAP for this TLD` instead of guessing.

</details>

<details>
<summary><b>Rate limiting that survives process exit</b></summary>

An agent invokes the checker many times per session — generate, check, refine,
check again — and sometimes runs several agents in parallel. Each invocation is
a separate process, so an in-process sleep protects none of them from each
other.

What this does instead:

- **Request budgets persist to disk.** Spent by one run is spent for the next.
- **`flock` guards the state**, so parallel processes take turns instead of each
  reading "0 used" and firing simultaneously.
- **A 429 parks every process** via a shared cooldown, honouring `Retry-After`
  with exponential backoff and jitter.
- **Results cache for an hour.** A 50-domain re-check drops from 26.8s to 0.16s,
  and from 3 requests to 0.
- **Failures are never swallowed.** A domain that failed to resolve is reported
  separately and excluded from `--available-only`.

Measurements, reasoning and tuning knobs:
[`references/rate-limits.md`](references/rate-limits.md).

</details>

## Documentation

| File | Contents |
|---|---|
| [`SKILL.md`](SKILL.md) | Claude Code entry point |
| [`AGENTS.md`](AGENTS.md) | Cross-tool entry point (Codex, Cursor, Copilot, …) |
| [`references/environment.md`](references/environment.md) | Every variable, where each credential comes from |
| [`references/providers.md`](references/providers.md) | Registrar API survey, verified behaviour, traps |
| [`references/rate-limits.md`](references/rate-limits.md) | Budgets, caching, how to tune |
| [`references/query-recipes.md`](references/query-recipes.md) | Constraints → exact commands |
| [`references/naming-guide.md`](references/naming-guide.md) | Word roots, affixes, combination patterns |

## Scope and limits

**Read-only.** This checks availability and prices. It does not buy, transfer,
or change DNS. Purchases happen at your registrar, under your own account.

**Availability is a lookup, not a guarantee.** Registry reservations, premium
pricing and trademark disputes are outside what any API reports. Re-check with
`--no-cache` immediately before buying.

**No opinions about your name.** No length rules, no price ceilings, no TLD
ranking. `references/naming-guide.md` is a palette, not a whitelist.

## Contributing

Adding a provider is one function plus a dict entry — see
[Adding a provider](references/providers.md#adding-a-provider). Two rules there
matter more than the code:

- Never map an ambiguous response to `available`. Use `unknown`.
- Report what you couldn't resolve. Silence reads as "all clear".

Corrections to the provider survey are especially welcome — registrar API
policies change, and the eligibility rules in that table are the part most
likely to go stale.

## License

MIT
