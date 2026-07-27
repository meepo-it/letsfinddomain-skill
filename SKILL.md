---
name: letsfinddomain-skill
description: Generate, check, and vet domain names. Use when the user wants domain name ideas, wants to check whether domains are available, or wants to compare registration and renewal prices across TLDs.
allowed-tools: Bash, Read, WebSearch
---

# Let's Find Domain

Help the user find a strong domain name, confirm its availability, show first-
year and renewal pricing, and flag obvious brand collisions.

## User-first behavior

- Start with the user's request. Do **not** run a standalone `example.com`
  preflight before understanding what they want.
- Use the bundled scripts internally. In normal user-facing replies, do not
  show Python commands or ask users to assemble command-line arguments.
- Use system environment variables first; a repository `.env` is a local
  fallback. Spaceship is the default availability provider when configured.
- If no availability provider is configured, say so in one or two sentences and
  link to [`references/environment.md`](references/environment.md). Do not dump
  every provider, RDAP caveat, or setup command unless the user asks.
- Never guess availability. `available` must come from a real provider; an
  unresolved result is not available.

## Workflow

1. Understand the brief: product, audience, naming style, length, TLDs, budget,
   banned or required words, and existing candidates. Ask only for missing
   information that changes the search.
2. Generate candidates around the brief. Use
   [`references/naming-guide.md`](references/naming-guide.md) when useful, but
   treat it as a palette rather than a whitelist.
3. When availability is requested, send the complete candidate list in one
   batch. Respect the selected provider's batch shape, shared rate budget, and
   one in-flight request rule; see [`references/rate-limits.md`](references/rate-limits.md)
   only when needed.
4. Vet available names for established brand or product collisions. Surface
   premium pricing and large renewal increases instead of hiding them.
5. Present a compact table with domain, status, registration price, renewal
   price, and notes. Recommend the strongest option when the user asks for
   suggestions, not just a raw list.

## Failure handling

- No provider: explain that availability cannot be confirmed yet and point to
  the cross-platform setup in [`references/environment.md`](references/environment.md).
- `lookup failed`, `unknown`, `no RDAP for this TLD`, and `not supported by this
  provider`: report as unresolved, never as available.
- RDAP is only an optional trial fallback. It reports registration records, not
  guaranteed purchasability or checkout pricing.

## Scope

Read-only only. Never buy, transfer, or modify domains or DNS. The user makes
the purchase in their registrar account.
