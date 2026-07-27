---
name: domain-finder
description: Generate, check, and vet domain names. Use when the user wants domain name ideas, wants to check whether domains are available, or wants to compare registration and renewal prices across TLDs.
allowed-tools: Bash, Read, WebSearch
---

# Domain Finder

Help the user land on a domain they can actually register: generate candidates,
check availability in bulk, attach reference prices, and flag the traps.

## Before anything else

Run the checker once to confirm the environment is wired up:

```bash
python3 scripts/check-domains.py example.com
```

If it reports `No availability provider configured`, point the user at
[`references/environment.md`](references/environment.md) and stop. Do not fall
back to guessing availability from memory or from a web search — a wrong
"available" wastes the user's time at checkout.

## This skill has no built-in taste

There are no hard rules here about price ceilings, TLD rankings, or name
length. Those are the user's call, and they change per project. Ask, or take
whatever constraints the user volunteers, and apply exactly those.

The one thing worth being opinionated about: **check for brand collisions**.
That is not a matter of taste — registering a name that collides with an
established product costs the user real SEO and legal grief later.

## Workflow

### 1. Collect the brief

Ask only for what you don't already have:

- What the project does, and who it's for
- Any naming constraints — length, TLDs, must-have or banned words, budget
- Whether they already have candidates in mind

If the user gives constraints in shorthand ("only .com", "max 6 characters",
"something ending in -ify"), read
[`references/query-recipes.md`](references/query-recipes.md) — it maps common
requests to exact command invocations.

### 2. Generate candidates

Use [`references/naming-guide.md`](references/naming-guide.md) for word roots
and combination patterns. It's a starting palette, not a whitelist — invent
freely beyond it.

For mechanical expansion, `gen-names.py` combines roots with affixes and
filters by length:

```bash
python3 scripts/gen-names.py --roots snap,clip,vault --suffixes ify,ly,kit \
  --max-len 6 | python3 scripts/check-domains.py --tlds com --available-only
```

Generate generously. Availability checking is cheap (20 domains per request)
and most good names are already taken, so 20–40 candidates is a reasonable
first pass, not overkill.

Apply the user's stated constraints while generating, not after. If they said
"max 6 characters", don't produce 9-character candidates and filter them later —
filtering at generation is free, checking is rate limited.

### 3. Check availability

```bash
# Full domains
python3 scripts/check-domains.py snapkit.com vaultly.com

# Bare names crossed with several TLDs
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgely

# Only show what's actually registrable, under a budget
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20

# Machine-readable, for when you need to post-process
python3 scripts/check-domains.py --json snapkit.com
```

The script batches, respects rate limits, and attaches prices automatically.

**Pass the whole candidate list in one call.** One call with 60 domains costs 3
requests; 60 calls with one domain each cost 60 and will get the user throttled.
Never loop the script over a list.

Before a large sweep, preview the cost:

```bash
python3 scripts/check-domains.py --plan --tlds com,ai,io $(cat names.txt)
```

If a run reports domains it could not resolve, say so. Those are **not**
confirmed available, and the script exits `3` to make that detectable. See
[`references/rate-limits.md`](references/rate-limits.md).

### 4. Vet what came back

For each available candidate, before presenting it:

- **Brand collision** — search the bare name. If an established product,
  company, or open-source project already owns it, say so and explain the
  consequence (you will fight them for your own name in search results).
- **Renewal cliff** — the script flags TLDs where renewal costs far more than
  the first year. `.xyz` at $2 first year and $13 after is a 6x jump; `.io`
  nearly doubles. Surface this, don't bury it.
- **Premium pricing** — flagged in the `Note` column. The listed TLD price does
  not apply; the real quote comes from the registrar.

### 5. Present

A table, with your reasoning underneath:

| Domain | Status | Reg. | Renewal | Brand risk | Notes |
|---|---|---|---|---|---|
| snapkit.com | available | $11.08 | $11.08 | none found | short, reads as a toolkit |
| vaultly.com | available | $11.08 | $11.08 | ⚠️ Vaultly is an existing fintech | — |

Then give a recommendation and say why. Don't just dump the table — the user
asked you because ranking the options is the hard part.

## What this skill does not do

It does not buy domains. Availability and price are read-only lookups; the
purchase happens at the user's registrar, under their account, with their
payment method. Point them there and stop.

## Reference files

| File | What's in it |
|---|---|
| [`references/environment.md`](references/environment.md) | Every env var, where to get each credential |
| [`references/providers.md`](references/providers.md) | Registrar API comparison, verified behaviour and gotchas |
| [`references/rate-limits.md`](references/rate-limits.md) | Request budgets, caching, what to do when throttled |
| [`references/query-recipes.md`](references/query-recipes.md) | Common constraints → exact commands |
| [`references/naming-guide.md`](references/naming-guide.md) | Word roots, affixes, combination patterns |
