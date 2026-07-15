#!/usr/bin/env python3
"""
agent_ariadne.py — deterministic project-governance CLI for Ariadne.

Stdlib only. Python 3.12+. Zero third-party dependencies, by design — this
script is meant to be vendored directly into a project's .ariadne/ directory
and run with nothing but a system Python install.

PHASE 1 (this file): core deterministic engine.
    init        Scaffold all Ariadne-managed files if missing
    status      Render current phase / milestone / task status
    validate    Check well-formedness of all Ariadne-managed files
    annotate    Inject/update file headers, rebuild CODE_INDEX.md
    config      Get/set PROJECT_CONFIG.md settings

PHASE 2 (not yet built): task lifecycle commands (start/advance/complete),
    git commit-message suggestions.
PHASE 3 (not yet built): install.sh + per-agent adapters (Pi, Claude Code,
    Codex, OpenCode).

See PROJECT_AGENT_SPEC.md for the full design this implements.

Design notes baked into this file (do not "simplify" these away without
re-reading the spec — each one was a deliberate decision):
  - No JSON state file anywhere. All state lives in the ALL-CAPS markdown
    files themselves. Checksums for annotation live inside each source
    file's own header, not in a separate manifest.
  - The CLI never prompts interactively. It reads/writes files and prints
    plain text. The calling agent is responsible for all human interaction.
  - Validation is tiered per file extension (see validate_command docs)
    rather than assuming one test framework fits every language.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

# ============================================================
#  CONSTANTS
# ============================================================

ARIADNE_DIR = ".ariadne"
SCHEMA_VERSION = "v1"
BORDER_WIDTH = 90

MANAGED_FILES = [
    "AGENTS.md",
    "PROJECT_STATUS.md",
    "PROJECT_SCOPE.md",
    "PROJECT_CONFIG.md",
    "ARCHITECTURE.md",
    "CODE_INDEX.md",
    "DEVELOPER_LOG.md",
    "README.md",
    "INSTRUCTIONS.md",
]

VERSIONED_FILES = [
    "AGENTS.md", "PROJECT_STATUS.md", "PROJECT_SCOPE.md", "PROJECT_CONFIG.md",
    "ARCHITECTURE.md", "CODE_INDEX.md", "DEVELOPER_LOG.md",
]

# Comment syntax per file extension for header injection.
COMMENT_SYNTAX: dict[str, str] = {
    ".py": "#", ".r": "#", ".R": "#", ".rb": "#", ".sh": "#", ".bash": "#",
    ".zsh": "#", ".ps1": "#", ".toml": "#",
    ".ts": "//", ".tsx": "//", ".js": "//", ".jsx": "//", ".svelte": "//",
    ".vue": "//", ".c": "//", ".cpp": "//", ".cc": "//", ".h": "//", ".hpp": "//",
    ".cs": "//", ".go": "//", ".rs": "//", ".swift": "//", ".kt": "//",
    ".java": "//", ".scala": "//",
    ".sql": "--", ".lua": "--", ".hs": "--",
}

# Files that get header injection via a synthetic markdown cell rather than
# a comment-line header, because their body is JSON, not plain text.
NOTEBOOK_EXTENSIONS = {".ipynb"}

SKIP_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".lock", ".log", ".map",
    ".md", ".txt", ".csv", ".env", ".gitignore",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".zip", ".tar", ".gz",
}

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".venv", "venv", ".next", ".nuxt", "coverage", ".pytest_cache",
    ARIADNE_DIR,
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "poetry.lock", "uv.lock",
    "pnpm-lock.yaml", "Pipfile.lock",
}

HEADER_START = "ARIADNE HEADER \u2014 DO NOT EDIT MANUALLY"
HEADER_END = "END ARIADNE HEADER"

# Default validation command guesses, used only the first time an extension
# is seen. These are starting points, not final answers -- config.py caches
# whatever is actually confirmed (auto-detected or user-set) per project.
DEFAULT_VALIDATION_GUESS: dict[str, tuple[int, str]] = {
    ".py": (2, "python -m py_compile {file}"),
    ".r":  (2, "Rscript -e \"source('{file}')\""),
    ".R":  (2, "Rscript -e \"source('{file}')\""),
    ".ts": (2, "npx tsc --noEmit"),
    ".tsx": (2, "npx tsc --noEmit"),
    ".js": (2, "node --check {file}"),
    ".jsx": (2, "node --check {file}"),
    ".go": (2, "go build ./..."),
    ".rs": (2, "cargo check"),
}


def today() -> str:
    return date.today().isoformat()


# ============================================================
#  FILE HELPERS
# ============================================================

def read_if_exists(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return None


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def embed_schema_version(content: str, version: str) -> str:
    """Embed/replace the schema version tag on line 2 of a markdown file."""
    lines = content.split("\n")
    tag = f"<!-- schema: {version} -->"
    if len(lines) > 1 and lines[1].startswith("<!-- schema:"):
        lines[1] = tag
    else:
        lines.insert(1, tag)
    return "\n".join(lines)


def read_schema_version(content: str) -> str | None:
    m = re.search(r"^<!-- schema:\s*(v\d+)\s*-->", content, re.MULTILINE)
    return m.group(1) if m else None


# ============================================================
#  TEMPLATES  (init command)
# ============================================================

def tpl_agents_md(project_name: str) -> str:
    return embed_schema_version(f"""# Agent Memory \u2014 {project_name}

> Auto-loaded at session start. Keep accurate and concise.
> Update whenever project direction, structure, or state changes meaningfully.

## What this project is

{{One paragraph: what it does, who uses it, what problem it solves.}}

## Agent rules (Constitution)

> This section is the project's constitution \u2014 non-negotiable principles that
> every spec sheet, plan, and task is checked against before and during work.
> Treat these as hard constraints, not suggestions.

- Before starting any task: read the task's spec sheet in PROJECT_SCOPE.md. If
  anything is vague or ambiguous, ask the human before writing code.
- Follow the task lifecycle: clarifying -> in_progress -> self_check ->
  awaiting_human_review -> done. Never mark a task done without human
  confirmation of the review checklist.
- Check CODE_INDEX.md before grepping the codebase for structure questions.
- Do not implement a feature that isn't in PROJECT_SCOPE.md's Approved
  Features without flagging it and asking first (see scope_enforcement in
  PROJECT_CONFIG.md for how strict this should be for this project).
- Do not remove an Implemented Feature or delete a tracked source file
  without confirming with the human first.
- Before beginning implementation, check the task's Acceptance Criteria
  (EARS-format, in its spec sheet) are unambiguous. If a criterion can't be
  read as a single testable statement, that's a signal to clarify, not proceed.
- Direct, no filler. State what you're doing, do it, report what happened.

## Learned patterns

> Preferences and conventions discovered while working on this project.
> Each entry is validated with the human before being added here \u2014 never
> record a pattern without confirming it first. Unlike DEVELOPER_LOG.md
> (chronological, append-only), this section reflects current understanding
> and can be edited or corrected as patterns are confirmed or refined.

- {{pattern or preference, once confirmed}}

## Reading order

1. AGENTS.md <- you are here (auto-loaded; includes constitution + learned patterns)
2. PROJECT_STATUS.md <- phases, milestones, tasks, last session summary
3. PROJECT_SCOPE.md <- boundaries, feature registry, per-task spec sheets
4. PROJECT_CONFIG.md <- settings (scope_enforcement, spec_depth, etc.)
5. ARCHITECTURE.md <- directory structure, module map, diagrams
6. CODE_INDEX.md <- every source file and what it does
7. Source files <- only when the above are insufficient

## Project files

| File | Purpose |
|---|---|
| AGENTS.md | This file. Auto-loaded memory + constitution + learned patterns. |
| PROJECT_STATUS.md | Phases, milestones, tasks, checklists, decisions, last session |
| PROJECT_SCOPE.md | Boundaries, feature registry, per-task spec sheets |
| PROJECT_CONFIG.md | Settings: scope_enforcement, spec_depth, validation commands |
| ARCHITECTURE.md | Directory structure, module map, diagrams (auto-regenerated) |
| CODE_INDEX.md | All source files and descriptions (fully automatic) |
| DEVELOPER_LOG.md | Append-only session log \u2014 what happened, not what was learned |
| README.md | GitHub-facing project description |
| INSTRUCTIONS.md | Setup and usage guide |
""", SCHEMA_VERSION)


def tpl_project_status_md(project_name: str) -> str:
    return embed_schema_version(f"""# Project Status \u2014 {project_name}

> Tracks current state, decisions, and session history.
> Task IDs: P1_T3 (zero-padded to P01_T03 once phase or task count hits 10+).
> Checklist markers: [ ] not started \u00b7 [x] complete \u00b7 [O] deferred (moved to
> another task \u2014 see the inline note for which one and why).

## Project summary

- **Name**: {project_name}
- **Purpose**: {{what it does and why \u2014 2-3 sentences}}
- **Stack**: {{languages / frameworks}}
- **Entry point**: {{e.g. main.py}}
- **Running it**: {{e.g. python main.py}}

## Current phase

- **Phase**: {{phase name and number}}
- **Status**: Not Started

## Roadmap

| Phase | Name | Status |
|---|---|---|
| 1 | {{phase name}} | Not Started |

## Milestones

| Milestone | Phase | Tasks | Definition of Done |
|---|---|---|---|

### Phase 1: {{Name}}

**P1_T1: {{Task name}}** ({{Effort: Easy/Medium/Hard}}, {{Speed: Fast/Slow}}) \u2014 Not Started
- [ ] {{checklist item}}
- [ ] {{checklist item}}

## Recent decisions

> Reverse chronological. Never edit existing entries.

- **{today()}** \u2014 Project initialized.

## Open questions

> Move to Recent decisions when resolved.

- [ ] {{question or uncertainty}}

## Known issues / tech debt

- None yet.

## Last session summary

- **Date**: {today()}
- **Done**: Project scaffolding initialized via `agent_ariadne.py init`.
- **Left off at**: Initial scaffolding complete.
- **Next action**: Run the planning conversation to define phases and tasks.
""", SCHEMA_VERSION)


def tpl_project_scope_md(project_name: str) -> str:
    return embed_schema_version(f"""# Project Scope \u2014 {project_name}

> Defines project boundaries, the feature registry, and every task's spec
> sheet. The agent checks this file before implementing any feature and
> before removing any existing one. Never delete entries \u2014 move them
> between sections instead.

## Scope definition

### Purpose
{{One sentence: what this project does and for whom.}}

### Inclusion criteria
- {{what's explicitly in scope}}

### Exclusion criteria
- {{what's explicitly out of scope}}

### Key constraints
- {{hard limits that cannot be changed}}

## Feature registry

### Approved Features
> Explicitly planned and approved. Do not implement anything not listed here
> without approval first.

### Implemented Features
> Fully working. The agent will confirm before removing anything here.

### Planned Features
> Approved but not yet implemented.

### Removed Features
> Implemented and later removed. Preserved for reference.

### Rejected Features
> Explicitly considered and decided against. Preserved to avoid relitigating.

### Future Considerations
> Ideas not on the roadmap. No commitment.

## Task Spec Sheets

> Organized by phase and task. Depth follows PROJECT_CONFIG.md's `spec_depth`
> setting unless the agent proposes a different depth for a specific task
> (subject to `scope_enforcement`).

### Phase 1

#### P1_T1: {{Task name}}

**Goal**
{{<<LLM: 1-2 sentences on what this task accomplishes>>}}

**Inputs / dependencies needed**
{{<<LLM: models, libraries, upstream data this task depends on>>}}

**Steps**
{{<<LLM: ordered steps/stages>>}}

**Data formats / schemas**
{{<<LLM: input and output shapes>>}}

**Edge cases & failure handling**
{{<<LLM: what could go wrong and how it's handled>>}}

**Acceptance criteria (EARS format)**
> Each line should read as one unambiguous, testable statement: "The system
> shall <response> when <trigger>" (or "while <state>", "if <condition>,
> then the system shall <response>"). If a criterion can't be phrased this
> way, that's a signal it's still ambiguous \u2014 clarify before starting, don't
> proceed and hope it works out.
{{<<LLM: one EARS-format statement per line>>}}

**Constraints / notes**
{{<<LLM: project-specific best practices, versioning rules, device handling, etc.>>}}
""", SCHEMA_VERSION)


def tpl_project_config_md(project_name: str) -> str:
    return embed_schema_version(f"""# Project Config \u2014 {project_name}

> Read and written by agent_ariadne.py. Hand-edits are fine but must keep
> this structure -- run `agent_ariadne.py validate` after editing by hand.

## Settings

- scope_enforcement: soft
- spec_depth: standard
- branching_strategy: none

## Detected Language Stacks

| Extension | Language | Validation Tier | Command | Set by |
|---|---|---|---|---|

## Contributors

""", SCHEMA_VERSION)


def tpl_architecture_md(project_name: str) -> str:
    return embed_schema_version(f"""# Architecture \u2014 {project_name}

> Auto-regenerated when directory structure changes or a file/module is
> added -- not on every function-level edit. Directory scan is deterministic;
> diagram and interface prose are written by the agent from that scan.

## System Overview

{{<<LLM: 2-4 sentences \u2014 how the parts fit together and data flows through the system>>}}

## Directory Structure

```
{{<<TOOL: directory tree injected here by `agent_ariadne.py annotate`>>}}
```

## Module Responsibilities

| Module/File | Responsibility | Inputs | Outputs |
|---|---|---|---|

## External Dependencies

| Dependency | Purpose | Notes |
|---|---|---|

## Design Principles

- {{<<LLM: project-specific principles, e.g. local-first, idempotent, etc.>>}}
""", SCHEMA_VERSION)


def tpl_code_index_md(project_name: str) -> str:
    return embed_schema_version(f"""# Code Index \u2014 {project_name}

> Fully automatic. Rebuilt by `agent_ariadne.py annotate` every time it runs.
> Do not hand-edit \u2014 changes will be overwritten on the next annotate pass.

## Entry Points

| File | Role |
|---|---|

## Source Files by Directory

""", SCHEMA_VERSION)


def tpl_developer_log_md(project_name: str) -> str:
    return embed_schema_version(f"""# Developer Log \u2014 {project_name}

> Append only \u2014 never edit existing entries.

## Entry format

```
### [YYYY-MM-DD] \u2014 [Short description]
- **Model / Tool**: [model name, or "human", or "n/a"]
- **Task**: [what was worked on, task ID if applicable]
- **Status**: Success / Partial / In Progress / Failed
- **Files changed**: [list, or "none"]
- **Notes**: [observations, decisions, next steps \u2014 or omit]
```

## Log

### {today()} \u2014 Project initialized
- **Model / Tool**: n/a
- **Task**: n/a
- **Status**: Success
- **Files changed**: {", ".join(MANAGED_FILES)}
""", SCHEMA_VERSION)


def tpl_readme_md(project_name: str) -> str:
    return f"""# {project_name}

{{One-sentence description.}}

## What it does

{{2-3 sentences.}}

## Quick start

```bash
{{setup / run commands}}
```

## Status

See PROJECT_STATUS.md for current phase and progress.
"""


def tpl_instructions_md(project_name: str) -> str:
    return f"""# Instructions \u2014 {project_name}

## Requirements

{{list requirements}}

## Setup

{{exact setup commands}}

## Running it

{{exact run commands}}

## Common issues

{{issue -> fix}}
"""


TEMPLATE_BUILDERS = {
    "AGENTS.md": tpl_agents_md,
    "PROJECT_STATUS.md": tpl_project_status_md,
    "PROJECT_SCOPE.md": tpl_project_scope_md,
    "PROJECT_CONFIG.md": tpl_project_config_md,
    "ARCHITECTURE.md": tpl_architecture_md,
    "CODE_INDEX.md": tpl_code_index_md,
    "DEVELOPER_LOG.md": tpl_developer_log_md,
    "README.md": tpl_readme_md,
    "INSTRUCTIONS.md": tpl_instructions_md,
}


# ============================================================
#  INIT COMMAND
# ============================================================

def detect_project_name(cwd: Path) -> str:
    pkg = read_if_exists(cwd / "package.json")
    if pkg:
        try:
            name = json.loads(pkg).get("name")
            if name:
                return name
        except json.JSONDecodeError:
            pass
    pyproject = read_if_exists(cwd / "pyproject.toml")
    if pyproject:
        m = re.search(r'name\s*=\s*"([^"]+)"', pyproject)
        if m:
            return m.group(1)
    return cwd.resolve().name


def cmd_init(args: argparse.Namespace) -> int:
    cwd = Path(args.path).resolve()
    project_name = args.name or detect_project_name(cwd)

    written: list[str] = []
    skipped: list[str] = []

    for filename in MANAGED_FILES:
        target = cwd / filename
        if target.exists():
            skipped.append(filename)
            continue
        content = TEMPLATE_BUILDERS[filename](project_name)
        write_file(target, content)
        written.append(filename)

    print(f"Ariadne init \u2014 project: {project_name}")
    if written:
        print(f"Written: {', '.join(written)}")
    if skipped:
        print(f"Skipped (already exist): {', '.join(skipped)}")
    if not written:
        print("All managed files already exist. Nothing to do.")
    return 0


# ============================================================
#  CHECKSUM / HEADER HELPERS  (annotate command)
# ============================================================

def strip_header(content: str, comment_char: str) -> str:
    start_marker = f"{comment_char} {HEADER_START}"
    end_marker = f"{comment_char} {HEADER_END}"
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        return content
    after_end = content.find("\n", end_idx)
    return "" if after_end == -1 else content[after_end + 1:].lstrip("\n")


def compute_checksum(body: str) -> str:
    return hashlib.md5(body.encode("utf-8")).hexdigest()[:8]


def extract_existing_checksum(content: str, comment_char: str) -> str | None:
    m = re.search(rf"^{re.escape(comment_char)}\s*Checksum:\s*([0-9a-f]{{8}})\s*$",
                   content, re.MULTILINE)
    return m.group(1) if m else None


def build_header(comment_char: str, file_name: str, checksum: str, purpose_placeholder: bool) -> str:
    c = comment_char
    border = f"{c} " + "=" * (BORDER_WIDTH - 2)
    lines = [
        border,
        f"{c} {HEADER_START}",
        f"{c}",
        f"{c}  File:      {file_name}",
        f"{c}  Last Edit: {today()}",
        f"{c}  Checksum:  {checksum}",
        border,
        f"{c}",
    ]
    if purpose_placeholder:
        lines.append(f"{c}  <<LLM: 1-3 sentences \u2014 what this file does and its role in the project>>")
        lines.append(f"{c}")
    lines.append(f"{c} {HEADER_END}")
    lines.append("")
    return "\n".join(lines)


def annotate_source_file(path: Path, ext: str) -> tuple[bool, str]:
    """Returns (changed, message)."""
    comment_char = COMMENT_SYNTAX.get(ext)
    if not comment_char:
        return False, "no comment syntax for extension"

    content = read_if_exists(path)
    if content is None:
        return False, "could not read file"

    body = strip_header(content, comment_char)
    new_checksum = compute_checksum(body)
    old_checksum = extract_existing_checksum(content, comment_char)

    if old_checksum == new_checksum:
        return False, "unchanged"

    header = build_header(comment_char, path.name, new_checksum, purpose_placeholder=True)
    write_file(path, header + body)
    return True, "annotated"


def annotate_notebook(path: Path) -> tuple[bool, str]:
    """Inject/update an Ariadne header as the first cell of a .ipynb file.

    Uses only the stdlib json module -- notebooks are plain documented JSON,
    so no nbformat dependency is needed to stay stdlib-only.
    """
    raw = read_if_exists(path)
    if raw is None:
        return False, "could not read file"
    try:
        nb = json.loads(raw)
    except json.JSONDecodeError:
        return False, "invalid notebook JSON, skipped"

    cells = nb.get("cells", [])
    is_header_cell = (
        cells
        and cells[0].get("cell_type") == "markdown"
        and any(HEADER_START in "".join(cells[0].get("source", [])) for _ in [0])
    )

    # Compute checksum over every non-header cell, serialized deterministically.
    body_cells = cells[1:] if is_header_cell else cells
    body_repr = json.dumps(body_cells, sort_keys=True)
    new_checksum = compute_checksum(body_repr)

    old_checksum = None
    if is_header_cell:
        existing_src = "".join(cells[0].get("source", []))
        m = re.search(r"Checksum\*{0,2}:\s*([0-9a-f]{8})", existing_src)
        old_checksum = m.group(1) if m else None

    if old_checksum == new_checksum:
        return False, "unchanged"

    header_lines = [
        f"### {HEADER_START}",
        "",
        f"- **File**: {path.name}",
        f"- **Last Edit**: {today()}",
        f"- **Checksum**: {new_checksum}",
        "",
        "<<LLM: 1-3 sentences -- what this notebook does and its role in the project>>",
        "",
        f"### {HEADER_END}",
    ]
    header_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in header_lines],
    }

    nb["cells"] = [header_cell] + body_cells
    write_file(path, json.dumps(nb, indent=1))
    return True, "annotated"


def enumerate_source_files(root: Path) -> list[Path]:
    results: list[Path] = []

    def walk(current: Path) -> None:
        try:
            entries = sorted(current.iterdir())
        except (FileNotFoundError, PermissionError):
            return
        for entry in entries:
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_dir():
                if name in SKIP_DIRS:
                    continue
                walk(entry)
            else:
                if name in SKIP_FILES:
                    continue
                ext = entry.suffix
                if ext in SKIP_EXTENSIONS:
                    continue
                if ext not in COMMENT_SYNTAX and ext not in NOTEBOOK_EXTENSIONS:
                    continue
                results.append(entry)

    walk(root)
    return results


def build_directory_tree(root: Path) -> str:
    lines = [f"{root.name}/"]

    def walk(current: Path, prefix: str, depth: int) -> None:
        if depth > 3:
            return
        try:
            entries = sorted(
                e for e in current.iterdir()
                if not e.name.startswith(".") and e.name not in SKIP_DIRS
            )
        except (FileNotFoundError, PermissionError):
            return
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            child_prefix = "    " if is_last else "\u2502   "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                walk(entry, prefix + child_prefix, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    walk(root, "", 0)
    return "\n".join(lines)


def build_code_index_entries(files: list[Path], root: Path) -> str:
    """Deterministic skeleton -- purpose text is left as an LLM placeholder
    since describing *what a file does* requires reading and judgment, not
    just its path. This keeps the index itself fully automatic while being
    honest that per-file descriptions still need a fill-in pass.
    """
    by_dir: dict[str, list[Path]] = {}
    for f in files:
        rel = f.relative_to(root)
        d = str(rel.parent) if rel.parent != Path(".") else "(root)"
        by_dir.setdefault(d, []).append(rel)

    lines = []
    for d in sorted(by_dir):
        lines.append(f"### {d}\n")
        lines.append("| File | Purpose |")
        lines.append("|---|---|")
        for rel in sorted(by_dir[d]):
            lines.append(f"| `{rel}` | <<LLM: one-line description>> |")
        lines.append("")
    return "\n".join(lines)


# ============================================================
#  ANNOTATE COMMAND
# ============================================================

def cmd_annotate(args: argparse.Namespace) -> int:
    cwd = Path(args.path).resolve()
    target_dir = Path(args.target).resolve() if args.target else cwd

    files = enumerate_source_files(target_dir)
    if not files:
        print("No annotatable source files found.")
        return 0

    annotated: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []

    for f in files:
        ext = f.suffix
        if ext in NOTEBOOK_EXTENSIONS:
            changed, msg = annotate_notebook(f)
        else:
            changed, msg = annotate_source_file(f, ext)

        rel = str(f.relative_to(cwd)) if f.is_relative_to(cwd) else str(f)
        if msg == "unchanged":
            unchanged.append(rel)
        elif changed:
            annotated.append(rel)
        else:
            skipped.append(f"{rel} ({msg})")

    # Rebuild CODE_INDEX.md -- fully automatic.
    index_path = cwd / "CODE_INDEX.md"
    project_name = detect_project_name(cwd)
    entries_section = build_code_index_entries(files, cwd)
    entry_points_note = "| (detect and list manually, or via /init planning conversation) | - |"
    code_index_content = embed_schema_version(f"""# Code Index \u2014 {project_name}

> Fully automatic. Rebuilt by `agent_ariadne.py annotate` every time it runs.
> Do not hand-edit \u2014 changes will be overwritten on the next annotate pass.

## Entry Points

| File | Role |
|---|---|
{entry_points_note}

## Source Files by Directory

{entries_section}""", SCHEMA_VERSION)
    write_file(index_path, code_index_content)

    print(f"Annotated: {len(annotated)}   Unchanged: {len(unchanged)}   Skipped: {len(skipped)}")
    if annotated:
        print("Changed files (need <<LLM:>> placeholders filled in):")
        for r in annotated:
            print(f"  - {r}")
    if skipped:
        print("Skipped:")
        for r in skipped:
            print(f"  - {r}")
    print("CODE_INDEX.md rebuilt.")
    print()
    print("NOTE: directory-structure changes should also trigger an ARCHITECTURE.md")
    print("regeneration -- that step is agent-driven (diagram/interface prose), not")
    print("yet wired into this command. See PROJECT_AGENT_SPEC.md section 7.")
    return 0


# ============================================================
#  STATUS COMMAND
# ============================================================

TASK_HEADER_RE = re.compile(
    r"^\*\*(P\d+_T\d+): (.+?)\*\*\s*\(([^)]*)\)\s*(?:\u2014|--)?\s*(.*)$"
)
CHECKLIST_ITEM_RE = re.compile(r"^\s*-\s\[([ xO])\]\s(.+)$")


def parse_project_status(content: str) -> dict:
    """Parse tasks and their checklists out of PROJECT_STATUS.md.

    Deliberately tolerant: a task is any line matching
    "**P<n>_T<n>: name** (metadata) -- status", followed by checklist lines
    until the next task header or section header.
    """
    tasks = []
    current = None
    for line in content.split("\n"):
        m = TASK_HEADER_RE.match(line.strip())
        if m:
            if current:
                tasks.append(current)
            task_id, name, meta, status = m.groups()
            current = {
                "id": task_id, "name": name, "meta": meta,
                "status": status.strip(), "checklist": [],
            }
            continue
        if current is not None:
            cm = CHECKLIST_ITEM_RE.match(line)
            if cm:
                marker, text = cm.groups()
                current["checklist"].append({"marker": marker, "text": text})
            elif line.startswith("#"):
                tasks.append(current)
                current = None
    if current:
        tasks.append(current)
    return {"tasks": tasks}


def cmd_status(args: argparse.Namespace) -> int:
    cwd = Path(args.path).resolve()
    status_path = cwd / "PROJECT_STATUS.md"
    content = read_if_exists(status_path)
    if content is None:
        print("PROJECT_STATUS.md not found. Run `agent_ariadne.py init` first.")
        return 1

    parsed = parse_project_status(content)
    tasks = parsed["tasks"]

    if not tasks:
        print("No tasks found in PROJECT_STATUS.md yet.")
        return 0

    print(f"{'ID':<10} {'Status':<14} {'Progress':<10} Name")
    print("-" * 70)
    for t in tasks:
        total = len(t["checklist"])
        done = sum(1 for c in t["checklist"] if c["marker"] == "x")
        deferred = sum(1 for c in t["checklist"] if c["marker"] == "O")
        progress = f"{done}/{total}" if total else "-"
        flag = f" ({deferred} deferred)" if deferred else ""
        print(f"{t['id']:<10} {t['status']:<14} {progress:<10} {t['name']}{flag}")

    return 0


# ============================================================
#  CONFIG COMMAND
# ============================================================

SETTINGS_RE = re.compile(r"^-\s*([a-z_]+):\s*(.+)$")


def parse_project_config(content: str) -> dict[str, str]:
    settings: dict[str, str] = {}
    in_settings = False
    for line in content.split("\n"):
        if line.strip() == "## Settings":
            in_settings = True
            continue
        if in_settings and line.startswith("## "):
            break
        if in_settings:
            m = SETTINGS_RE.match(line.strip())
            if m:
                settings[m.group(1)] = m.group(2).strip()
    return settings


def cmd_config(args: argparse.Namespace) -> int:
    cwd = Path(args.path).resolve()
    config_path = cwd / "PROJECT_CONFIG.md"
    content = read_if_exists(config_path)
    if content is None:
        print("PROJECT_CONFIG.md not found. Run `agent_ariadne.py init` first.")
        return 1

    settings = parse_project_config(content)

    if args.action == "get":
        if args.key:
            print(settings.get(args.key, f"(not set: {args.key})"))
        else:
            for k, v in settings.items():
                print(f"{k}: {v}")
        return 0

    if args.action == "set":
        if not args.key or args.value is None:
            print("Usage: agent_ariadne.py config set <key> <value>")
            return 1
        pattern = re.compile(rf"^-\s*{re.escape(args.key)}:\s*.+$", re.MULTILINE)
        replacement = f"- {args.key}: {args.value}"
        if pattern.search(content):
            new_content = pattern.sub(replacement, content, count=1)
        else:
            # Append the new setting to the end of the Settings section.
            new_content = content.replace(
                "## Settings\n", f"## Settings\n\n{replacement}", 1
            )
        write_file(config_path, new_content)
        print(f"Set {args.key} = {args.value}")
        return 0

    print(f"Unknown config action: {args.action}")
    return 1


# ============================================================
#  VALIDATE COMMAND
# ============================================================

def validate_project_status(content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for i, line in enumerate(content.split("\n"), start=1):
        stripped = line.strip()
        if re.match(r"^-\s\[[^ xO]\]", stripped):
            errors.append(
                f"line {i}: checklist item uses an invalid marker "
                f"(expected [ ], [x], or [O]): {stripped[:60]}"
            )

    parsed = parse_project_status(content)
    for t in parsed["tasks"]:
        if "Effort" not in t["meta"] and "Speed" not in t["meta"] and (
            "effort" not in t["meta"].lower() and "speed" not in t["meta"].lower()
        ):
            warnings.append(f"Task {t['id']}: no Effort/Speed metadata found")

    return errors, warnings


def validate_project_config(content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    settings = parse_project_config(content)
    required = {"scope_enforcement", "spec_depth", "branching_strategy"}
    for key in required:
        if key not in settings:
            warnings.append(f"missing setting: {key}")

    if settings.get("scope_enforcement") not in (None, "strict", "soft"):
        errors.append(
            f"scope_enforcement has invalid value '{settings['scope_enforcement']}' "
            "(expected 'strict' or 'soft')"
        )
    if settings.get("spec_depth") not in (None, "minimal", "standard", "thorough"):
        errors.append(
            f"spec_depth has invalid value '{settings['spec_depth']}' "
            "(expected 'minimal', 'standard', or 'thorough')"
        )

    return errors, warnings


def cmd_validate(args: argparse.Namespace) -> int:
    cwd = Path(args.path).resolve()
    total_errors = 0
    total_warnings = 0

    print("agent_ariadne.py validate")
    print("\u2501" * 50)
    print(f"Validation Report \u2014 {today()}")
    print("\u2501" * 50)
    print()

    checks = {
        "PROJECT_STATUS.md": validate_project_status,
        "PROJECT_CONFIG.md": validate_project_config,
    }

    for filename, validator in checks.items():
        path = cwd / filename
        content = read_if_exists(path)
        print(filename)
        if content is None:
            print(f"  \u2717 file not found")
            total_errors += 1
            print()
            continue

        errors, warnings = validator(content)
        schema = read_schema_version(content)
        if filename in VERSIONED_FILES and schema is None:
            warnings.append("no schema version tag found")

        if not errors and not warnings:
            print("  \u2713 well-formed")
        for e in errors:
            print(f"  \u2717 {e}")
        for w in warnings:
            print(f"  \u26a0 {w}")
        total_errors += len(errors)
        total_warnings += len(warnings)
        print()

    print("\u2501" * 50)
    print(f"{total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


# ============================================================
#  ARGUMENT PARSING
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent_ariadne.py",
        description="Deterministic project-governance CLI for Ariadne.",
    )
    parser.add_argument(
        "--path", default=".", help="Project root (default: current directory)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Scaffold all Ariadne-managed files")
    p_init.add_argument("--name", help="Project name (auto-detected if omitted)")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="Render phase/milestone/task status")
    p_status.set_defaults(func=cmd_status)

    p_validate = sub.add_parser("validate", help="Check well-formedness of managed files")
    p_validate.set_defaults(func=cmd_validate)

    p_annotate = sub.add_parser("annotate", help="Inject/update headers, rebuild CODE_INDEX.md")
    p_annotate.add_argument("--target", help="Subdirectory to annotate (default: whole project)")
    p_annotate.set_defaults(func=cmd_annotate)

    p_config = sub.add_parser("config", help="Get/set PROJECT_CONFIG.md settings")
    p_config.add_argument("action", choices=["get", "set"])
    p_config.add_argument("key", nargs="?")
    p_config.add_argument("value", nargs="?")
    p_config.set_defaults(func=cmd_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())