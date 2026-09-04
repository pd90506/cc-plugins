# Plan 01 — Migrate `pi-arxiv` to a Claude Code plugin (`cc-arxiv`)

- **Date:** 2026-09-04
- **Status:** Completed 2026-09-04 (cc-arxiv 0.1.2). Deviations: `userConfig` not used (unverifiable headlessly) — `.mcp.json` uses `${ALPHAXIV_API_KEY}`; a unittest suite was added under `tests/`; AC 6 amended (filename keeps the arXiv version suffix, as pi-arxiv did); AC 9 pattern corrected to `\balphaxiv_`. Verified in-session after restart 2026-09-04: MCP connected, `discover_papers` live, `/cc-arxiv:arxiv` and `read-paper` script ran with no prompt. Only the eli5 check (AC 11) is left for the user. Key stored in `~/.claude/settings.json` `env` because the desktop app does not inherit shell exports.
- **Research:** [docs/research/pi-arxiv-to-claude-code-plugin-2026-09-04.md](../research/pi-arxiv-to-claude-code-plugin-2026-09-04.md)

## Spec

### Goal / problem statement

`pi-arxiv` is a Pi extension (9 tools, 6 slash commands, 7 skills, ~2,000 lines of TypeScript) for finding, reading, citing, and reviewing research papers via arXiv and alphaXiv. Pi has been dropped in favor of Claude Code. The paper-research workflows must keep working in Claude Code as a plugin in `cc-plugins/`, with the same debloated philosophy as `cc-skills`: skill content first, runtime code only where prose cannot do the job.

### Scope

**In scope**

- A new plugin `cc-plugins/cc-arxiv/` (own git repo, like `cc-skills`), listed in `cc-plugins/.claude-plugin/marketplace.json`.
- The alphaXiv capabilities (semantic search, paper content, ask-a-PDF, read linked GitHub repo) exposed as MCP tools.
- The arXiv capabilities (field search, PDF download, BibTeX/text citation) exposed as a skill with a bundled script.
- The 7 skills (`literature-review`, `source-comparison`, `research-review`, `paper-code-audit`, `deep-research`, `eli5`, `read-paper`) ported with their tool references remapped to Claude Code.
- API-key configuration via plugin `userConfig`, with `ALPHAXIV_API_KEY` env fallback.
- README and maintainer CLAUDE.md.

**Out of scope (non-goals)**

- Porting `src/index.ts` glue, `src/config.ts`, or any Pi UI behavior (status bar, display-only messages, interactive key prompt).
- The local paper-annotation tools (`alphaxiv_annotate_paper`, `alphaxiv_list_annotations`). Low value, Pi-local state; dropped. Notes can live in repo files.
- The `/arxiv`, `/arxiv-get`, `/arxiv-cite`, `/alphaxiv` shortcut commands as separate skills. The single `arxiv` skill accepts `$ARGUMENTS`, and alphaXiv search is a plain request.
- A bundled Node MCP server (research Layout B). Rejected for the first cut: it re-adds a runtime, `node_modules` in the cache copy, and a 60-second install budget for no capability gain.
- Named plugin subagents (`agents/researcher.md` etc.). Deferred; skills use the built-in `Agent` tool with roles described in the prompt, exactly as the Pi skills do today.
- Automated tests. `cc-skills` ships none; verification is manual smoke tests plus `claude plugin validate`.
- Copying `reference/`, `.env`, `docs/`, `tests/`, or `node_modules/` from pi-arxiv. `.env` holds a live key and the plugin directory is copied verbatim into the plugin cache.

### Requirements / behavior

1. **When the plugin is enabled with an API key configured,** four alphaXiv MCP tools are available: `discover_papers`, `get_paper_content`, `answer_pdf_queries`, `read_files_from_github_repository`, named `mcp__plugin_cc-arxiv_alphaxiv__<tool>`.
2. **When a user asks to search arXiv by author, title, id, category, or date,** the `arxiv` skill runs `${CLAUDE_SKILL_DIR}/scripts/arxiv.py search ...` via Bash without a permission prompt and returns formatted results (title, id, categories, date, authors, abs/pdf URLs, trimmed summary).
3. **When a user asks to download an arXiv paper,** the script saves `<id> - <title>.pdf` under `~/Downloads/arxiv` by default, or a directory the user names.
4. **When a user asks for a citation,** the script emits BibTeX by default or APA-style text on request, matching pi-arxiv's key scheme `<lastname><year><firstword>`.
5. **When a user runs `/cc-arxiv:arxiv <text>`,** the skill treats the text as a search query.
6. **When a request matches a workflow skill's description,** the skill auto-loads and its "Tool Discipline" block names only tools that exist in Claude Code (`WebSearch`, `WebFetch`, `Agent`, `Read`, the MCP tool names above, the `arxiv` script). No `web_search`, `fetch_content`, `subagent`, `alphaxiv_*`, `arxiv_*`, or `/skill:` strings remain.
7. **When `read-paper` runs,** it uses `python3 ${CLAUDE_SKILL_DIR}/readpaper.py` without a prompt, opens PNGs with `Read`, and mentions that `Read` can ingest a PDF directly for the text pass. It no longer references `read-pdf`.
8. **When no API key is configured,** the arXiv skill and all pure-prose skills still work; only the alphaXiv MCP server fails to connect, and the README says how to fix that.
9. **When a maintainer edits a skill,** `claude --plugin-dir` shows the change immediately; releasing requires a version bump in `plugin.json` followed by `claude plugin update cc-arxiv@cc-plugins`.

### Acceptance criteria

- [x] `claude plugin validate cc-arxiv` passes (warnings about root CLAUDE.md are acceptable).
- [x] `claude plugin validate /Users/panda/repo/Agents/cc-plugins` passes with `cc-arxiv` listed.
- [x] With `claude --plugin-dir cc-arxiv`, `/mcp` shows server `plugin:cc-arxiv:alphaxiv` connected and listing the four tools.
- [x] A live `discover_papers` call on a test question returns paper results.
- [x] `python3 cc-arxiv/skills/arxiv/scripts/arxiv.py search --query 'au:Vaswani AND ti:attention' --max 10` prints results including `1706.03762`.
- [x] `arxiv.py get 1706.03762 --dir <tmp>` writes `1706.03762v7 - Attention Is All You Need.pdf`.
- [x] `arxiv.py cite 1706.03762` prints a `@misc{vaswani2017attention, ...}` entry; `--format text` prints one APA-style line.
- [x] `/cc-arxiv:arxiv attention is all you need` in a session returns search results with no permission prompt.
- [x] `grep -rE 'web_search|fetch_content|\bsubagent\b|\balphaxiv_[a-z_]+|arxiv_(search|download|cite)|/skill:|read-pdf' cc-arxiv/skills` returns nothing.
- [x] `/cc-arxiv:read-paper` on a local arXiv PDF renders a figure crop and reads it with `Read`, with no permission prompt for the script.
- [ ] (interactive session needed) `/cc-arxiv:eli5 1706.03762` produces the fixed-structure explainer using the MCP tools.
- [x] `cc-arxiv/` contains no `.env`, `reference/`, `node_modules/`, or `docs/` (a new `tests/` was added; see deviations).
- [x] `cc-arxiv` is installed via `claude plugin install cc-arxiv@cc-plugins`, and `claude plugin list` shows it enabled.

### Constraints & assumptions

- Claude Code 2.1.252 is installed. Docs state `userConfig`, `${user_config.*}`, `${CLAUDE_SKILL_DIR}`, and `allowed-tools` substitution but no minimum version; step 1 verifies them.
- `python3` 3.9.6 is on PATH with PyMuPDF 1.26.5 already installed; `node` v26 is also present. The arXiv script is written in Python so both bundled scripts share one runtime and need zero dependencies (`urllib`, `xml.etree`).
- The alphaXiv MCP server is Streamable HTTP at `https://api.alphaxiv.org/mcp/v1` with bearer-key auth and no OAuth (verified live by pi-arxiv on 2026-09-04).
- Plugin installs copy the directory into `~/.claude/plugins/cache/`; explicit `version` must be bumped for every release because `cc-plugins/` is not a git repo.
- The skill bodies in this plugin will name Claude Code tools literally. This intentionally departs from the `cc-skills` "agent-neutral" rule and is documented in `cc-arxiv/CLAUDE.md`.
- pi-arxiv's client-side niceties (keyword derivation, markdown-to-JSON normalization, section filtering) are dropped; Claude supplies `keywords[]` itself and reads the server's markdown directly.

### Open questions

1. Does `${user_config.alphaxiv_api_key}` resolve inside a plugin `.mcp.json` `headers` block, and does `${ALPHAXIV_API_KEY:-...}` env fallback also expand there? Step 1 answers this; if only one works, use that one.
2. Is alphaXiv's server stable under Claude Code's MCP client (pi-arxiv retried transient SSE errors)? Step 1 answers this.
3. Should `deep-research`, `research-review`, and `paper-code-audit` be user-only (`disable-model-invocation: true`) to save always-on description context? Default in this plan: keep all model-invocable except none; revisit after use.
4. Plugin name `cc-arxiv` is assumed. It prefixes every skill and MCP tool name, so it should be settled before step 2.

## Research summary

Full findings: [pi-arxiv-to-claude-code-plugin-2026-09-04.md](../research/pi-arxiv-to-claude-code-plugin-2026-09-04.md). Key points:

- Claude Code plugins can add tools **only via MCP**; everything else is a skill, optionally with a bundled script run through Bash. (`code.claude.com/docs/en/tools-reference`)
- Four of pi-arxiv's tools are pass-throughs to the upstream alphaXiv MCP server (`src/alphaxiv.ts:281-335`). Pointing `.mcp.json` straight at that server removes all runtime code.
- The three arXiv tools are a dependency-free Atom client plus formatting (`src/arxiv.ts`, 279 lines). Best fit is a skill-bundled script pre-approved with `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/arxiv.py *)`.
- Pi commands map to skills; `/alphaxiv-setup`'s interactive key prompt maps to plugin `userConfig` with `sensitive: true`.
- The 7 skills port structurally as-is; the work is remapping tool names in their "Tool Discipline" blocks (research §3.3).
- Install copies the plugin directory into the cache, so secrets and reference material must stay out of it. Updates apply only on a `version` bump.

## Implementation steps

Each step names the requirement (R) or acceptance criterion (AC) it satisfies.

### ✅ Step 1 — Spike the two riskiest unknowns (open questions 1, 2)

_Result: alphaXiv server verified live via curl (bearer key, 19 tools, `discover_papers` returns results). Headless `claude -p` could not authenticate, so `${user_config.*}` substitution was not testable; `${ALPHAXIV_API_KEY}` chosen. This session later showed the plugin sending the header (HTTP 401 with no key in the desktop app's env), confirming the wiring._

Create a throwaway plugin dir in the scratchpad with only `.claude-plugin/plugin.json` (with `userConfig.alphaxiv_api_key`, `sensitive: true`) and `.mcp.json` pointing at alphaXiv with `Authorization: Bearer ${user_config.alphaxiv_api_key}`. Launch `claude --plugin-dir <dir>`, run `/mcp`, and call `discover_papers` once. Repeat with `Bearer ${ALPHAXIV_API_KEY}` and the env var exported. Record which substitution works and whether the server connects reliably. The key comes from the user's environment; never read `.env` contents into the conversation.
→ AC 3, 4. Decides the final `.mcp.json` form.

### ✅ Step 2 — Scaffold `cc-arxiv`

- `cc-plugins/cc-arxiv/.claude-plugin/plugin.json`: `name: cc-arxiv`, `version: 0.1.0`, description, author, license MIT, `userConfig.alphaxiv_api_key` (`type: string`, `sensitive: true`, title, description with the alphaXiv key URL).
- `cc-plugins/cc-arxiv/.mcp.json`: one `http` server `alphaxiv` using whichever substitution step 1 proved.
- `.gitignore` copied from `cc-skills`.
- `git init` and an initial commit after step 8.
→ R1, R8.

### ✅ Step 3 — Port arXiv as a skill with a Python script

- `skills/arxiv/scripts/arxiv.py`: port `src/arxiv.ts` (Atom parse via `xml.etree`, date clause, `search`, `get`, `cite` subcommands, `~` and relative dir handling, filename sanitization, BibTeX key scheme, APA text). Argparse flags mirror the Pi tool schema: `--query`, `--ids`, `--max` (1–100, default 10), `--start`, `--sort-by`, `--sort-order`, `--from`, `--to`; `get <id|url> [--dir] [--filename]`; `cite <ids...> [--format bibtex|text]`. User-Agent `cc-arxiv/0.1`.
- `skills/arxiv/SKILL.md`: `name: arxiv`, description covering author/title/id/category/date search, download, and citation; `argument-hint: "<query or arXiv id>"`; `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/arxiv.py *)`; body explains the three subcommands, arXiv query syntax, when to prefer alphaXiv `discover_papers` for semantic topic discovery instead (this replaces pi-arxiv's `promptGuidelines`), and how `$ARGUMENTS` is treated as a search query when present.
→ R2, R3, R4, R5; AC 5, 6, 7, 8.

### ✅ Step 4 — Port the six workflow skills

Copy `literature-review`, `source-comparison`, `research-review`, `paper-code-audit`, `deep-research`, `eli5` from `pi-arxiv/skills/`. In each, rewrite the "Tool Discipline" block and any inline references per this map:

| Pi text | Claude Code text |
|---|---|
| `alphaxiv_search` | `mcp__plugin_cc-arxiv_alphaxiv__discover_papers` (pass `keywords[]`, `question`, `difficulty`; optional `prioritize`, `published_after/before`) |
| `alphaxiv_get_paper` | `mcp__plugin_cc-arxiv_alphaxiv__get_paper_content` (`url`, `fullText?`) |
| `alphaxiv_ask_paper` | `mcp__plugin_cc-arxiv_alphaxiv__answer_pdf_queries` (`paper`, `queries[]`) |
| `alphaxiv_read_code` | `mcp__plugin_cc-arxiv_alphaxiv__read_files_from_github_repository` (`githubUrl`, `path`) |
| `arxiv_search` / `arxiv_download` / `arxiv_cite` | the `arxiv` skill (`python3 ${CLAUDE_SKILL_DIR}/../arxiv/scripts/arxiv.py` is not valid across skills; instead say "load the `arxiv` skill and run its `search` / `get` / `cite` subcommand") |
| `web_search` | `WebSearch` |
| `fetch_content` (urls array) | `WebFetch` (one `url` + `prompt` per call) |
| `subagent` | `Agent` tool, role described in the prompt, `subagent_type: general-purpose` |
| `read` | `Read` |
| `/skill:<name>` | `/cc-arxiv:<name>` |
| "(pi-arxiv)" labels | "(cc-arxiv)" |

Keep `deep-research`'s pause-for-confirmation step; do not add `context: fork` to it. Leave the conditional "memory tool if visible" line as is.
→ R6; AC 9.

### ✅ Step 5 — Port `read-paper`

Copy `SKILL.md` and `readpaper.py` unchanged in logic. Edits to `SKILL.md`: drop the trailing "use read-pdf instead" sentence from the description; add `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/readpaper.py *)`; replace bare `python3 readpaper.py` with `python3 ${CLAUDE_SKILL_DIR}/readpaper.py`; replace the `read` tool with `Read`; remap the three paper-tool names as in step 4; add one sentence noting `Read` can ingest the PDF directly (whole file up to 10 pages, else `pages` ranges) as the quickest text pass, with the script still used for crops and per-page text with page citations.
→ R7; AC 9, 10.

### ✅ Step 6 — Docs

- `cc-arxiv/README.md`: what it is, skill table, MCP tools table, API-key setup (userConfig prompt at install, `ALPHAXIV_API_KEY` fallback, note that `get_paper_content` and `answer_pdf_queries` consume alphaXiv AI quota), install commands (`--plugin-dir` and marketplace), release procedure (bump version, commit, `claude plugin update`).
- `cc-arxiv/CLAUDE.md`: maintainer conventions, including that skill bodies in this plugin intentionally name Claude Code tools literally, and the "no secrets or reference material in the plugin dir" rule.
- `cc-plugins/.claude-plugin/marketplace.json`: add the `cc-arxiv` entry with `source: ./cc-arxiv`.
- `cc-plugins/README.md`: add `cc-arxiv/` to the plugin list.
→ R8, R9; AC 2, 12.

### ✅ Step 7 — Verify

Run the acceptance checklist in order: both `validate` commands, the script commands directly, the grep for dead names, then `claude --plugin-dir cc-arxiv` for the MCP connection, `/cc-arxiv:arxiv`, `/cc-arxiv:read-paper` on a downloaded PDF, and `/cc-arxiv:eli5`.
→ AC 1–11.

### ✅ Step 8 — Commit and install

`git init` in `cc-arxiv`, initial commit, then `claude plugin marketplace update cc-plugins` and `claude plugin install cc-arxiv@cc-plugins`. Confirm with `claude plugin list`.
→ AC 13.

## Files to create or modify

**Create**

- `cc-arxiv/.claude-plugin/plugin.json`
- `cc-arxiv/.mcp.json`
- `cc-arxiv/.gitignore`
- `cc-arxiv/README.md`
- `cc-arxiv/CLAUDE.md`
- `cc-arxiv/skills/arxiv/SKILL.md`
- `cc-arxiv/skills/arxiv/scripts/arxiv.py`
- `cc-arxiv/skills/{literature-review,source-comparison,research-review,paper-code-audit,deep-research,eli5}/SKILL.md`
- `cc-arxiv/skills/read-paper/SKILL.md`
- `cc-arxiv/skills/read-paper/readpaper.py`

**Modify**

- `.claude-plugin/marketplace.json` (add `cc-arxiv`)
- `README.md` (plugin list)

**Not copied from pi-arxiv:** `src/`, `tests/`, `scripts/spike-alphaxiv.ts`, `docs/`, `reference/`, `.env*`, `package*.json`, `AGENTS.md`.

## Risks and assumptions

- **Substitution in `.mcp.json` headers may not work for one of the two forms.** Mitigated by step 1; worst case the README instructs users to export `ALPHAXIV_API_KEY` and `.mcp.json` uses `${ALPHAXIV_API_KEY}`.
- **alphaXiv server flakiness.** pi-arxiv retried transient SSE errors. Claude Code reconnects automatically; if calls fail often, Layout B (bundled Node server with retries) is the fallback and is described in the research doc.
- **Dropping keyword derivation** means Claude must supply `keywords[]` to `discover_papers`. The skills' tool-discipline text tells it to; quality of results may shift slightly from pi-arxiv.
- **Model-invocable skill descriptions cost context** (seven descriptions, up to 1,536 chars each). If the listing feels heavy, flip the three heavyweight review skills to user-only (open question 3).
- **`allowed-tools` grants last one turn.** Long `read-paper` sessions may re-prompt for the script on later turns. Acceptable; users can allow the pattern in settings.
- **Python 3.9** is old but sufficient; the script must avoid 3.10+ syntax (no `match`, no `X | Y` types).
- **Assumption:** the user is fine dropping annotations and the four shortcut commands. Both are called out as non-goals above and are cheap to add later as skills.
