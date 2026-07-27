<!--
  letsfinddomain-skill — append this file directly to your project's AGENTS.md,
  CLAUDE.md, GEMINI.md, or .github/copilot-instructions.md:

      cat install/agents-snippet.md >> AGENTS.md

  Everything below is meant to be appended as-is. If you cloned the repo
  somewhere other than tools/letsfinddomain-skill/, adjust the paths.
-->

## Domain lookups

When the user wants domain name ideas, or asks whether a domain is available,
use the tools in `tools/letsfinddomain-skill/`. Read that directory's
`AGENTS.md` for the full workflow.

When the user asks about domains, invoke this skill and handle the request
through the agent workflow. The user does not need to run the Python scripts.
The commands below are implementation examples for the agent:

Check availability — reports first-year **and renewal** price:

```bash
python3 tools/letsfinddomain-skill/scripts/check-domains.py \
  --tlds com,ai,io snapkit vaultly --available-only
```

Generate candidates, then check them:

```bash
python3 tools/letsfinddomain-skill/scripts/gen-names.py \
  --roots snap,clip,vault --suffixes ify,ly --max-len 6 \
  | python3 tools/letsfinddomain-skill/scripts/check-domains.py \
      --tlds com --available-only
```

Useful flags: `--max-price 20`, `--json`, `--no-cache`, `--plan` (preview
request cost without spending it).

Rules:

- **Pass the whole candidate list in one call.** One call with 60 domains costs
  3 requests; 60 separate calls cost 60 and will get throttled. Never loop the
  script over a list.
- **Never guess availability** from memory or a web search. If the tool is not
  configured, say so and point at
  `tools/letsfinddomain-skill/references/environment.md`.
- **`lookup failed`, `unknown`, `no RDAP for this TLD`, and `not supported by this provider` mean "don't know"**,
  never "available". The script exits `3` when anything is unresolved — report
  it rather than staying silent.
- **Always surface the renewal price.** `.xyz` is $2.04 the first year and
  $12.98 after.
- **Check for brand collisions** before recommending a name.
- **Read-only.** Never buys, transfers, or changes DNS.
