# Domain Finder — agent instructions

Instructions for any coding agent that reads `AGENTS.md` (Codex, Cursor,
Copilot, Gemini CLI, Aider, Windsurf, Zed, and others).

Claude Code users: [`SKILL.md`](SKILL.md) is the equivalent entry point, and it
loads on demand rather than staying in context.

---

## What this repo provides

Two command-line tools for naming a project:

| Tool | Purpose |
|---|---|
| `scripts/check-domains.py` | Check domain availability in bulk, with first-year **and renewal** prices |
| `scripts/gen-names.py` | Combine word roots and affixes into candidates, filtered by length |

Both are Python 3.8+, standard library only, and read-only — they never buy,
transfer, or modify anything.

## Before the first lookup

Confirm the environment is configured:

```bash
python3 scripts/check-domains.py example.com
```

Expected output shows `example.com` as `taken`. If it prints
`No availability provider configured`, direct the user to
[`references/environment.md`](references/environment.md) and stop.

**Do not fall back to guessing availability** from memory or a web search. A
wrong "available" wastes the user's time at checkout and destroys their trust in
the answer.

## No built-in taste

This repo has no rules about price ceilings, TLD rankings, or name length.
Those belong to the user and change per project. Ask, or apply whatever
constraints the user volunteers — exactly those, nothing added.

The one thing to be opinionated about: **check for brand collisions**. Not a
matter of taste. A name that collides with an established product costs the user
real SEO and legal grief later.

## Workflow

### 1. Collect the brief

Ask only for what you don't already have:

- What the project does, and who it's for
- Naming constraints — length, TLDs, must-have or banned words, budget
- Any candidates they already have in mind

Shorthand constraints ("only .com", "max 6 characters", "ending in -ify") map to
exact commands in
[`references/query-recipes.md`](references/query-recipes.md).

### 2. Generate candidates

[`references/naming-guide.md`](references/naming-guide.md) has word roots and
combination patterns. It's a starting palette, not a whitelist.

```bash
python3 scripts/gen-names.py --roots snap,clip,vault --suffixes ify,ly,kit \
  --max-len 6
```

Generate generously — 20–40 candidates on the first pass. Most good short names
are taken, and checking is cheap in bulk.

Apply constraints **while** generating, not after. Filtering at generation is
free; checking is rate limited.

### 3. Check availability

```bash
# full domains
python3 scripts/check-domains.py snapkit.com vaultly.com

# bare names crossed with TLDs
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgely

# only registrable, under budget
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20

# JSON for post-processing
python3 scripts/check-domains.py --json snapkit.com
```

**Pass the whole list in one call.** One call with 60 domains costs 3 requests;
60 calls with one domain each cost 60 and will get the user throttled. Never
loop this script over a list.

Preview cost before a large sweep:

```bash
python3 scripts/check-domains.py --plan --tlds com,ai,io $(cat names.txt)
```

### 4. Vet the results

For each available candidate, before presenting it:

- **Brand collision** — search the bare name. If an established product,
  company, or well-known open-source project owns it, say so and explain the
  consequence.
- **Renewal cliff** — flagged in the `Note` column. `.xyz` at $2.04 renewing at
  $12.98 is a 6.4x jump. Surface it, don't bury it.
- **Premium pricing** — also flagged. The TLD list price does not apply; the
  real quote comes from the registrar.

### 5. Present

A table, then your reasoning:

| Domain | Status | Reg. | Renewal | Brand risk | Notes |
|---|---|---|---|---|---|
| snapkit.com | available | $11.08 | $11.08 | none found | short, reads as a toolkit |
| vaultly.com | available | $11.08 | $11.08 | ⚠️ existing fintech | — |

Then recommend one and say why. Ranking the options is the hard part — that's
what the user wants from you, not a raw dump.

## Reading the output

| Value | Meaning |
|---|---|
| `available` | No registration record. Registrable, subject to premium pricing and registry reservations. |
| `taken` | Registered. |
| `no RDAP for this TLD` | The keyless fallback can't answer for this TLD. **Not a "no".** |
| `lookup failed` | Errored after retries. **Not confirmed available.** |
| `unknown` | Unexpected provider response. Unresolved. |
| Note `cached` | Up to an hour old. Re-check with `--no-cache` before purchase. |

Exit codes: `0` all resolved · `1` no valid input · `2` no provider configured ·
`3` partial — some lookups failed.

**If anything is unresolved, say so.** Silence reads as "all clear".

## Constraints

- **Read-only.** This does not buy domains. Purchases happen at the user's
  registrar, under their account, with their payment method. Point them there
  and stop.
- **Never present an unresolved lookup as available.**
- **Don't work around the rate limiter.** If a run is slow, it is waiting on a
  budget that exists for a reason. See
  [`references/rate-limits.md`](references/rate-limits.md).

## Reference files

| File | Contents |
|---|---|
| [`references/environment.md`](references/environment.md) | Every variable, where each credential comes from |
| [`references/providers.md`](references/providers.md) | Registrar API survey, verified behaviour, traps |
| [`references/rate-limits.md`](references/rate-limits.md) | Budgets, caching, what to do when throttled |
| [`references/query-recipes.md`](references/query-recipes.md) | Constraints → exact commands |
| [`references/naming-guide.md`](references/naming-guide.md) | Word roots, affixes, combination patterns |
