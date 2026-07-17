# Developer Log — Ariadne
<!-- schema: v1 -->

> Append only — never edit existing entries.

## Entry format

```
### [YYYY-MM-DD] — [Short description]
- **Model / Tool**: [model name, or "human", or "n/a"]
- **Task**: [what was worked on, task ID if applicable]
- **Status**: Success / Partial / In Progress / Failed
- **Files changed**: [list, or "none"]
- **Notes**: [observations, decisions, next steps — or omit]
```

## Log

### 2026-07-15 — Project initialized
- **Model / Tool**: n/a
- **Task**: n/a
- **Status**: Success
- **Files changed**: AGENTS.md, PROJECT_STATUS.md, PROJECT_SCOPE.md, PROJECT_CONFIG.md, ARCHITECTURE.md, CODE_INDEX.md, DEVELOPER_LOG.md, README.md, INSTRUCTIONS.md

### 2026-07-15 — Full design + Phase 1 build
- **Model / Tool**: Claude (Sonnet 4.6, web)
- **Task**: End-to-end design of Ariadne through extensive clarification, then Phase 1 build (init, annotate, validate, status, config)
- **Status**: Success
- **Files changed**: agent_ariadne.py, README.md, PROJECT_STATUS.md, PROJECT_SCOPE.md, PROJECT_CONFIG.md, AGENTS.md, CODE_INDEX.md
- **Notes**: Manual end-to-end testing during the build caught two idempotency
  bugs before shipping: (1) the header start/end marker written by
  build_header didn't match the marker strip_header searched for (spacing
  mismatch), so annotation never converged; (2) the notebook checksum
  extraction regex didn't account for the markdown bold syntax
  (**Checksum**:) actually written into the header cell. Both fixed and
  re-verified. Repo was then dogfooded on itself (this file, PROJECT_STATUS.md,
  PROJECT_SCOPE.md, and agent_ariadne.py's own header were all produced by
  running Ariadne's own commands against its own repo). Next session should
  start on P2_T1 (task state commands) — see PROJECT_STATUS.md's Last
  session summary and Next action.

### 2026-07-15 — Filled in ARCHITECTURE.md and INSTRUCTIONS.md
- **Model / Tool**: Claude (Sonnet 4.6, web, via Pi)
- **Task**: Replace the last unfilled template placeholders in the two remaining managed files (ARCHITECTURE.md System Overview + Design Principles; INSTRUCTIONS.md setup/usage). No task ID — not a Phase 2 task, just template cleanup.
- **Status**: Success
- **Files changed**: ARCHITECTURE.md, INSTRUCTIONS.md
- **Notes**: Root cause (clarified with the human after the fact): the
  Phase 1 build was an interrupted dogfooding run of `init` against this
  repo that hit token limits before it finished; the init entry above was
  written optimistically as if all 9 files had landed, when in fact only the
  first 7 did. So both ARCHITECTURE.md and INSTRUCTIONS.md were genuinely
  missing from disk — not a lost handoff, an interrupted run. Re-running
  init now would have skipped everything (the other 7 files are real and
  customized), so these two were created from scratch instead, with
  content grounded in the actual agent_ariadne.py source rather than the
  template stubs. ARCHITECTURE.md:
  System Overview (single stdlib-only CLI, markdown-as-state, no JSON/no
  manifest, checksums-live-in-headers, agent-driven workflow), a real
  directory tree for the current repo, filled Module Responsibilities and
  External Dependencies tables, and six Design Principles drawn from the
  code's actual behavior. INSTRUCTIONS.md: requirements with the 3.11
  cave (Path.is_relative_to), both install paths, documented all five
  Phase 1 commands with their real flags, what-it-manages table,
  task-lifecycle note, and six common-issue entries. Ran
  `python3 agent_ariadne.py validate` after — 0 errors, 0 warnings, both
  PROJECT_STATUS.md and PROJECT_CONFIG.md well-formed. Note that validate
  only checks STATUS and CONFIG by design, so it does not itself verify the
  prose in the two files just written.

### [2026-07-16] — P1_T6: managed-file template-residue validation
- **Model / Tool**: Claude (Sonnet 4.6, web, via Pi)
- **Task**: P1_T6 — add double-brace scaffolding-placeholder template-residue detection to `validate` across all 9 managed markdown files; drop the dangling `PROJECT_AGENT_SPEC.md` reference from the `annotate` stdout note; fill the standing annotation placeholder in agent_ariadne.py's own header. Phase 1 follow-up, the minimal foundation for P2_T2's spec-sheet gating.
- **Status**: Success
- **Files changed**: agent_ariadne.py, PROJECT_STATUS.md, PROJECT_SCOPE.md, DEVELOPER_LOG.md
- **Notes**: Added `validate_template_residue()` (line-by-line scan for the
  double-brace scaffold-placeholder pattern, no re.DOTALL so only
  single-line matches fire — every placeholder the init templates
  actually emit is on one line), wired into `cmd_validate` as a
  cross-cutting layer that runs on top of file-specific validators rather
  than replacing them. Severity is error -> non-zero exit; per-hit
  message is actionable ("replace this placeholder with real prose
  before continuing") so the calling agent knows what to fix without the
  CLI prompting. Detection scope is the double-brace markdown convention
  only; bare `<<LLM:>>` (the source-file annotation convention) is
  deliberately not flagged. Empirically verified with a scratch repo
  seeded with two scaffold-placeholder lines and one bare `<<LLM:>>`
  line: both scaffold forms flagged on the right line numbers, the
  annotation line correctly ignored, exit 1. Clean repo: 0 errors across
  all 9 managed files. Also dropped the `See PROJECT_AGENT_SPEC.md
  section 7.` sentence from the annotate note (that file does not exist
  in this repo — the reference survived from the earlier design doc that
  never made it into the managed file set). Last step: hand-filled
  agent_ariadne.py's own header `<<LLM:>>` with a real one-line purpose.
  Note on annotate + filled purpose lines: the filled-in text sits inside
  the header region (between the start/end markers), which strip_header
  excludes from the checksum, so a no-op annotate run leaves the filled
  purpose intact ("Annotated: 0, Unchanged: 1" confirmed). The genuine
  clobber risk is narrower than the earlier note implied: annotate rewrites
  the header only when the *body* checksum changes, and on such a rewrite
  it currently re-emits a fresh bare `<<LLM:...>>` placeholder rather than
  preserving any previously-written purpose text. Preserving a filled
  purpose across a body-change rewrite is the actual Phase 2 annotation
  concern, out of scope for P1_T6, recorded here for accuracy. Full
  EARS-format spec sheet added under PROJECT_SCOPE.md "Phase 1
  follow-up"; task entry added to PROJECT_STATUS.md Phase 1 section
  marked Complete with one deferred item (the clarifying -> in_progress
  gate, owned by P2_T2); feature
  registered in PROJECT_SCOPE.md Implemented Features.

### [2026-07-16] — Codify the no-double-brace-in-managed-markdown convention
- **Model / Tool**: Claude (Sonnet 4.6, web, via Pi)
- **Task**: Follow-on to P1_T6 — make the writing convention that the
  template-residue check forces into the project explicit and discoverable,
  rather than implicit and learnable only by getting validate errors.
- **Status**: Success
- **Files changed**: AGENTS.md, INSTRUCTIONS.md
- **Notes**: When P1_T6's check was first turned on it flagged 12 lines
  across PROJECT_STATUS.md, PROJECT_SCOPE.md, and DEVELOPER_LOG.md, all
  of them prose I had just written that *described* the double-brace
  placeholder convention by writing its literal glyph form. The check is
  correct to flag those — it matches the character pattern alone and
  cannot tell residue apart from prose. Resolved line-by-line by referring
  to the convention by name ("double-brace placeholder", "double curly
  brackets", "the scaffold form") instead of the glyph. That fix encodes a
  real writing rule the project did not formally have before: managed
  markdown files may never contain the literal two-braces / two-braces
  sequence in prose. Human confirmed 2026-07-16 to codify it and
  explicitly sanctioned the "double-brace placeholder" / "double curly
  brackets" naming. Added a Learned Patterns entry to AGENTS.md recording
  the rule and its rationale (the only place earlier entries can be
  edited/corrected, so appropriate for a convention that may itself be
  refined over time); added a Common-issues bullet to INSTRUCTIONS.md so
  someone who hits the error has the workaround next to where they'd look.
  Dogfooded the rule on its own writeup: the first draft of the AGENTS.md
  entry contained the glyph five times while explaining the convention,
  validate caught it, rewritten to name-only. Final validate: 0 errors
  across all 9 managed files. No code changes this entry — pure project-
  documentation work.
