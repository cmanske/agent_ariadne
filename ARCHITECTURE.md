# Architecture — Ariadne
<!-- schema: v1 -->

> Auto-regenerated when directory structure changes or a file/module is
> added — not on every function-level edit. Directory scan is deterministic;
> diagram and interface prose are written by the agent from that scan.

## System Overview

Ariadne is a single Python 3.12+ CLI (`agent_ariadne.py`, standard library
only) that acts as the deterministic backbone of an agent-governed project.
It reads and writes a fixed set of ALL-CAPS markdown files
(`AGENTS.md`, `PROJECT_STATUS.md`, `PROJECT_SCOPE.md`, `PROJECT_CONFIG.md`,
plus this file, `CODE_INDEX.md`, and `DEVELOPER_LOG.md`) that together hold
all project state — there is no JSON state file and no database. The CLI
itself never prompts: it parses markdown, validates it, injects
checksum-bearing headers into source files, rebuilds the code index, and
prints plain-text summaries. An external coding agent (Pi, Claude Code,
Codex, OpenCode, or any tool that reads `AGENTS.md`) drives the workflow by
calling the CLI at the right moments — session start, before a task starts,
after self-check, on completion — and handling all human interaction
(clarifying questions, review sign-off) that the CLI deliberately refuses
to do itself.

Data flow is linear and stateless per invocation: each command reads the
relevant markdown files from disk, performs a deterministic transformation
in memory, and writes results back to the same files. The only persistent
state is the markdown; the only cross-command coupling is the shared file
format and the schema-version tag each managed file carries on line 2.
Source-file headers carry their own checksum inside the file (no separate
manifest), so `annotate` can detect drift on its own by recomputing and
comparing in place.

## Directory Structure

```
agent_ariadne/
├── AGENTS.md
├── ARCHITECTURE.md
├── CODE_INDEX.md
├── DEVELOPER_LOG.md
├── LICENSE
├── PROJECT_CONFIG.md
├── PROJECT_SCOPE.md
├── PROJECT_STATUS.md
├── README.md
└── agent_ariadne.py
```

## Module Responsibilities

| Module/File | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `agent_ariadne.py` | The entire deterministic core: arg parsing, file scaffolding (`init`), annotation + code-index rebuild (`annotate`), status rendering (`status`), well-formedness checks (`validate`), and settings get/set (`config`). Single stdlib-only file, deliberately not split into a package. | Project root path; one `ALL-CAPS` markdown files; source files under the root | Modified `ALL-CAPS` markdown files; source files with injected headers; rebuilt `CODE_INDEX.md`; plain-text stdout; exit code 0/1 |

## External Dependencies

| Dependency | Purpose | Notes |
|---|---|---|
| Python 3.12+ stdlib | Everything: `argparse`, `hashlib`, `json`, `re`, `sys`, `datetime`, `pathlib` | Zero third-party packages, by design — the file is meant to be vendored into a project's `.ariadne/` and run with only a system Python |

## Design Principles

- **Deterministic first.** LLM judgment is used only where it's genuinely required — filling in narrative descriptions, judging spec-sheet ambiguity, writing diagram prose. Everything else is plain Python, so two runs over the same input produce byte-identical output.
- **No hidden state.** Every file a human can open is the same file the CLI parses. There is no JSON state file and no separate manifest: each source file's checksum lives inside its own header, and project state lives in the `ALL-CAPS` markdown the human is already expected to read.
- **The CLI never prompts.** It reads and writes files and prints plain text; it never waits on stdin. All human interaction (clarifying questions, review sign-off, retry decisions) is the calling agent's responsibility. This keeps the CLI scriptable from hooks and CI alike.
- **Validation is tiered, not one-size-fits-all.** Per-language validation commands are cached in `PROJECT_CONFIG.md` (a real test suite where one exists, a compile/parse check where that's all there is, human review otherwise), rather than assuming every project has `pytest`.
- **Idempotent and drift-aware.** `init` skips files that already exist; `annotate` compares the recomputed checksum to the one already in a file's header and only rewrites when they differ, so repeated runs converge instead of churning.
- **Adapts to the project, not the other way around.** `scope_enforcement` (strict/soft) and `spec_depth` (minimal/standard/thorough) are per-project toggles in `PROJECT_CONFIG.md`, not fixed policies baked into code.
