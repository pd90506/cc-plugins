# Research: migrating `pi-arxiv` (Pi extension) to a Claude Code plugin

- **Date:** 2026-09-04
- **Question:** What does the Pi extension `pi-arxiv` provide, and how does each piece map onto Claude Code plugin surfaces (skills, slash commands, agents, hooks, MCP servers, LSP), so it can be ported into `/Users/panda/repo/Agents/cc-plugins/<plugin>/`?
- **Primary sources:** pi-arxiv source at `/Users/panda/repo/Agents/pi-plugins/pi-arxiv` (git `20cade9`), the `cc-skills` reference plugin, and the official Claude Code docs at `code.claude.com/docs` (fetched 2026-09-04; URLs cited per claim).

## Summary

1. pi-arxiv is **9 LLM tools + 6 slash commands + 7 skills + 1 shutdown hook**, all registered from one file, `src/index.ts` (728 lines). Six of the tools/commands are thin wrappers over the **upstream alphaXiv MCP server** (`https://api.alphaxiv.org/mcp/v1`, Streamable HTTP, `Authorization: Bearer <API key>`); three are a keyless arXiv Atom-feed client; two are local-only annotation storage.
2. Claude Code has **no way for a plugin to register a tool except via an MCP server** (`tools-reference`: "To add custom tools, connect an MCP server... a skill... runs through the existing `Skill` tool rather than adding a new tool entry"). Runtime logic therefore becomes either a plugin-bundled MCP server (`.mcp.json`), a script Claude runs via Bash from a skill directory (`${CLAUDE_SKILL_DIR}/...`), or an executable in the plugin's `bin/` (added to the Bash `PATH`).
3. **Biggest simplification:** the four `alphaxiv_search/get_paper/ask_paper/read_code` tools can be replaced by pointing Claude Code *directly* at the alphaXiv MCP server as an `http` entry in the plugin's `.mcp.json` with `"headers": {"Authorization": "Bearer ${ALPHAXIV_API_KEY}"}`. Zero runtime code, zero `node_modules`. What is lost is pi-arxiv's client-side polish (keyword derivation, markdown-to-JSON normalization, section extraction, URL normalization); Claude can do all of these itself.
4. The three **arXiv tools** (search/download/cite) have no upstream MCP server. Best fit: a skill with a bundled dependency-free script (`scripts/arxiv.{mjs,py}`) and `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/arxiv.* *)`, or the same script in `bin/`. An MCP server is possible but heavier (needs Node + `@modelcontextprotocol/sdk`).
5. **Pi commands map to user-invoked skills** (`disable-model-invocation: true`, `argument-hint`, `$ARGUMENTS`), invoked as `/<plugin>:<name>`. `/alphaxiv-setup` (interactive secret entry via `ctx.ui.input`) has no equivalent; the Claude Code-native replacement is plugin `userConfig` with `sensitive: true` (substituted as `${user_config.KEY}` in MCP config and exported as `CLAUDE_PLUGIN_OPTION_<KEY>`), plus the `ALPHAXIV_API_KEY` env var.
6. **The 7 skills port as-is structurally** (same `SKILL.md` frontmatter), but their "Tool Discipline" blocks hard-code Pi host tool names (`web_search`, `fetch_content`, `subagent`, `read`) and pi-arxiv tool names (`alphaxiv_*`, `arxiv_*`). In Claude Code these become `WebSearch`, `WebFetch`, `Agent`, `Read`, and either `mcp__plugin_<plugin>_<server>__<tool>` names or script invocations. This is the main authoring work.
7. Claude Code adds capabilities Pi lacked: **named plugin subagents** (`agents/researcher.md` etc., what Feynman originally had), `context: fork`, hooks, and native PDF reading in `Read` (whole file if <=10 pages, else `pages` ranges of up to 20). `read-paper`'s `readpaper.py` still adds value (figure/table crops, page rendering) and stays a skill-bundled script.
8. **Versioning gotcha confirmed by the docs:** with an explicit `version` in `plugin.json`, "Pushing new commits without bumping it has no effect, and `/plugin update` reports 'already at the latest version'". Omitting `version` only helps when the marketplace is git-hosted (falls back to commit SHA); for "local directories not inside a git repository" the fallback is `unknown`. `/Users/panda/repo/Agents/cc-plugins` is **not** a git repo (only `cc-skills/.git` exists), so explicit-version-and-bump is the only working scheme today.
9. **Cache-copy hazards:** marketplace installs *copy the plugin directory* to `~/.claude/plugins/cache/...` (not a git checkout), so pi-arxiv's gitignored `reference/feynman` (Feynman source) and `.env` (contains a live API key) would be copied verbatim if left in the plugin dir. Keep them out of the Claude Code plugin directory.
10. If a Node MCP server is bundled: ship `package.json` + `package-lock.json` and Claude Code runs `npm ci --ignore-scripts` into the cache copy (60 s timeout, cannot be disabled); Python deps (`readpaper.py` self-installs PyMuPDF with `pip --user`) should instead target `${CLAUDE_PLUGIN_DATA}`.

## Part 1: pi-arxiv inventory

### 1.1 Repo facts

| Item | Value | Source |
|---|---|---|
| Package | `pi-arxiv` 0.1.0, ESM, `"pi": {"extensions": ["./src/index.ts"], "skills": ["./skills"]}` | `package.json:1-25` |
| Declared deps | only `@modelcontextprotocol/sdk ^1.30.0` | `package.json:31-33`; lockfile top-level deps = `['@modelcontextprotocol/sdk']`, 95 packages |
| Undeclared (host-provided) imports | `@earendil-works/pi-coding-agent` (types), `@earendil-works/pi-ai` (`StringEnum`), `typebox` (`Type`) | `src/index.ts:15-17` |
| Runtime | TypeScript run directly by Node >=22 (type stripping), no build, no lint | `AGENTS.md:9-12` |
| Tests | `node --test "tests/**/*.test.ts"`; 6 files: `alphaxiv`, `alpha-sections`, `annotations`, `config`, `skills-lint`, `live` (skipped unless key) | `package.json:16`, `tests/` |
| Fixture | `tests/fixtures/discover_papers.md.txt` (captured `discover_papers` markdown) | `src/alphaxiv.ts:3-6` |
| Manual spike | `scripts/spike-alphaxiv.ts` (connect + `listTools` + one `discover_papers` call) | `scripts/spike-alphaxiv.ts:1-44` |
| Config files | `.env.example` (`ALPHAXIV_API_KEY=`), `.env` (present, contains a real key, gitignored) | `.env.example:1-5`, `.gitignore:14` |
| Gitignored | `/reference/` (Feynman source, ~100s of files), `node_modules/`, `dist/`, `.env` | `.gitignore:1-14` |
| Docs | `docs/plans/01..03`, `docs/research/*` (Feynman port notes), `README.md`, `AGENTS.md` | tree |
| Git log (head) | `20cade9 feat(skills): add read-paper skill`, `d561d78 refactor(plan-03): collapse to skills-only`, `3661ca6 research-workflow skills`, `64bce17 alphaXiv paper tools`, `3b7b3db alphaXiv semantic search`, `364c9d6 initial scaffold` | `git log --oneline` |

### 1.2 Tools registered via `pi.registerTool` (9)

All in `src/index.ts`. Return shape is `{ content: [{type:"text", text}], details }` with `isError: true` for expected user errors (`AGENTS.md:17-21`).

| Tool | What it does | Input schema (TypeBox) | Implementation | External deps / network | Disk state | Secrets |
|---|---|---|---|---|---|---|
| `arxiv_search` | Field/known-item search of arXiv; formats up to 100 results (title, id, cats, date, authors, abs/pdf URLs, 500-char summary) | `query?` (arXiv query syntax `ti:/au:/abs:/cat:/all:` + `AND/OR/ANDNOT`), `ids?: string[]`, `max_results? 1-100` (default 10), `start?`, `sort_by? relevance\|lastUpdatedDate\|submittedDate`, `sort_order?`, `submitted_from?`, `submitted_to?` (`YYYY-MM-DD` or `YYYYMMDDHHMM`) | `src/index.ts:164-258`; `searchArxiv` `src/arxiv.ts:170-198`; regex Atom parser `parseFeed` `:155-168`; date clause `:84-100` | `fetch` to `https://export.arxiv.org/api/query` (`src/arxiv.ts:9`), UA `pi-arxiv/0.1`; no npm deps | none | none |
| `arxiv_download` | Resolve id/URL -> metadata -> download PDF to `<dir>/<id> - <title>.pdf` | `id` (id, `arXiv:<id>`, abs/pdf URL), `dir?` (default `~/Downloads/arxiv`, supports `~`, relative to `ctx.cwd`), `filename?` | `src/index.ts:261-316`; `downloadPdf` `src/arxiv.ts:201-218`; `paperFilename` `src/index.ts:89-97`; `resolveDir` `:82-86` | `fetch` arXiv API + PDF URL | writes PDF under `~/Downloads/arxiv` (`src/index.ts:74`) | none |
| `arxiv_cite` | BibTeX (default) or APA-style text citations | `ids: string[]`, `format? bibtex\|text` | `src/index.ts:319-352`; `toBibtex` `src/arxiv.ts:245-264` (`@misc`/`@article`, key `<lastname><year><word>` `:233-242`), `toCitation` `:267-279` | arXiv API | none | none |
| `alphaxiv_search` | Semantic discovery via upstream MCP tool `discover_papers`; parses its markdown into normalized records | `query` (-> `question`), `keywords?: string[]` (derived from query if absent), `difficulty? 1-10` (default 3), `prioritize? historical\|default\|recency\|popular`, `published_after?`, `published_before?` | `src/index.ts:442-518`; `searchPapers` `src/alphaxiv.ts:343-364`; `parseDiscoverResults` `:79-108` (regex `ENTRY_RE` `:75-76`); `deriveKeywords` `:250-258` | `@modelcontextprotocol/sdk` `Client` + `StreamableHTTPClientTransport` to `https://api.alphaxiv.org/mcp/v1` (`src/alphaxiv.ts:9-17,153-170`), cached client, 3x retry on transient SSE errors (`:141-151,221-242`) | none | `ALPHAXIV_API_KEY` |
| `alphaxiv_get_paper` | Upstream `get_paper_content` (AI report, or raw `fullText`), optional canonical-section filter, attaches local annotation | `paper` (arXiv id / arXiv URL / alphaXiv URL), `fullText?`, `section?`, `sections?: string[]` (raw JSON-schema array via `Type.Unsafe` to dodge Pi coercion, `src/index.ts:63-72`) | `src/index.ts:553-604`; `getPaperContent` `src/alphaxiv.ts:301-307` (args `{url, fullText?}` `:281-285`); `extractPaperSections` `src/alpha-sections.ts:145-161` (aliases `:10-19`); `readAnnotation` `src/annotations.ts:77-79` | alphaXiv MCP (consumes alphaXiv AI quota, `README.md:31-32`) | reads annotation JSON | `ALPHAXIV_API_KEY` |
| `alphaxiv_ask_paper` | Upstream `answer_pdf_queries` with one question | `paper`, `question` | `src/index.ts:607-633`; `answerPdfQueries` `src/alphaxiv.ts:315-321` (args `{paper, queries:[q]}` `:288-290`) | alphaXiv MCP (AI quota) | none | key |
| `alphaxiv_read_code` | Upstream `read_files_from_github_repository` | `githubUrl`, `path?` (default `/`) | `src/index.ts:636-658`; `readGithubRepo` `src/alphaxiv.ts:327-335` | alphaXiv MCP | none | key |
| `alphaxiv_annotate_paper` | Save or clear a local note on a paper | `paper`, `note?`, `clear?` | `src/index.ts:661-688`; `annotatePaper`/`clearPaperAnnotation` `src/annotations.ts:110-125`; `writeAnnotation` `:47-55` | none (local FS) | `<agentDir>/pi-arxiv-annotations/<id>.json`, mode `0600` (`src/annotations.ts:32-34,52-53`) | none |
| `alphaxiv_list_annotations` | List all local notes | `{}` | `src/index.ts:691-701`; `listPaperAnnotations` `src/annotations.ts:128-131` | none | reads same dir | none |

Upstream alphaXiv MCP facts (verified live by pi-arxiv's own spike on 2026-09-04, `docs/plans/01-alphaxiv-search-2026-09-03.md:17-46`): API-key bearer auth works with no OAuth; the only search tool is `discover_papers` with required `keywords[]`, `question`, `difficulty` and optional `published_after/before`, `prioritize`; response is markdown text. Other tool names used: `get_paper_content` (`{url, fullText?}`), `answer_pdf_queries` (`{paper, queries[]}`), `read_files_from_github_repository` (`{githubUrl, path}`) (`docs/research/alphaxiv-paper-tools-2026-09-04.md:55,93,106`).

### 1.3 Commands registered via `pi.registerCommand` (6)

| Command | Behaviour | Implementation | Pi UI APIs used |
|---|---|---|---|
| `/arxiv <query>` | Search (10 results), post results as a display-only message without triggering a model turn | `src/index.ts:355-380` | `ctx.ui.notify`, `ctx.ui.setStatus`, `pi.sendMessage({customType:"pi-arxiv", display:true}, {triggerTurn:false})` (`:374`) |
| `/arxiv-cite <id...>` | BibTeX for several ids, display-only message | `src/index.ts:384-410` | same |
| `/arxiv-get <id\|url>` | Download to `~/Downloads/arxiv`, notify path | `src/index.ts:412-439` | notify/setStatus |
| `/alphaxiv <query>` | Semantic search, display-only message | `src/index.ts:521-550` | same + key guard |
| `/alphaxiv-setup` | Resolve key from env, then project `.env` (`readKeyFromDotenv` `:149-160`), else **interactive prompt** `ctx.ui.input(...)` (`:709`); persist with `setAlphaXivKey` | `src/index.ts:704-722` | `ctx.hasUI`, `ctx.ui.input`, `ctx.cwd` |

### 1.4 Skills shipped via `pi.skills` (7, `skills/<name>/SKILL.md`)

| Skill | Frontmatter | Body summary | Output artifacts | References other tools/skills |
|---|---|---|---|---|
| `literature-review` | `name`, `description` (`skills/literature-review/SKILL.md:1-4`) | 6-step plan/gather/synthesize/cite/verify/deliver; "Tool Discipline" block (`:10-17`) | `outputs/<slug>.md` + `.provenance.md`, `outputs/.plans/`, `outputs/.drafts/` | `alphaxiv_*`, `arxiv_*`, `web_search`, `fetch_content`, `subagent` (roles via system prompt), `/skill:literature-review` (`:8`) |
| `source-comparison` | same | comparison matrix workflow | `outputs/<slug>-comparison.md` | same set (`:15-16,23`) |
| `research-review` | same | severity-graded critique | `outputs/<slug>-review.md` (+ plan, evidence) | same (`:15-16,40`) |
| `paper-code-audit` | same | paper-vs-code audit | `outputs/<slug>-audit.md` | emphasizes `alphaxiv_read_code`, `alphaxiv_ask_paper` (`:15-16,24`) |
| `deep-research` | same | 7-step brief; **pauses for user plan confirmation** (`skills/deep-research/SKILL.md:44`); scale decision on subagent count (`:46-50`); optional memory tool (`:38`) | `outputs/<slug>.md` + `.provenance.md` | same (`:14-17`) |
| `eli5` | same | chat-inline plain-English explainer, fixed section structure (`skills/eli5/SKILL.md:19-25`) | none | `arxiv_search`, `alphaxiv_search/get_paper/ask_paper`, `web_search`, `fetch_content` (`:14-15`) |
| `read-paper` | `name`, `description` ending "For non-paper PDFs ... use **read-pdf** instead" (`skills/read-paper/SKILL.md:3`) | two-tier PDF reading: text layer via script, render pixels only where needed; "eyes-on" rule | PNG crops in a temp dir by default (`readpaper.py:29`) | bundled **`readpaper.py`** (`:10`), Pi `read` tool for PNGs (`:16,21-23`), `arxiv_search`/`alphaxiv_get_paper`/`alphaxiv_ask_paper` (`:12`), `read-pdf` (`:3`) |

`readpaper.py` (396 lines): subcommands `probe|text|pages|page|find|crop|sweep` (`skills/read-paper/readpaper.py:262-292`); imports PyMuPDF and **auto-installs it with `pip install --user` on first run** (`:35-64`); falls back to `pypdf` + macOS `sips` (`:103-140`). Local machine check: `python3` 3.9.6 with PyMuPDF 1.26.5 already installed.

Note: the `read-pdf` skill referenced at `skills/read-paper/SKILL.md:3` was removed from `cc-skills` (`cc-skills` git `d84e84c Remove read-pdf skill; Claude Code reads PDFs natively`), so that sentence must be dropped or reworded in the port.

### 1.5 Other Pi surfaces

| Surface | Use | Source |
|---|---|---|
| Event hook | `pi.on("session_shutdown")` closes the cached alphaXiv MCP client | `src/index.ts:725-727`, `disconnect` `src/alphaxiv.ts:185-204` |
| Tool metadata beyond schema | `label`, `promptSnippet`, `promptGuidelines` (system-prompt hints steering `arxiv_search` vs `alphaxiv_search`) | `src/index.ts:166-177,450-455` |
| Progress streaming | `onUpdate?.({content:[...]})` during tool execution | e.g. `src/index.ts:227,287,302` |
| Message renderers / TUI widgets / prompts templates | none (plan 03 removed `pi.prompts`; `tests/skills-lint.test.ts:69-75` asserts they stay removed) | |

### 1.6 Pi-specific APIs used (no direct Claude Code equivalent)

- `pi.registerTool({name,label,description,promptSnippet,promptGuidelines,parameters,execute(toolCallId,params,signal,onUpdate,ctx)})` - `src/index.ts:164,261,319,442,553,607,636,661,691`.
- `pi.registerCommand(name,{description,handler(args,ctx)})` - `:355,384,412,521,704`.
- `pi.sendMessage(..., {triggerTurn:false})` display-only messages - `:374,404,544`.
- `pi.on("session_shutdown")` - `:725`.
- `ctx.ui.notify/setStatus/input`, `ctx.hasUI`, `ctx.cwd` - `:360,363,709,708,297`.
- `Type` from `typebox`, `StringEnum` from `@earendil-works/pi-ai`, `Type.Unsafe` workaround for Pi array coercion - `:16-17,63-72`.
- Pi agent dir resolution `PI_CODING_AGENT_DIR` / `~/.pi/agent` re-implemented in `src/config.ts:28-54`; config file `~/.pi/agent/pi-arxiv.json` (`:57-59`), key precedence env > file (`:73-78`), `0600` writes (`:84-91`).
- Skill invocation syntax `/skill:<name>` in every skill body (e.g. `skills/eli5/SKILL.md:8`).

### 1.7 Agent-neutral prose vs runtime code

| Category | Files | Portable as-is? |
|---|---|---|
| Pure instructions | 7 x `SKILL.md` | Yes structurally; **tool names inside must be remapped** (see 3.3) |
| Pure logic, host-independent | `src/arxiv.ts` (Atom parse, BibTeX), `src/alpha-sections.ts`, `src/annotations.ts` (modulo agent-dir), `src/config.ts` (modulo agent-dir), `src/alphaxiv.ts` (MCP client + parsing) | Yes, but needs a new *host*: MCP server process, CLI script, or dropped in favor of Claude doing it |
| Pi host glue | `src/index.ts` entirely | No; rewrite per target surface |
| Runtime script for a skill | `skills/read-paper/readpaper.py` | Yes, unchanged |
| Tests | `tests/*.test.ts` | Logic tests port with the code; `skills-lint.test.ts` must be rewritten for the new tool names |

## Part 2: Claude Code plugin facts (official docs)

Each row cites the page it was read from. Pages were fetched 2026-09-04.

### 2.1 Manifest and layout

| Fact | Detail | Source |
|---|---|---|
| Manifest | `.claude-plugin/plugin.json`; only `name` required (kebab-case; used as namespace). Optional: `displayName`, `version`, `description`, `author{name,email,url}`, `homepage`, `repository`, `license`, `keywords`, `metadata`, `defaultEnabled`, `dependencies`, `userConfig`, `channels`, and component paths `skills`, `commands`, `agents`, `workflows`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`, `experimental.{themes,monitors}`. Unrecognized fields are ignored (`claude plugin validate --strict` warns). | https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema |
| Auto-discovered layout | `skills/<name>/SKILL.md`, `commands/*.md`, `agents/*.md`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `monitors/monitors.json`, `bin/` (executables on Bash `PATH`), `scripts/` (conventional, not special), `settings.json` (only `agent`, `subagentStatusLine`). Everything except `plugin.json` must be at plugin root, **not inside `.claude-plugin/`**. | https://code.claude.com/docs/en/plugins-reference#plugin-directory-structure ; https://code.claude.com/docs/en/plugins#plugin-structure-overview |
| Path rules | Manifest paths are relative, start with `./` (`skills` may also be `"."`). `skills` *adds to* the default `skills/` scan; `commands`, `agents` *replace* defaults; `hooks`, `mcpServers`, `lspServers` merge. Paths escaping the plugin root are rejected ("path escapes plugin directory"). | https://code.claude.com/docs/en/plugins-reference#path-behavior-rules ; #path-traversal-limitations |
| `CLAUDE.md` in a plugin | "A `CLAUDE.md` file at plugin root is **not** loaded as project context. Plugins contribute context through skills, agents, and hooks." | https://code.claude.com/docs/en/plugins-reference#plugin-directory-structure |
| `bin/` | "Executables added to the Bash tool's `PATH` and invokable as bare commands while the plugin is enabled." Not allowed for plugins distributed via claude.ai org settings. | https://code.claude.com/docs/en/plugins-reference#file-locations-reference |
| Namespacing | Plugin skills are `/<plugin-name>:<skill>` (frontmatter `name` overrides the last segment; bare `/<skill>` also works unless taken). Agents: `<plugin>:<file>` (subfolders add segments). | https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name ; https://code.claude.com/docs/en/sub-agents |
| Single-skill plugin | A root `SKILL.md` with no `skills/` loads as one skill; use `skills/` for multi-skill plugins. | https://code.claude.com/docs/en/plugins-reference#skills |
| Testing | `claude --plugin-dir ./my-plugin` (repeatable; overrides an installed plugin of the same name for the session); `/reload-plugins` reloads skills, agents, hooks, plugin MCP and LSP servers; `claude plugin validate ./my-plugin`; `claude --debug`. | https://code.claude.com/docs/en/plugins#test-your-plugins-locally ; https://code.claude.com/docs/en/plugins-reference#debugging-and-development-tools |

### 2.2 Shipping an MCP server in a plugin

| Fact | Detail | Source |
|---|---|---|
| Where | `.mcp.json` at plugin root (auto-discovered), or `mcpServers` in `plugin.json` (inline object or path). Format is the standard `{"mcpServers": {...}}`. | https://code.claude.com/docs/en/plugins-reference#mcp-servers |
| Server fields | `command`, `args`, `env`, `type` (`stdio` default, `http`, `sse`, `ws`), `url`, `headers`, `headersHelper`, `timeout` | https://code.claude.com/docs/en/plugins-reference#mcp-servers ; https://code.claude.com/docs/en/mcp#option-1-add-a-remote-http-server |
| stdio via `npx`/`node` | Documented example: `{"command": "npx", "args": ["@company/mcp-server", "--plugin-mode"]}` and `{"command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server", ...}` | https://code.claude.com/docs/en/plugins-reference#mcp-servers |
| Placeholders | `${CLAUDE_PLUGIN_ROOT}` (install dir; changes on update), `${CLAUDE_PLUGIN_DATA}` (persistent `~/.claude/plugins/data/<id>/`, survives updates), `${CLAUDE_PROJECT_DIR}`. Substituted in stdio `command`/`args`/`env` and in http/sse/ws `url`/`headers`/`headersHelper`; also exported as env vars to MCP/LSP/hook subprocesses. | https://code.claude.com/docs/en/plugins-reference#environment-variables ; https://code.claude.com/docs/en/mcp#plugin-provided-mcp-servers |
| Generic env expansion | In `.mcp.json`: `${VAR}` and `${VAR:-default}` expand in `command`, `args`, `env`, `url`, `headers`. Unset vars load with a warning and the literal text. (Stated for `.mcp.json` generally; the plugin page adds "User environment access: access to the same environment variables as manually configured servers".) | https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson ; #plugin-provided-mcp-servers |
| Bearer auth on HTTP servers | `{"type":"http","url":"...","headers":{"Authorization":"Bearer ${API_KEY}"}}` is the documented pattern. | https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson |
| Plugin `userConfig` | Values prompted at enable time; `sensitive: true` masks and stores in secure storage; available as `${user_config.KEY}` "in MCP, LSP server configs, and hook commands", non-sensitive also in skill/agent content; all exported as `CLAUDE_PLUGIN_OPTION_<KEY>`. | https://code.claude.com/docs/en/plugins-reference#user-configuration |
| Tool names | `mcp__plugin_<plugin-name>_<server-name>__<tool-name>` (non `[A-Za-z0-9_-]` chars become `_`); server registers as `plugin:<plugin>:<server>`; hook matchers on the bare server key never fire for plugin servers. | https://code.claude.com/docs/en/mcp#plugin-provided-mcp-servers |
| Lifecycle | Servers start when the plugin is enabled; connect at session startup; `/reload-plugins` after enable/disable; remote servers used before may show `cached` and connect lazily on first call; unchanged servers keep live connections across reload. | https://code.claude.com/docs/en/mcp#plugin-provided-mcp-servers |
| Limits | Warning at >10,000 output tokens; default max 25,000 (`MAX_MCP_OUTPUT_TOKENS`); per-tool `_meta["anthropic/maxResultSizeChars"]`; startup timeout `MCP_TIMEOUT`; per-server `timeout` ms; idle window 5 min HTTP / 30 min stdio. | https://code.claude.com/docs/en/mcp#mcp-output-limits-and-warnings |
| Tool search | MCP tool definitions can be deferred; only names + server instructions load at start; descriptions/instructions truncated at 2 KB. | https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search |
| MCP prompts | A server's prompts appear as `/servername:promptname (MCP)` and `/mcp__servername__promptname [args]`. | https://code.claude.com/docs/en/mcp#use-mcp-prompts-as-commands |
| Node deps auto-install | On copy to cache, if `package.json` + `package-lock.json` (or bun lock) exist: `npm ci --ignore-scripts`, frozen, 60 s timeout, cannot be disabled; failure never blocks the plugin. Python deps: "install them from a hook into the persistent data directory". | https://code.claude.com/docs/en/plugins-reference#node-js-package-dependencies |

### 2.3 Skills

| Fact | Detail | Source |
|---|---|---|
| Commands merged into skills | "Custom commands have been merged into skills. A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way." Plugin `commands/` = "Skills as flat Markdown files. Use `skills/` for new plugins". | https://code.claude.com/docs/en/skills ; https://code.claude.com/docs/en/plugins#plugin-structure-overview |
| Frontmatter | `name`, `description` (recommended; combined with `when_to_use` capped at 1,536 chars), `when_to_use`, `argument-hint`, `arguments` (named positional), `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`. All optional. | https://code.claude.com/docs/en/skills#frontmatter-reference |
| Invocation control | default: both can invoke, description always in context; `disable-model-invocation: true`: only user, description **not** in context; `user-invocable: false`: only Claude. | https://code.claude.com/docs/en/skills#control-who-invokes-a-skill |
| Arguments | `$ARGUMENTS` (whole string; if no placeholder receives it, `ARGUMENTS: <value>` is appended), `$ARGUMENTS[N]`, `$N` (0-based; shell-style quoting), `$name` via `arguments:`; escape with `\$`. | https://code.claude.com/docs/en/skills#pass-arguments-to-skills ; #available-string-substitutions |
| Path substitutions | `${CLAUDE_SKILL_DIR}` (skill's own dir, "the skill's subdirectory within the plugin, not the plugin root"), `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`; substituted in body **and** in `allowed-tools` Bash rules, e.g. `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)` so a bundled script runs without prompting. | https://code.claude.com/docs/en/skills#available-string-substitutions |
| Supporting files | Skill dir may hold `reference.md`, `scripts/helper.py` ("executed, not loaded"); reference them from `SKILL.md`. | https://code.claude.com/docs/en/skills#add-supporting-files |
| Dynamic context | `` !`command` `` runs before the body is sent; failure aborts the invocation; never prompts (pre-approve via `allowed-tools`). | https://code.claude.com/docs/en/skills#inject-dynamic-context |
| Fork | `context: fork` + `agent: Explore|Plan|general-purpose|<custom>` runs the body as a subagent prompt, background by default (`background: false` to wait); no conversation history. | https://code.claude.com/docs/en/skills#run-skills-in-a-subagent |
| Lifecycle | Invoked content stays in context; `allowed-tools` grant lasts one turn; compaction keeps first 5,000 tokens of each, 25,000 total. | https://code.claude.com/docs/en/skills#skill-content-lifecycle |
| Live reload | `SKILL.md` edits are picked up immediately; `hooks/`, `.mcp.json`, `agents/` need `/reload-plugins`. | https://code.claude.com/docs/en/plugins-reference#skills-directory-plugins |

### 2.4 Subagents, hooks, LSP, tools

| Fact | Detail | Source |
|---|---|---|
| Subagent files | `agents/<name>.md`: frontmatter `name` (no `:`), `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills` (preloaded, full content), `mcpServers` (names or inline defs), `hooks`, `memory`, `background`, `isolation: worktree`, `color`, `effort`; body = system prompt. Plugin agents are lowest priority and named `<plugin>:<file>`; invoked by description, `@agent-<plugin>:<name>`, or the `Agent` tool. | https://code.claude.com/docs/en/sub-agents |
| Hooks | `hooks/hooks.json` `{"hooks": {"<Event>": [{"matcher", "hooks": [{"type":"command","command":..., "args", "timeout"}]}]}}`; events include `SessionStart` (stdout/`additionalContext` injected), `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStart/Stop`, `PreCompact`, `Setup`, `ConfigChange`, etc. Types: `command`, `http`, `mcp_tool`, `prompt`, `agent`. Plugin hooks merge with user/project hooks. | https://code.claude.com/docs/en/hooks |
| LSP | `.lsp.json` `{"<lang>": {"command", "args", "extensionToLanguage"}}`; binary must be installed separately. Not relevant to pi-arxiv. | https://code.claude.com/docs/en/plugins-reference#lsp-servers |
| Adding tools | "To add custom tools, connect an MCP server. To extend Claude with reusable prompt-based workflows, write a skill, which runs through the existing `Skill` tool rather than adding a new tool entry." | https://code.claude.com/docs/en/tools-reference |
| Built-in tools relevant to the port | `Read` ("support for images, PDFs"; PDFs >10 pages read via `pages` ranges, up to 20 pages per call), `WebFetch` (URL + prompt, lossy extraction via small model, 15-min cache), `WebSearch`, `Agent` (subagent, `subagent_type`), `Bash` (2-min default / 10-min max timeout; ~30,000-char inline output), `Skill`, `SendMessage`, `Monitor`. | https://code.claude.com/docs/en/tools-reference |

### 2.5 Marketplace, install scopes, versioning and updates

| Fact | Detail | Source |
|---|---|---|
| `marketplace.json` | `name`, `owner{name}`, `plugins[]{name, source, description?, version?, category?, strict?}`; relative sources `./plugin` resolve against the marketplace root; `metadata.pluginRoot` for bare names (v2.1.239+). | https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema ; #relative-paths |
| Install = copy | "Claude Code copies each installed plugin into the local versioned plugin cache at `~/.claude/plugins/cache`", one dir per resolved version; old versions swept ~14 days later; files outside the plugin dir are not copied; symlinks to elsewhere in the same marketplace are dereferenced, outside it skipped. | https://code.claude.com/docs/en/plugins-reference#plugin-caching-and-file-resolution ; https://code.claude.com/docs/en/plugin-marketplaces (walkthrough note) |
| Version resolution order | 1) `plugin.json` `version`; 2) marketplace entry `version`; 3) git commit SHA "for `github`, `url`, `git-subdir`, and relative-path sources in a git-hosted marketplace"; 4) archive sha256; 5) "`unknown`, for `npm` sources or local directories not inside a git repository". | https://code.claude.com/docs/en/plugins-reference#version-management |
| Update semantics | "Users get updates only when you bump this field. Pushing new commits without bumping it has no effect, and `/plugin update` reports 'already at the latest version'." Commit-SHA versioning requires omitting `version` in both places. | https://code.claude.com/docs/en/plugins-reference#version-management ; https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels |
| Auto-update | Background check after session start; "Third-party and local development marketplaces have auto-update disabled by default." `/plugin marketplace update <name>` then `/plugin update <plugin>@<marketplace>`. | https://code.claude.com/docs/en/discover-plugins#configure-auto-updates |
| Scopes | `user` (`~/.claude/settings.json`, default), `project` (`.claude/settings.json`), `local` (`.claude/settings.local.json`), `managed`. | https://code.claude.com/docs/en/plugins-reference#plugin-installation-scopes |
| Skills-dir plugins | A folder under `~/.claude/skills/` with `.claude-plugin/plugin.json` loads in place as `<name>@skills-dir` (no copy, no install); `claude plugin init <name>` scaffolds it. Alternative to a marketplace for a personal dev loop. | https://code.claude.com/docs/en/plugins-reference#skills-directory-plugins |
| Reload after install | Install summary says `Plugin is now active.` or `Run /reload-plugins to activate.`; `claude plugin install` from the shell takes effect next session or after `/reload-plugins`. | https://code.claude.com/docs/en/discover-plugins#install-plugins |
| Plugin MCP trust | Project-scope skills-dir plugins' MCP servers "go through the same per-server approval as a project `.mcp.json`"; marketplace/user-scope plugin servers start automatically. | https://code.claude.com/docs/en/plugins-reference#skills-directory-plugins ; https://code.claude.com/docs/en/mcp#plugin-provided-mcp-servers |

## Part 3: mapping

### 3.1 Piece-by-piece mapping table

| pi-arxiv piece | Claude Code equivalent (recommended) | Alternatives | Rationale / tradeoffs |
|---|---|---|---|
| `alphaxiv_search`, `alphaxiv_get_paper`, `alphaxiv_ask_paper`, `alphaxiv_read_code` | **`.mcp.json` `http` entry pointing straight at `https://api.alphaxiv.org/mcp/v1`** with `"headers": {"Authorization": "Bearer ${ALPHAXIV_API_KEY}"}` (or `${user_config.alphaxiv_api_key}`). Tools surface as `mcp__plugin_<plugin>_alphaxiv__discover_papers`, `..._get_paper_content`, `..._answer_pdf_queries`, `..._read_files_from_github_repository`. | (b) Bundle a Node stdio MCP server porting `src/alphaxiv.ts` + `alpha-sections.ts` (keeps the `alphaxiv_*` names, keyword derivation, section filter, normalized JSON); needs `package.json`+lockfile, `npm ci` at install, Node on PATH. (c) A skill + script calling the MCP endpoint via `node`/`python` (awkward: Streamable HTTP client in a one-shot script). | pi-arxiv's client code is a pass-through plus formatting (`src/alphaxiv.ts:281-335`). Claude can derive `keywords` itself (the upstream schema simply requires them), read the markdown result directly, and request `fullText` or specific sections in prose. Direct HTTP = zero runtime, zero deps, no `node_modules` copy, and Claude Code handles reconnect/`cached` state. Costs: lose `promptGuidelines` steering (move it into a skill/`when_to_use`), the section-extraction heuristic, and the local-annotation attach in `get_paper`. |
| `alphaxiv_annotate_paper`, `alphaxiv_list_annotations` | **Skill `paper-notes` with a tiny script** writing JSON under `${CLAUDE_PLUGIN_DATA}/annotations/` (survives updates), `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/notes.* *)`. | Fold into the Node MCP server if option (b) is chosen; or drop entirely and rely on notes in the repo / Claude Code memory. | Pure local FS (`src/annotations.ts`), no key. Claude Code's persistent data dir is the documented home for such state. Low value relative to cost; candidate to drop. |
| `arxiv_search`, `arxiv_download`, `arxiv_cite` | **One skill `arxiv` bundling `scripts/arxiv.mjs` (or `.py`) with subcommands `search|get|cite`** ported from `src/arxiv.ts`; `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/arxiv.mjs *)`; default download dir `~/Downloads/arxiv` kept. | (b) Same script in `bin/arxiv` so it is a bare command (nice for user-invoked commands; note `bin/` is "manual registration" per the file-locations table, verify in practice). (c) stdio MCP server. (d) No script: skill tells Claude to `curl "https://export.arxiv.org/api/query?..."` and parse Atom, then `Read` the PDF. | The Atom client is ~280 dependency-free lines; BibTeX/citation formatting is deterministic and better in code than prose. Script loads only when the skill fires (no always-on tool cost), runs through Bash, needs only `node` or `python3`. MCP would give typed args but is always loaded and needs a runtime + SDK. |
| `/arxiv <query>` | Skill `arxiv-search` with `disable-model-invocation: true`, `argument-hint: "<query>"`, body runs `... search "$ARGUMENTS"` and prints results. | Merge into the `arxiv` skill (one skill, model-invocable) and document `/<plugin>:arxiv <query>`. | Pi's display-only message (`triggerTurn:false`) has no equivalent; every skill invocation is a model turn. |
| `/arxiv-get <id>` | Skill `arxiv-get`, `disable-model-invocation: true`, `argument-hint: "<id|url>"`. | as above | |
| `/arxiv-cite <ids>` | Skill `arxiv-cite`, `disable-model-invocation: true`, `argument-hint: "<id|url> [id...]"`. | as above | |
| `/alphaxiv <query>` | Skill `alphaxiv-search`, `disable-model-invocation: true`, `argument-hint: "<query>"`, body calls the MCP `discover_papers` tool with derived keywords. | Skip; users can just ask. | |
| `/alphaxiv-setup` | **`userConfig` in `plugin.json`**: `{"alphaxiv_api_key": {"type":"string","title":"alphaXiv API key","sensitive":true, ...}}`, referenced as `${user_config.alphaxiv_api_key}` in `.mcp.json` headers; document `ALPHAXIV_API_KEY` env var as the fallback (`${ALPHAXIV_API_KEY:-...}`). | A `setup` skill that only *explains* how to set the env var. | Claude Code has no `ctx.ui.input`; and Claude must never type secrets into anything itself. `userConfig` is the native, secure-storage path. Verify the `sensitive` + `${user_config.*}` behaviour on the installed Claude Code version (docs do not state a minimum version). |
| `~/.pi/agent/pi-arxiv.json` key file | Replaced by `userConfig` secure storage / env var. | | `src/config.ts` becomes unnecessary. |
| `~/.pi/agent/pi-arxiv-annotations/` | `${CLAUDE_PLUGIN_DATA}/annotations/` | | |
| `pi.on("session_shutdown")` | Not needed (Claude Code owns MCP connections). If a stdio server is bundled, it is killed by Claude Code; a `SessionEnd` hook exists but adds nothing here. | | |
| `promptSnippet` / `promptGuidelines` | Move into the skill descriptions / `when_to_use` and into MCP **server instructions** (matter for tool search). No per-tool system-prompt hints for HTTP servers you do not control. | | https://code.claude.com/docs/en/mcp#for-mcp-server-authors |
| Skills `literature-review`, `source-comparison`, `research-review`, `paper-code-audit`, `deep-research`, `eli5` | **`skills/<same-name>/SKILL.md` as-is**, with the Tool Discipline block remapped (3.3). Consider `agents/{researcher,verifier,reviewer}.md` to restore Feynman's named roles. | `context: fork` for `eli5` only; not for `deep-research` (it pauses for user confirmation, `skills/deep-research/SKILL.md:44`, which a fork cannot do). | Frontmatter already matches (`name`, `description`). `/skill:<name>` -> `/<plugin>:<name>`. |
| Skill `read-paper` + `readpaper.py` | **`skills/read-paper/{SKILL.md,readpaper.py}`** unchanged logic; body references `python3 ${CLAUDE_SKILL_DIR}/readpaper.py ...`; `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/readpaper.py *)`; Pi `read` -> `Read`; drop the `read-pdf` sentence; mention that `Read` can ingest the PDF directly (<=10 pages whole, else `pages`) as the fastest "text pass". | Move PyMuPDF install to `${CLAUDE_PLUGIN_DATA}` venv via a `SessionStart`/`Setup` hook instead of `pip --user` at runtime. | The two-tier method and figure cropping remain valuable; Claude Code's native PDF reading covers only the text/vision pass of whole pages. |
| `tests/*.test.ts` | Port logic tests alongside whatever runtime survives; rewrite `skills-lint` for the new dead-name list (`web_search`, `fetch_content`, `subagent`, `alphaxiv_*` bare names, `/skill:`). | | `cc-skills` ships no tests (`cc-skills/CLAUDE.md:17`), so tests are optional per repo convention. |
| `README.md`, `AGENTS.md` | `README.md` (plugin usage), `CLAUDE.md` for maintainers only (not loaded by Claude Code when installed). | | |
| `reference/`, `.env`, `node_modules/`, `docs/` | **Do not place in the plugin directory** (would be copied into the cache; `.env` holds a live key). Keep research/plans under `cc-plugins/docs/` or the pi-arxiv repo. | | |

### 3.2 Two candidate layouts

**Layout A - zero runtime code (recommended first cut)**

```
cc-plugins/cc-arxiv/                      # or "research-papers"; name = namespace
  .claude-plugin/plugin.json              # name, version (bump on every change), userConfig.alphaxiv_api_key (sensitive)
  .mcp.json                               # "alphaxiv": {"type":"http","url":"https://api.alphaxiv.org/mcp/v1","headers":{"Authorization":"Bearer ${user_config.alphaxiv_api_key}"}}
  skills/
    arxiv/            SKILL.md + scripts/arxiv.mjs   # search|get|cite; model-invocable
    arxiv-search/     SKILL.md   (disable-model-invocation, argument-hint)  -> optional
    arxiv-get/        SKILL.md   (same)
    arxiv-cite/       SKILL.md   (same)
    alphaxiv-search/  SKILL.md   (same; calls the MCP tool)
    paper-notes/      SKILL.md + scripts/notes.mjs   # optional
    literature-review/ source-comparison/ research-review/ paper-code-audit/ deep-research/ eli5/  (SKILL.md each)
    read-paper/       SKILL.md + readpaper.py
  agents/             researcher.md verifier.md reviewer.md   # optional, restores named roles
  README.md
```

**Layout B - bundled Node MCP server (keeps `alphaxiv_*`/`arxiv_*` tool names exactly)**

Same as A plus `servers/pi-arxiv-mcp.mjs` (ports `src/{arxiv,alphaxiv,alpha-sections,annotations}.ts` behind `@modelcontextprotocol/sdk`'s server API), `package.json` + `package-lock.json` (so `npm ci --ignore-scripts` runs on install), and `.mcp.json` `{"arxiv-tools": {"command":"node","args":["${CLAUDE_PLUGIN_ROOT}/servers/pi-arxiv-mcp.mjs"],"env":{"ALPHAXIV_API_KEY":"${user_config.alphaxiv_api_key}","DATA_DIR":"${CLAUDE_PLUGIN_DATA}"}}}`. Tool names become `mcp__plugin_cc-arxiv_arxiv-tools__arxiv_search` etc. Tradeoff: typed inputs, exact name continuity, section filtering and annotation-attach preserved, progress via MCP; but always-loaded tool definitions (mitigated by tool search), Node required at runtime, `node_modules` copied per version, 60 s install budget, and SSE-flakiness handling (`src/alphaxiv.ts:141-151`) has to be re-hosted.

### 3.3 Tool-name remap for the skill bodies (the core authoring work)

| In pi-arxiv skills | In Claude Code (Layout A) | In Claude Code (Layout B) |
|---|---|---|
| `web_search` | `WebSearch` | same |
| `fetch_content` (`urls` array) | `WebFetch` (single `url` + `prompt`; lossy summary) | same |
| `subagent` with role via system prompt | `Agent` tool (`subagent_type: general-purpose`/`Explore`) or plugin agents `@agent-<plugin>:researcher` etc. | same |
| `read` (view PNG) | `Read` | same |
| `alphaxiv_search` | `mcp__plugin_<plugin>_alphaxiv__discover_papers` (must pass `keywords[]`, `question`, `difficulty`) | `mcp__plugin_<plugin>_<server>__alphaxiv_search` |
| `alphaxiv_get_paper` | `..._alphaxiv__get_paper_content` (`url`, `fullText?`) | `..._alphaxiv_get_paper` |
| `alphaxiv_ask_paper` | `..._alphaxiv__answer_pdf_queries` (`paper`, `queries[]`) | `..._alphaxiv_ask_paper` |
| `alphaxiv_read_code` | `..._alphaxiv__read_files_from_github_repository` (`githubUrl`, `path`) | `..._alphaxiv_read_code` |
| `arxiv_search` / `arxiv_download` / `arxiv_cite` | `${CLAUDE_SKILL_DIR}/scripts/arxiv.mjs search|get|cite ...` via Bash (or `arxiv ...` if in `bin/`) | `..._arxiv_search` etc. |
| `/skill:<name>` | `/<plugin>:<name>` | same |
| "memory tool if visible" (`deep-research:38`) | leave conditional; Claude Code has no memory *tool* by default | same |

Tension to resolve: `cc-skills/CLAUDE.md:25-26` says "Skill bodies are agent-neutral: avoid Claude-Code-only tool names", whereas these skills exist to pin literal tool names (`skills/*/SKILL.md` "Tool Discipline (Read First)"). Options: (i) accept Claude-Code-specific names in this plugin and say so in its `CLAUDE.md`; (ii) describe capabilities generically ("the web-search tool", "the paper-discovery MCP tool") and let the skill listing/tool descriptions bind them; (iii) keep a per-host remap table at the top of each skill.

### 3.4 Things with no equivalent (flag)

- Display-only messages without a model turn (`pi.sendMessage(..., {triggerTurn:false})`, `src/index.ts:374,404,544`) and status-bar/notify UI (`ctx.ui.setStatus/notify`).
- Interactive secret prompt (`ctx.ui.input`, `src/index.ts:709`) -> `userConfig` at enable time instead.
- Per-tool `promptGuidelines`/`promptSnippet` for tools you do not own (upstream alphaXiv MCP) -> skill descriptions only.
- Pi `Type.Unsafe` array workaround (`src/index.ts:63-72`) -> irrelevant (schemas are the server's).
- `/reload` semantics: Claude Code `SKILL.md` edits are live, but `.mcp.json`/agents need `/reload-plugins`, and *installed* copies do not see source edits at all until `version` is bumped and `/plugin update` runs (2.5). Use `claude --plugin-dir` while developing.

### 3.5 Open questions

1. **Does `${VAR}` env expansion apply inside a *plugin's* `.mcp.json`?** The MCP page documents it for `.mcp.json` generally and says plugin servers have "the same environment variables as manually configured servers"; the plugin page only lists `${CLAUDE_PLUGIN_*}` and `${user_config.*}` substitution. Verify with `claude --debug` / `claude mcp list` after `--plugin-dir`.
2. **Is alphaXiv's Streamable HTTP server compatible with Claude Code's MCP client** (pi-arxiv saw transient "SSE stream disconnected"/"Bad Gateway" errors it retries, `src/alphaxiv.ts:141-151`)? Claude Code documents automatic reconnection; needs a live check.
3. **`userConfig` with `sensitive: true`**: confirm it prompts on `/plugin install` from a local marketplace and that `${user_config.alphaxiv_api_key}` resolves in `headers`. No minimum version is stated.
4. **Script runtime choice for the arXiv skill:** Node (direct port of `src/arxiv.ts`, but Node not guaranteed on PATH for native Claude Code installs) vs Python 3 (present on macOS by default, consistent with `readpaper.py`).
5. **Keep or drop annotations?** They are Pi-local state with modest value; Claude Code memory/notes or repo files may suffice.
6. **Plugin name/namespace:** `cc-arxiv`, `arxiv`, or `research-papers`? It prefixes every skill (`/<name>:literature-review`) and every MCP tool name.
7. **Versioning workflow:** since `cc-plugins/` is not a git repo, either (a) keep explicit `version` and bump on every change, or (b) `git init` the marketplace root so the commit-SHA fallback works when `version` is omitted; or (c) develop via `~/.claude/skills/<name>/` as a `@skills-dir` plugin (loaded in place, no copy) and only publish to the marketplace for releases.
8. **Should the six workflow skills stay model-invocable?** Each always-on description costs context (1,536-char cap each; listing budget 1% of context). `read-paper`, `eli5`, `literature-review` are natural auto-triggers; `deep-research`/`research-review`/`paper-code-audit` could be user-only.
9. **Named agents:** ship `agents/researcher.md`, `verifier.md`, `reviewer.md` (Feynman's originals live in `reference/feynman/.feynman/agents/`) or keep the Pi-era "role via prompt" wording with the built-in `general-purpose`/`Explore` agents?
10. **`bin/` vs `scripts/`:** the file-locations table marks `bin/` as "No (manual registration)" under auto-discovery while the text says executables there are added to PATH; test whether a `bin/arxiv` shim works without manifest changes.
