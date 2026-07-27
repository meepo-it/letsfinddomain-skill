<!--
  letsfinddomain-skill — append this file directly to your project's AGENTS.md,
  CLAUDE.md, GEMINI.md, or .github/copilot-instructions.md.

      cat install/agents-snippet.md >> AGENTS.md

  If the repository is cloned somewhere else, adjust the skill path in the
  referenced AGENTS.md.
-->

## Domain lookups

When the user wants domain ideas, naming help, or availability checks, invoke
`letsfinddomain-skill` and handle the request through its agent workflow. Let
the user describe the product, audience, style, TLDs, budget, or candidate list
in natural language. The user should not need to run scripts or construct
command-line arguments.

Rules:

- Start with the user's request. Do not run a standalone environment preflight
  or check `example.com` before understanding what the user wants.
- If the user asks only for ideas, generate them without blocking on API setup.
- If availability is requested, pass the complete candidate list in one batch and
  respect the provider's batch and rate limits.
- Never guess availability. If no provider is configured, explain that it cannot
  be confirmed and point to `references/environment.md`.
- Never present unresolved results as available.
- Always surface renewal pricing and premium-domain warnings when available.
- Check brand collisions before recommending a name.
- Read-only: never buy, transfer, or change DNS.
