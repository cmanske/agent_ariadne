# Project Scope - Ariadne
<!-- schema: v1 -->

> Defines project boundaries, the feature registry, and every task's spec
> sheet. The agent checks this file before implementing any feature and
> before removing any existing one. Never delete entries, move them
> between sections instead.

## Scope definition

### Purpose
A deterministic, agent-agnostic project-governance CLI that keeps ad-hoc
coding-agent projects from drifting: enforced scope, gated spec sheets,
tiered validation, and an automatically maintained code index and file
headers.

### Inclusion criteria
- A single stdlib-only Python CLI as the deterministic core
- All project state in plain, human-readable ALL-CAPS markdown files
- Support for Pi, Claude Code, Codex, and OpenCode via thin per-agent
  adapters, plus a universal AGENTS.md layer that works everywhere
- Tiered, per-language validation (real test suite, self-check, or
  human-only, depending on what's actually available for the language)
- Self-contained checksums (in each file's own header) instead of an
  external state/manifest file

### Exclusion criteria
- No GUI, no web service, no cloud dependency
- No JSON state files of any kind for project state (config, status, scope)
- No automatic update mechanism for vendored copies - updates are always a
  deliberate re-install
- No interactive prompting inside the CLI itself - all human interaction is
  the calling agent's responsibility
- Not a replacement for git; it suggests commit messages, it never commits
  automatically

### Key constraints
- Python 3.12+, standard library only, zero third-party dependencies
- Must run identically whether invoked by a human or by an agent's hook
  system

## Feature registry

### Approved Features
- Task subcommand group (start/advance/complete) - Target: Phase 2
- Spec sheet gating tied to scope_enforcement - Target: Phase 2
- Git commit-message suggestion on task completion - Target: Phase 2
- Deferred checklist item auto-tasking - Target: Phase 2
- ARCHITECTURE.md auto-regeneration trigger - Target: Phase 2
- install.sh with per-agent detection - Target: Phase 3
- Pi / Claude Code / Codex / OpenCode adapters - Target: Phase 3

### Implemented Features
- File scaffolding (`init`) for all 9 managed files, skip-if-exists
- Annotation pipeline: comment-syntax header injection, self-contained
  checksums, notebook (.ipynb) support via stdlib json
- CODE_INDEX.md automatic rebuild
- `validate` command: PROJECT_STATUS.md and PROJECT_CONFIG.md well-formedness
  checks, error/warning distinction, non-zero exit on error
- `validate` command: double-brace scaffolding-placeholder template-residue
  detection across all 9 managed markdown files (Phase 1 follow-up,
  P1_T6) -- cross-cutting check layered on top of file-specific
  validators; the foundation for P2_T2's spec-sheet gating
- `status` command: task/checklist parsing and progress summary
- `config` get/set for PROJECT_CONFIG.md settings

### Planned Features
> All Approved Features above are currently Planned.

### Removed Features
> None yet.

### Rejected Features
- A separate SPEC_SHEETS.md file - merged into PROJECT_SCOPE.md instead
- A separate PATTERNS.md file for learned preferences - folded into
  AGENTS.md's Learned Patterns section instead
- An automatic `update` command for vendored copies - rejected in favor of
  deliberate manual re-install, to avoid silently changing an in-flight
  project's behavior
- Global CLI installation (pipx, etc.) - rejected in favor of a vendored,
  per-project, dependency-free copy

### Future Considerations
- A real pytest suite for agent_ariadne.py itself
- A `--json` output mode, if an agent adapter ever genuinely needs
  structured parsing beyond plain text (not needed as of Phase 1)

## Task Spec Sheets

> Organized by phase and task. Depth follows PROJECT_CONFIG.md's spec_depth
> setting unless the agent proposes a different depth for a specific task
> (subject to scope_enforcement).

### Phase 1 follow-up

#### P1_T6: Managed-file template-residue validation

**Goal**
Add a deterministic check to the `validate` command that reports any
remaining double-brace template placeholder in the managed markdown
files, so that a file the human/agent forgot to fill in is caught
automatically rather than shipping with unfilled template prose still in
it. This is the minimal foundation for P2_T2's spec-sheet gating; the
full scope-enforcement behavior stays in P2_T2.

**Inputs / dependencies needed**
- The existing `validate` command and its per-file validator dispatch
  in `cmd_validate`.
- The list of managed markdown files (`MANAGED_FILES`).
- No new external dependencies; stdlib `re` only.

**Steps**
1. Add a validator `validate_template_residue(content)` that scans
   line-by-line for `\{\{.*?\}\}` (no `re.DOTALL`, single-line matches
   only) and returns one error per occurrence, each naming the
   one-based line number and a truncated (<=60 char) excerpt of the
   matched text, with wording "replace this ... placeholder with real
   prose before continuing".
2. Dispatch it as a cross-cutting layer over every file in
   `MANAGED_FILES` (all 9, including README.md and INSTRUCTIONS.md), in
   addition to -- not instead of -- any file-specific validator
   (STATUS markers, CONFIG enum values).
3. Severity is error (non-zero exit), not warning, because residual
   template prose is a definite "this file is not finished" signal,
   not a soft preference; this same output is what P2_T2's
   clarifying -> in_progress gate will consume.
4. The detection scope is the double-brace markdown convention only.
   It must NOT flag a bare `<<LLM:...>>` token, because those belong
   to source-file annotation headers (a different workflow).
5. Drop the dangling `See PROJECT_AGENT_SPEC.md section 7.` sentence
   from `cmd_annotate`'s stdout note (the referenced file does not
   exist in this repo); keep the rest of the note.
6. Fill the single outstanding `<<LLM:...>>` placeholder in
   agent_ariadne.py's annotation header with a one-line purpose
   describing the file. (Last step in the changeset -- any earlier
   `annotate` run would re-inject the placeholder and clobber it; the
   annotate-should-preserve-filled-purpose issue is a known Phase 2
   limitation, out of scope here.)

**Data formats / schemas**
- No file format changes. A new validator function returning
  `(errors, warnings)` tuples like the existing two; the `checks` dict
  in `cmd_validate` now maps filename to a list of validators
  (file-specific plus residue), whose results are merged in order.

**Edge cases & failure handling**
- Multi-line scaffold placeholders: the non-greedy single-line regex
  misses them. This is intentional -- the init templates emit only
  single-line placeholders, so multi-line residue cannot arise from
  the tool's own templates. Simplicity beats edge-case coverage that
  cannot occur in practice.
- Prose that names the double-brace convention by its glyph form will
  itself match the regex. The managed markdown files therefore refer to
  the convention by description ("double-brace placeholder",
  "double-brace scaffold form") rather than writing the literal
  two-braces-text-two-braces glyph into prose unfenced. The glyph form
  is reserved for agent_ariadne.py's init templates (a source file,
  not subject to the residue check) and never appears in managed
  markdown prose.
- A literal double-brace pair in real prose that is not a placeholder:
extremely unlikely in these markdown files and trivial to edit out.
  Will not add escaping complexity to handle it.
- File-specific and residue validators both failing on the same file:
  errors from both surface in order (file-specific first), no
  deduplication needed because their concerns are disjoint.

**Acceptance criteria (EARS format)**
- The system shall report an error for each line in a managed markdown
  file that matches the double-brace scaffold-placeholder pattern
  (two opening braces, content, two closing braces, all on one line),
  when `validate` is run.
- The system shall print, for each occurrence, the filename (via the
  existing per-file heading), the one-based line number, and a
  truncated excerpt of the matched text.
- The system shall exit non-zero when at least one such placeholder is
  present in any managed markdown file.
- The system shall not flag any `<<LLM:...>>` token that is not also
  enclosed in the double-brace scaffold form, because such tokens
  belong to source-file annotation headers, not managed markdown
  scaffolding.
- The system shall run the template-residue check on every file in
  `MANAGED_FILES` regardless of whether that file also has a
  file-specific validator.
- The system shall leave all managed files unchanged when `validate`
  is run (validate is read-only by design).
- When `cmd_annotate` runs, the system shall not print any reference to
  `PROJECT_AGENT_SPEC.md` (that file does not exist in this repo).

**Constraints / notes**
- Detection is scoped to the double-brace markdown convention only.
  The single-brace `<<LLM:...>>` annotation convention in source files
  is handled by the annotation workflow, not this check.
- This is a Phase 1 follow-up, not P2_T2. P2_T2 keeps the full
  scope_enforcement-gated clarifying -> in_progress transition logic;
  P1_T6 contributes only the underlying residue detection that P2_T2
  will later wire into its gate. The deferred checkbox on P1_T6 in
  PROJECT_STATUS.md records this boundary explicitly.
- Non-interactive by design: the actionable message wording
  ("...before continuing") tells the calling agent what to fix, but
  the CLI itself never prompts or waits.

### Phase 2

#### P2_T1: Task state commands

**Goal**
Add a `task` subcommand group to agent_ariadne.py that moves a task through
its lifecycle (not_started -> clarifying -> in_progress -> self_check ->
awaiting_human_review -> done), enforcing that transitions happen in order
and that `done` can only be reached after human confirmation.

**Inputs / dependencies needed**
- PROJECT_STATUS.md's existing task-parsing logic (parse_project_status),
  already built in Phase 1 and reusable here
- No new external dependencies

**Steps**
1. Extend PROJECT_STATUS.md's task header format to carry an explicit state
   field (not just the current free-text status column)
2. Add `task start <id>`: fails if the task isn't `not_started`; on success,
   writes the spec sheet scaffold into PROJECT_SCOPE.md if it doesn't exist
   yet, and sets state to `clarifying`
3. Add `task advance <id> --to <state>`: validates the transition is legal
   (no skipping states) and rejects the jump to `done` outright, since only
   `task complete` can reach it
4. Add `task complete <id>`: requires state to already be
   `awaiting_human_review` and a `--confirmed` flag (the agent only passes
   this after the human has explicitly signed off); refuses otherwise
5. Wire `scope_enforcement` (strict/soft) into the `clarifying -> in_progress`
   transition: strict blocks if the spec sheet still has unresolved
   `<<LLM:>>` placeholders, soft only warns

**Data formats / schemas**
- Task state stored as plain text in the existing
  `**P1_T1: Name** (Effort, Speed) - Status` header line in PROJECT_STATUS.md
  - no new file, no JSON

**Edge cases & failure handling**
- Attempting to advance a task that doesn't exist: clear error, non-zero
  exit code, no file changes
- Attempting to skip a state (e.g. not_started straight to done): rejected
  with a message naming the required intermediate states
- Concurrent edits (two agents/processes touching the same task): out of
  scope for Phase 2 - single-agent-at-a-time is the assumed usage pattern

**Acceptance criteria (EARS format)**
- The system shall reject a `task complete` call when the task's state is
  not `awaiting_human_review`.
- The system shall reject a `task advance` call that would skip an
  intermediate state.
- The system shall block the `clarifying -> in_progress` transition when
  `scope_enforcement` is `strict` and the spec sheet contains an unresolved
  `<<LLM:>>` placeholder.
- If `scope_enforcement` is `soft`, then the system shall print a warning
  but still allow the `clarifying -> in_progress` transition.
- The system shall leave PROJECT_STATUS.md unchanged when any transition is
  rejected.

**Constraints / notes**
- Keep the CLI's non-interactive design intact: these commands read state,
  validate, and write - they never prompt. The confirmation step is a flag
  the calling agent passes in, not something the CLI asks for itself.
