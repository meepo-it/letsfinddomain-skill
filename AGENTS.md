# Let's Find Domain — agent instructions

Instructions for any coding agent that reads `AGENTS.md` (Codex, Cursor,
Copilot, Gemini CLI, Aider, Windsurf, Zed, and others).

Claude Code users: [`SKILL.md`](SKILL.md) is the equivalent entry point, and it
loads on demand rather than staying in context.

---

## Maintenance rules

### Keep user-facing documentation bilingual

`README.md` and `README.zh-CN.md` are a pair. Any change to user-facing
workflow, installation, provider support, pricing, limits, or examples must be
made in both files in the same change.

Provider walkthroughs are also paired: every
`docs/providers/*/setup.md` must have a matching
`setup.zh-CN.md`. Keep their section order, numbered steps, environment
variables, official URLs, screenshots, and verification flow aligned. The
verification flow shown to users is `/letsfinddomain-skill`; do not replace it
with direct Python commands in provider walkthroughs.

Referral links, when valid and intentionally supported, belong only in the
corresponding provider walkthrough link. Never add referral codes to README or
invent one when the provider does not offer a confirmed program.

Run the local repository test suite after documentation or code changes:

```bash
python3 scripts/test.py
```

The repository includes a Git `pre-commit` hook under `.githooks/` that runs the
same suite. Enable it once after cloning:

```bash
python3 scripts/install-hooks.py
```

Do not create a commit while the suite is failing. The hook is local and does
not require a network connection.

---

## User request workflow

- Start with the user's actual request. Do not run a standalone `example.com`
  preflight before understanding the request.
- Use the scripts internally and keep normal replies focused on the user's
  result. Do not show Python commands or a long provider survey unless the user
  explicitly asks for technical setup.
- If the user asks only for ideas, generate ideas without blocking on API setup.
- If availability is requested, pass the full candidate list in one batch and
  respect the selected provider's batch and rate limits.
- If no provider is configured, say that availability cannot be confirmed yet,
  link [`references/environment.md`](references/environment.md), and stop there.
  Do not guess or substitute a web search.
- Never present `unknown`, `lookup failed`, `no RDAP for this TLD`, or
  `not supported by this provider` as available.
- Always surface first-year and renewal prices when available, plus premium or
  renewal-cliff warnings.
- Check obvious brand collisions before recommending a name.
- Keep the tool read-only: it never buys, transfers, or changes DNS.

## Reference files

| File | Contents |
|---|---|
| [`references/environment.md`](references/environment.md) | Every variable, cross-platform setup, and credential path |
| [`references/providers.md`](references/providers.md) | Registrar API survey, verified behaviour, and traps |
| [`references/rate-limits.md`](references/rate-limits.md) | Budgets, caching, and throttling guidance |
| [`references/query-recipes.md`](references/query-recipes.md) | Constraints → exact internal query recipes |
| [`references/naming-guide.md`](references/naming-guide.md) | Word roots, affixes, and combination patterns |
