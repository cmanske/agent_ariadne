# Instructions — Ariadne

## Requirements

- Python 3.12 or newer (uses `pathlib` APIs like `Path.is_relative_to`,
  so 3.11 and older will not work).
- No third-party packages. The script uses only the standard library
  (`argparse`, `hashlib`, `json`, `re`, `sys`, `datetime`, `pathlib`), so
  there is nothing to `pip install` and no virtualenv required.

## Setup

Ariadne isn't installed system-wide. You vendor `agent_ariadne.py` once
into the project you want to govern, and that copy is pinned to whatever
version you copied. Updating later is a deliberate re-copy, never an
automatic pull — an in-flight project shouldn't have its behavior change
out from under it.

**Recommended — clone and inspect before running anything:**

```bash
git clone --depth 1 https://github.com/<you>/ariadne.git .ariadne_setup
mkdir -p .ariadne
cp .ariadne_setup/agent_ariadne.py .ariadne/agent_ariadne.py
rm -rf .ariadne_setup
```

**Fast path** (also supported, once `install.sh` ships in Phase 3):

```bash
curl -fsSL https://raw.githubusercontent.com/<you>/ariadne/main/install.sh | bash
```

Until Phase 3 ships `install.sh`, use the clone-and-copy path above and
just copy `agent_ariadne.py` into your project (either at the repo root
during development, or into `.ariadne/`). The commands below assume the
file is on your project root; if you vendored it into `.ariadne/`,
substitute `python3 .ariadne/agent_ariadne.py` everywhere.

## Running it

All commands take an optional `--path <dir>` (default: current directory)
to point at a project root other than the one you're standing in.

```bash
# 1. Scaffold all nine managed markdown files, skipping any that exist.
#    Project name is auto-detected from package.json / pyproject.toml /
#    the directory name; override with --name.
python3 agent_ariadne.py init --name MyProject

# 2. Check current phase, milestone, and task progress (parsed live
#    out of PROJECT_STATUS.md).
python3 agent_ariadne.py status

# 3. Check that the managed files are well-formed: checklist markers,
#    required config settings, valid enum values, schema-version tags.
#    Exits non-zero on errors (warnings alone still exit 0).
python3 agent_ariadne.py validate

# 4. Inject/refresh the Ariadne header on every source file under the
#    project root and rebuild CODE_INDEX.md. Files whose stored checksum
#    still matches their body are left untouched (idempotent). Supports
#    comment-syntax headers for many languages and a markdown-cell header
#    for .ipynb notebooks.
python3 agent_ariadne.py annotate
# Annotate only a subtree:
python3 agent_ariadne.py annotate --target src/

# 5. Read or change settings in PROJECT_CONFIG.md.
python3 agent_ariadne.py config get                # list all settings
python3 agent_ariadne.py config get scope_enforcement
python3 agent_ariadne.py config set scope_enforcement strict
python3 agent_ariadne.py config set spec_depth thorough
```

### What it manages

`init` writes these nine files (existing files are never overwritten —
re-run `init` to fill in any that are missing):

| File | What it's for |
|---|---|
| `AGENTS.md` | Auto-loaded agent memory: project description, constitution, learned patterns |
| `PROJECT_STATUS.md` | Phases, milestones, tasks, checklists, decisions, last-session summary |
| `PROJECT_SCOPE.md` | In/out scope, feature registry, and a per-task spec sheet (EARS-format acceptance criteria) |
| `PROJECT_CONFIG.md` | Settings (`scope_enforcement`, `spec_depth`, `branching_strategy`) and cached per-language validation commands |
| `ARCHITECTURE.md` | This file's sibling — directory tree, module map, design principles |
| `CODE_INDEX.md` | Every source file and what it does — rebuilt fully automatically by `annotate` |
| `DEVELOPER_LOG.md` | Append-only session log |
| `README.md` | GitHub-facing project description |
| `INSTRUCTIONS.md` | This file — setup and usage guide |

You edit all of these by hand (they're plain markdown). The only one that
is fully machine-regenerated and should not be hand-edited is
`CODE_INDEX.md` — `annotate` will overwrite it on the next run.

### Task lifecycle (Phase 2, not yet implemented)

The intended flow is `not_started → clarifying → in_progress → self_check →
awaiting_human_review → done`. Phase 1 ships the deterministic plumbing
(`init`, `annotate`, `validate`, `status`, `config`); the `task`
subcommand group that enforces those transitions lands in Phase 2.

## Common issues

- **`validate` flags a double-brace pair in your own prose.** The
  template-residue check matches the double-brace glyph on the character
  pattern alone, so a sentence that writes the literal two-braces /
  two-braces sequence to *describe* the convention will be flagged even
  though it is real prose, not residue. Refer to the convention by name —
  "double-brace placeholder" or "double curly brackets" — and never write
  the literal sequence (an opening brace pair, text, a closing brace
  pair) into managed markdown. The literal glyph is fine in source files
  like agent_ariadne.py, which `validate` does not check.
- **`init` says everything was skipped.** All nine files already exist in
  the project root. `init` never overwrites; delete the ones you want
  reset, or edit them in place.
- **`validate` reports "missing setting" warnings.** A required setting
  (`scope_enforcement`, `spec_depth`, `branching_strategy`) isn't in
  `PROJECT_CONFIG.md`. Fix with `config set <key> <value>`, e.g.
  `python3 agent_ariadne.py config set scope_enforcement strict`. Warnings
  exit 0; only errors exit non-zero.
- **`validate` errors on `scope_enforcement` / `spec_depth` value.** These
  are enum-checked: `scope_enforcement` must be `strict` or `soft`;
  `spec_depth` must be `minimal`, `standard`, or `thorough`. Set a valid
  value via `config set`.
- **`annotate` skips a file you expected it to touch.** It only annotates
  files whose extension is in its comment-syntax table (`.py`, `.r`, `.ts`,
  `.js`, `.go`, `.rs`, `.sql`, etc.) plus `.ipynb` notebooks. Markdown,
  data, and binary files are deliberately skipped, as are anything in
  `node_modules`, `.git`, `dist`, `__pycache__`, `.venv`, etc.
- **`annotate` never converges / rewrites on every run.** This means the
  file's body genuinely keeps changing, or (if true) the header markers
  were hand-edited — the `ARIADNE HEADER — DO NOT EDIT MANUALLY` /
  `END ARIADNE HEADER` block must be left intact for the checksum math to
  work.
- **`--path <dir>` doesn't seem to do anything.** It names the project
  root the command operates on, not the file to annotate. To annotate a
  subtree, use `annotate --target <subdir>`.
