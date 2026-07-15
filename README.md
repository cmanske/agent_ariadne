# Ariadne
 
A deterministic project-governance layer for AI coding agents — phases, tasks,
and spec sheets that keep an ad-hoc project from turning into a labyrinth.
 
Works the same way regardless of which coding agent you use (Pi, Claude Code,
Codex, OpenCode, and others via a universal `AGENTS.md` layer). All state
lives in plain, human-readable markdown files — no hidden JSON, no database.
 
## Why
 
Ad-hoc projects drift. Scope creeps in silently, tasks get marked "done"
without anyone checking, and six months later nobody remembers why a
decision was made. Ariadne enforces a lightweight discipline instead:
 
- Every task gets a spec sheet before code gets written, with clarifying questions asked up front rather than guessed at.
- Every task is validated (tiered by what's actually possible for the language — real tests where they exist, a basic run/parse check where they don't, human review where neither is possible) before it's marked done.
- Every source file gets a short, versioned header explaining what it does, kept in sync automatically via checksums — no separate manifest to drift out of date.
- Scope boundaries are explicit and enforced (strictly or loosely, your choice per project) instead of implicit and silently ignored.
## Status
 
**Phase 1 of 3 is built and tested.** Phase 1 covers the deterministic core:
scaffolding, annotation, validation, status reporting, and config. Phase 2
(task lifecycle commands, git integration) and Phase 3 (`install.sh` +
per-agent adapters for Pi / Claude Code / Codex / OpenCode) are next.
 
Until Phase 3 ships, install by copying `agent_ariadne.py` directly into
your project — see below.
 
## Install
 
**Recommended — clone and inspect before running anything:**
 
```bash
git clone --depth 1 https://github.com/<you>/ariadne.git .ariadne_setup
cp .ariadne_setup/agent_ariadne.py ./.ariadne/agent_ariadne.py
rm -rf .ariadne_setup
```
 
**Fast path** (also supported, once `install.sh` ships in Phase 3):
 
```bash
curl -fsSL https://raw.githubusercontent.com/<you>/ariadne/main/install.sh | bash
```
 
Either way, nothing stays dependent on this repo afterward — it's a one-time
copy into your project's `.ariadne/` directory, pinned to whatever version
you copied. Updating means deliberately re-running the install step again,
not an automatic pull — a project already in flight shouldn't have its
behavior change out from under it.
 
## Requirements
 
Python 3.12+. Standard library only — nothing to `pip install`.
 
## Usage
 
```bash
# Scaffold all managed files (skips any that already exist)
python3 .ariadne/agent_ariadne.py init --name MyProject
 
# See current phase/milestone/task status
python3 .ariadne/agent_ariadne.py status
 
# Check that all managed files are well-formed
python3 .ariadne/agent_ariadne.py validate
 
# Inject/update file headers, rebuild CODE_INDEX.md
python3 .ariadne/agent_ariadne.py annotate
 
# Get/set a project setting
python3 .ariadne/agent_ariadne.py config get scope_enforcement
python3 .ariadne/agent_ariadne.py config set scope_enforcement strict
```
 
Normally you won't type these yourself — your coding agent runs them for you
at the right points in the workflow (session start, before marking a task
done, etc.) once the Phase 3 adapters are wired in. Manual invocation is
there for whenever you want to check something yourself.
 
## Files it manages
 
| File | Purpose |
|---|---|
| `AGENTS.md` | Auto-loaded memory: what the project is, the constitution (non-negotiable rules), and learned patterns/preferences |
| `PROJECT_STATUS.md` | Phases, milestones, tasks, checklists, decisions, last session summary |
| `PROJECT_SCOPE.md` | Boundaries, feature registry, and every task's spec sheet (goal, inputs, steps, data formats, edge cases, EARS-format acceptance criteria, constraints) |
| `PROJECT_CONFIG.md` | Settings — `scope_enforcement`, `spec_depth`, `branching_strategy`, cached per-language validation commands |
| `ARCHITECTURE.md` | Directory structure, module map, diagrams — regenerated when structure changes, not on every edit |
| `CODE_INDEX.md` | Every source file and what it does — fully automatic |
| `DEVELOPER_LOG.md` | Append-only session log |
| `README.md` / `INSTRUCTIONS.md` | Standard project docs |
 
## Task lifecycle
 
```
not_started
  -> clarifying          (spec sheet drafted, ambiguity resolved before coding starts)
  -> in_progress          (agent builds)
  -> self_check            (agent validates its own work — tiered by language)
  -> awaiting_human_review  (checklist shown to a human)
  -> done                   (human confirms; agent proposes a git commit message)
```
 
A task can loop back to `in_progress` if the human's review finds an issue.
Whether the spec sheet is a hard gate or a soft draft depends on the
project's `scope_enforcement` setting.
 
## Design principles
 
- **Deterministic first.** LLM judgment is used only where it's genuinely required — filling in narrative descriptions, judging ambiguity, writing diagram prose. Everything else is plain Python.
- **No hidden state.** Every file a human can open is the same file the CLI parses. Checksums live inside each source file's own header, not in a separate manifest.
- **The CLI never prompts.** It reads/writes files and prints text. The calling agent handles all human interaction.
- **Adapts to the project, not the other way around.** Validation is tiered per language rather than assuming everyone has `pytest`. Scope enforcement is a per-project toggle, not a fixed policy.
## Contributing
 
This started as an internal tool for a small group of collaborators across
data science, backend, and frontend work. Issues and PRs welcome, but expect
opinionated defaults tuned to that use case.
 
## License
 
MIT
 

