# cc-arxiv

Research-paper skills for [Claude Code](https://docs.claude.com/en/docs/claude-code), packaged as a plugin. Migrated from the Pi extension `pi-arxiv` with the runtime code removed: alphaXiv is reached directly as an MCP server, arXiv through a small bundled script, and the workflows are plain skills.

## What you get

**MCP tools** (server `alphaxiv`, tool names `mcp__plugin_cc-arxiv_alphaxiv__<tool>`), provided by alphaXiv's hosted server:

| Tool | Purpose |
| --- | --- |
| `discover_papers` | Semantic topic discovery. Requires `keywords[]`, `question`, `difficulty` (1–10). |
| `get_paper_content` | AI report on a paper, or the raw text with `fullText: true`. Uses alphaXiv AI quota. |
| `answer_pdf_queries` | Ask questions about a paper's PDF. Uses alphaXiv AI quota. |
| `read_files_from_github_repository` | Read a paper's linked GitHub repo. |

The server also exposes alphaXiv library, folder, and researcher tools; the skills below only rely on the four above.

**Skills** (`/cc-arxiv:<name>`):

| Skill | Description |
| --- | --- |
| `arxiv` | Search arXiv by author/title/id/category/date, download a PDF, or emit BibTeX / APA citations. Bundles `scripts/arxiv.py`. |
| `literature-review` | Plan, gather, synthesize, cite, verify, deliver a literature review to `outputs/`. |
| `source-comparison` | Grounded comparison matrix across papers, tools, or claims. |
| `research-review` | Severity-graded critique of a paper or draft. |
| `paper-code-audit` | Compare a paper's claims against its public codebase. |
| `deep-research` | Source-heavy investigation with provenance; pauses for plan approval. |
| `eli5` | Plain-English explainer of a paper or idea, inline in chat. |

The workflow skills name Claude Code tools literally (`WebSearch`, `WebFetch`, `Agent`, `Read`, the MCP tools above, and the `arxiv` script), so they are Claude Code specific by design.

## Setup

1. **alphaXiv API key.** Get one from your alphaXiv account settings. The plugin declares it as a `userConfig` option, so Claude Code (and Cowork) prompt for it when the plugin is enabled and store it in the OS keychain. It is never written to the repo or to `settings.json`.

   To change it later, run `/plugin` and reconfigure `cc-arxiv`.

   The plugin's `.mcp.json` sends it as a bearer token. Without it the `alphaxiv` server reports HTTP 401 and only the alphaXiv tools are unavailable; the `arxiv` skill and everything else still works.

2. **Python 3.9+** on `PATH` as `python3`. `arxiv.py` has no dependencies. PDFs are read with Claude Code's built-in `Read` tool.

## Install

**Quick test (no install)** — load the plugin for one session:

```bash
claude --plugin-dir /Users/panda/repo/Agents/cc-plugins/cc-arxiv
```

**Persistent install** from the local `cc-plugins` marketplace:

```bash
claude plugin marketplace add /Users/panda/repo/Agents/cc-plugins
```

```bash
claude plugin install cc-arxiv@cc-plugins
```

Run `/mcp` in a session to confirm `plugin:cc-arxiv:alphaxiv` is connected.

## Releasing a change

Installs are copies. After editing, bump `version` in `.claude-plugin/plugin.json`, commit, then:

```bash
claude plugin marketplace update cc-plugins && claude plugin update cc-arxiv@cc-plugins
```

Restart Claude Code or run `/reload-plugins`. Edits made while running with `--plugin-dir` need no bump.

## Tests

```bash
python3 -m unittest discover -s tests
```

Covers the pure functions of `arxiv.py` (feed parsing, id normalization, date clauses, citations, filenames, result formatting). Network paths are checked by running the script by hand.
