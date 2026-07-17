# Project Status - Ariadne
<!-- schema: v1 -->

> Tracks current state, decisions, and session history.
> Task IDs: P1_T3 (zero-padded to P01_T03 once phase or task count hits 10+).
> Checklist markers: [ ] not started, [x] complete, [O] deferred (moved to
> another task, see the inline note for which one and why).

## Project summary

- **Name**: Ariadne
- **Purpose**: A deterministic project-governance CLI for AI coding agents.
  Tracks phases/milestones/tasks, enforces scope, scaffolds and gates spec
  sheets, validates task completion, and keeps source-file headers and a
  code index in sync automatically. Agent-agnostic by design.
- **Stack**: Python 3.12+, standard library only, no third-party dependencies
- **Entry point**: `agent_ariadne.py` (vendored into `.ariadne/` once Phase 3's
  install.sh exists; lives at repo root during development)
- **Running it**: `python3 agent_ariadne.py <command>`

## Current phase

- **Phase**: 2 - Task Lifecycle & Git Integration
- **Status**: Not Started
- **Active branch**: main

## Roadmap

| Phase | Name | Status |
|---|---|---|
| 1 | Core Engine | Done |
| 2 | Task Lifecycle & Git Integration | Not Started |
| 3 | Distribution & Per-Agent Adapters | Not Started |

## Milestones

| Milestone | Phase | Tasks | Definition of Done |
|---|---|---|---|
| M1: Core Engine | 1 | P1_T1-P1_T5 | init/status/validate/annotate/config all working, tested end to end |
| M2: Task Lifecycle | 2 | P2_T1, P2_T2 | Task state transitions and spec-sheet gating enforced by the CLI |
| M3: Git Integration | 2 | P2_T3, P2_T4 | Commit-message suggestion and deferred-item auto-tasking working |
| M4: Distribution | 3 | P3_T1-P3_T5 | install.sh detects agents and wires adapters correctly for each |

### Phase 1: Core Engine

**P1_T1: File scaffolding & templates** (Effort: Easy, Speed: Fast) - Complete
- [x] Templates for all 9 managed files
- [x] `init` command, skips files that already exist
- [x] Project-name auto-detection (package.json, pyproject.toml, dir name)

**P1_T2: Annotation pipeline** (Effort: Hard, Speed: Slow) - Complete
- [x] Comment-syntax table across supported languages
- [x] Checksum stored inside each file's own header (no separate manifest)
- [x] Notebook (.ipynb) support via stdlib json, no nbformat dependency
- [x] CODE_INDEX.md rebuild, fully automatic
- [O] ARCHITECTURE.md auto-regeneration trigger on structural changes - deferred to P2_T5, reason: needs the diagram/interface-prose generation step designed, which depends on task-lifecycle self-check hooks being in place first

**P1_T3: Validate command** (Effort: Medium, Speed: Fast) - Complete
- [x] PROJECT_STATUS.md checklist marker validation
- [x] PROJECT_CONFIG.md settings validation
- [x] Error vs. warning distinction, non-zero exit code on error

**P1_T4: Status command** (Effort: Easy, Speed: Fast) - Complete
- [x] Parse tasks/checklists out of PROJECT_STATUS.md
- [x] Render progress summary with deferred-item flagging

**P1_T5: Config command** (Effort: Easy, Speed: Fast) - Complete
- [x] get/set for PROJECT_CONFIG.md settings
- [x] Appends new keys cleanly if not already present

**P1_T6: Managed-file template-residue validation** (Effort: Easy, Speed: Fast) - Complete
- [x] `validate` flags double-brace scaffolding-template placeholder residue across all 9 managed markdown files
- [x] Report per hit: filename, one-based line number, truncated excerpt, actionable "replace ... with real prose before continuing" wording
- [x] Severity: error -> non-zero exit
- [x] Detection scoped to double-brace markdown convention; does NOT flag bare `<<LLM:...>>` (source-file annotation convention)
- [x] Cross-cutting layer: runs on top of file-specific validators (STATUS markers, CONFIG enum values) without displacing them
- [x] Dropped dangling `See PROJECT_AGENT_SPEC.md section 7.` ref from `annotate` stdout note
- [x] Filled standing `<<LLM:>>` purpose placeholder in agent_ariadne.py's own header
[O] Wire residue check into clarifying -> in_progress gate - deferred to P2_T2, reason: full scope_enforcement-gated transition logic is P2_T2's scope; P1_T6 ships only the detection

### Phase 2: Task Lifecycle & Git Integration

**P2_T1: Task state commands** (Effort: Medium, Speed: Medium) - Not Started
- [ ] `task start <id>` - transitions not_started -> clarifying
- [ ] `task advance <id> --to <state>` - moves through in_progress/self_check/awaiting_human_review
- [ ] `task complete <id>` - only succeeds if state is awaiting_human_review and human has confirmed
- [ ] Enforce scope_enforcement (strict/soft) on the clarifying -> in_progress transition

**P2_T2: Spec sheet gating** (Effort: Hard, Speed: Slow) - Not Started
- [ ] Detect an empty/placeholder spec sheet vs. a filled one
- [ ] Block task start under scope_enforcement: strict until spec sheet has no remaining <<LLM:>> placeholders
- [ ] Support agent-proposed depth override (see PROJECT_SCOPE.md Constraints)

**P2_T3: Git commit-message suggestion** (Effort: Medium, Speed: Fast) - Not Started
- [ ] On `task complete`, generate "P01_T03: <task name> - <summary>" and print it
- [ ] CLI never runs git commit itself; only ever prints a suggestion for the agent to act on
- [ ] Branch-naming helper, gated by branching_strategy setting

**P2_T4: Deferred checklist item auto-tasking** (Effort: Medium, Speed: Fast) - Not Started
- [ ] Detect [O] markers written by the agent
- [ ] Auto-create a new task entry in the current phase for the deferred item
- [ ] Cross-reference the new task ID back into the original item's note

**P2_T5: ARCHITECTURE.md regeneration trigger** (Effort: Medium, Speed: Medium) - Not Started
- [ ] Detect directory-structure changes (new file/module vs. edit to existing file)
- [ ] Wire into the self_check step of the task lifecycle from P2_T1

### Phase 3: Distribution & Per-Agent Adapters

**P3_T1: install.sh** (Effort: Medium, Speed: Medium) - Not Started
- [ ] Detect which agent directories exist (.pi/, .claude/, .codex/, .opencode/)
- [ ] Vendor agent_ariadne.py into .ariadne/
- [ ] Always write/update AGENTS.md regardless of detected agents

**P3_T2: Pi adapter** (Effort: Medium, Speed: Fast) - Not Started
- [ ] .pi/extensions/ariadne.ts calling agent_ariadne.py at the right hook points
- [ ] Commands prefixed xtn_ariadne_*

**P3_T3: Claude Code adapter** (Effort: Medium, Speed: Fast) - Not Started
- [ ] .claude/settings.json hooks (PreToolUse, PostToolUse, SessionStart, Stop)
- [ ] Accompanying SKILL.md

**P3_T4: Codex adapter** (Effort: Medium, Speed: Fast) - Not Started
- [ ] .codex/config.toml hooks, same lifecycle points as Claude Code

**P3_T5: OpenCode adapter** (Effort: Medium, Speed: Medium) - Not Started
- [ ] .opencode/plugin/ariadne.ts using OpenCode's own event names

## Recent decisions

> Reverse chronological. Never edit existing entries.

- **2026-07-15** - ARCHITECTURE.md and INSTRUCTIONS.md were missing from
  the initial handoff despite being logged as created; Pi created both
  from scratch on 2026-07-15, grounded in the actual code.
- **2026-07-14** - No update command for vendored copies. Updating means
  deliberately re-running install.sh; an automatic update could silently
  change behavior mid-project, which is riskier than the friction of a
  conscious re-install.
- **2026-07-14** - CLI output to the agent is plain text, no --json mode.
  The agent parses it the same way it parses any other file or output.
- **2026-07-14** - Minimum Python version set to 3.12+, no need to support
  older installs.
- **2026-07-14** - Tool named Ariadne (over Mnemosyne/Janus/Mimir) - best
  balance of recognizability ("Ariadne's thread" is a common idiom) and fit
  to the system's most distinctive feature: scope/task navigation through
  complexity.
- **2026-07-14** - Checksum manifest eliminated entirely. Each file's
  checksum lives in its own header instead of a separate JSON state file,
  keeping the "no hidden state" principle intact.
- **2026-07-14** - PROJECT_CONFIG.md holds settings as plain key: value
  lines plus a validation-command cache table, not JSON.
- **2026-07-14** - PROJECT_SCOPE.md merges scope boundaries and per-task spec
  sheets into one file, organized by phase/task, rather than a separate
  SPEC_SHEETS.md.
- **2026-07-14** - Milestones are required, always contained within a single
  phase, and get their own section (Milestone, Phase, Tasks, Definition
  of Done) after the Roadmap.
- **2026-07-14** - Adopted EARS-format acceptance criteria in spec sheets and
  a Learned Patterns section folded into AGENTS.md (not a separate file),
  both inspired by comparable tools (GitHub Spec Kit's constitution/EARS
  approach, Cline's Memory Bank pattern).
- **2026-07-14** - Distribution is a public GitHub repo with install.sh
  supporting both a clone-then-inspect path (recommended) and a curl-pipe
  fast path.

## Open questions

> Move to Recent decisions when resolved.

- [ ] Final repo name (ariadne vs. agent-ariadne vs. ariadne-cli) not
  yet locked in.
- [ ] Exact wording/scope of the Codex and OpenCode adapters is a best-effort
  design based on current docs (checked 2026-07-14) - worth re-verifying
  against each platform's docs at Phase 3 build time in case anything shifted.

## Known issues / tech debt

- ARCHITECTURE.md auto-regeneration is not yet wired into annotate - the
  command prints a note about this every run as a reminder (see P2_T5).
- No automated test suite for agent_ariadne.py itself yet - Phase 1 was
  validated by manual end-to-end runs during the build session, which caught
  and fixed two idempotency bugs (header-marker spacing mismatch, notebook
  checksum-regex mismatch). Writing a real pytest suite is a good early
  Phase 2 task even though it isn't formally listed above.

## Last session summary

- **Date**: 2026-07-14
- **Done**: Full design of Ariadne finalized across many rounds of
  clarification. Phase 1 built and tested end to end: init, status, validate,
  annotate (including the notebook path), and config all working correctly.
  README written. Constitution and Learned Patterns sections added to
  AGENTS.md; EARS-format acceptance criteria added to the spec sheet
  template.
- **Left off at**: Phase 1 complete and dogfooded on its own repo (this
  file). Ready to start Phase 2.
- **Next action**: Build the task subcommand group (P2_T1), starting with
  task start and the scope_enforcement-gated transition into in_progress.
