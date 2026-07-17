# Agent Memory — Ariadne
<!-- schema: v1 -->

> Auto-loaded at session start. Keep accurate and concise.
> Update whenever project direction, structure, or state changes meaningfully.

## What this project is

Ariadne is a deterministic project-governance CLI for AI coding agents. It scaffolds and enforces a lightweight SDLC discipline (phases, milestones, tasks, gated spec sheets, tiered validation, and automatic source-file annotation) for people who don't have a strong SDLC background by default, like ad-hoc data scientists working alongside backend/frontend collaborators. It is agent-agnostic: a single stdlib-only Python CLI does all the deterministic work, with thin adapters per coding agent (Pi, Claude Code, Codex, OpenCode).

## Agent rules (Constitution)

> This section is the project's constitution — non-negotiable principles that
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
> Each entry is validated with the human before being added here — never
> record a pattern without confirming it first. Unlike DEVELOPER_LOG.md
> (chronological, append-only), this section reflects current understanding
> and can be edited or corrected as patterns are confirmed or refined.

- **Never write the literal double-brace glyph in managed markdown files.**
  The `init` templates emit double-brace scaffold placeholders for the
  agent/human to fill in — either a bare form (two opening braces, a
  word such as "placeholder", two closing braces) or a nested form (an
  LLM annotation token, itself angle-bracketed, wrapped in the
  double-brace pair). `validate` flags any surviving glyph as template
  residue. Because the check matches on the character pattern alone,
  writing the glyph *into prose to describe it* also trips it. So: when
  a managed markdown file needs to refer to the convention, name it in
  words — "double-brace placeholder", "double curly brackets", "the
  scaffold form" — never write the literal two-braces / two-braces
  sequence inline (an opening pair of braces, text, a closing pair of
  braces). The literal glyph is reserved for source files (for example
  agent_ariadne.py's init templates), which `validate` does not check.
  Confirmed 2026-07-16 alongside the P1_T6 follow-up that introduced
  the residue check.

- {pattern or preference, once confirmed}

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
| DEVELOPER_LOG.md | Append-only session log — what happened, not what was learned |
| README.md | GitHub-facing project description |
| INSTRUCTIONS.md | Setup and usage guide |
