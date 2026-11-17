# orwir project templates — canonical source

This gist is the **single source of truth** for the reusable project lifecycle docs.
Each project keeps a *mirror* copy of the repo-facing files in `docs/guides/`; edit
here, then re-sync the mirrors.

## Files (lifecycle order)

- **`idea_gauntlet.md`** — pre-project stage-gate: an evening of research and
  definition, an evening drawing the product, then one decision — make, park, or
  kill. Covers software, hardware, and mixed builds. Every idea lives in a private
  ideas home repo: one folder each, with `IDEA.md` and its evidence
  (`docs/product/`, `design/`). A graduated idea moves out into its own repo, where
  `IDEA.md` freezes into `docs/product/idea.md`; a killed one moves to the home's
  `archive/`.
- **`project_kickstart.md`** — language-agnostic playbook for standing up and
  growing a project (branching, releases, CI, docs layers, tracking, the
  user-facing-surface foundation, what to grow / what to skip).
- **`agents_template.md`** — copy-and-fill skeleton for a new repo's `AGENTS.md`
  (the operating contract AI assistants read).
- **`contributing_template.md`** — copy-and-fill skeleton for a new repo's
  `CONTRIBUTING.md`: branching with branch-deletion hygiene, quality gates, the
  four-column board lifecycle, the release checklist.
- **`issue_template_bug.md`** / **`issue_template_task.md`** — copy-and-fill issue
  templates; install to `.github/ISSUE_TEMPLATE/` as `bug.md` / `task.md`.
- **`pr_template.md`** — copy-and-fill PR template; install to
  `.github/pull_request_template.md`.
- **`task_review.md`** — a task's two review rounds, each read by a reviewer agent
  with no author context (a subagent, where the assistant can launch one). The plan
  round, at Clarify, reads the plan in the issue against the code when the plan has a
  shape that has shipped holes before, and ends in the Clarify brief; the work round,
  before the hand-back, reads the tree against the accepted plan and ends in the
  hand-back brief. The packets between the agents, the briefs, and each role's rules;
  the same rounds whether the work rides a PR or lands on the integration branch.
- **`codebase_review.md`** — comprehensive-review template (13 phases, 0–12, in the default
  layout) for solo-maintained repos; the method is language-agnostic and the shell
  recipes are shown for Python. Run after a heavy build phase to catch
  drift, dead code, and quiet bugs; plan lives in `docs/reviews/` as a permanent
  record.
- **`ux_review.md`** — CUJ-driven review of the user-facing surface (web, desktop,
  TUI, CLI, chat bot): journey walkthroughs, error paths, consistency, latency,
  accessibility floor, surface diet. Shares the codebase review's machinery.
- **`design_workflow.md`** — the design lifecycle (the *how*): found the foundation
  before screen 2, codify every design round back into it, and evolve it on a
  trigger. Companion to each project's own `design_language.md` (the *what* — tokens,
  components, patterns), which is project-specific and not mirrored here.
- **`design_review.md`** — the runnable design-language pass: establish or evolve the
  visual system (baseline → north-star → foundations → components & states →
  conformance audit → codify). The design counterpart of the code and UX reviews;
  shares the codebase review's machinery.

## Use in a project

Mirror the files into the repo (an ideas home mirrors them once, at its root) and
point `AGENTS.md` at the kickstart as the "why":

```
base=https://gist.githubusercontent.com/orwir/d288ef4ec7dcb37a4cd3e9ae2019c037/raw
curl -sL "$base/idea_gauntlet.md"     -o docs/guides/idea_gauntlet.md
curl -sL "$base/project_kickstart.md" -o docs/guides/project_kickstart.md
curl -sL "$base/agents_template.md"   -o docs/guides/agents_template.md
curl -sL "$base/contributing_template.md" -o docs/guides/contributing_template.md
curl -sL "$base/issue_template_bug.md"    -o docs/guides/issue_template_bug.md
curl -sL "$base/issue_template_task.md"   -o docs/guides/issue_template_task.md
curl -sL "$base/pr_template.md"           -o docs/guides/pr_template.md
curl -sL "$base/task_review.md"       -o docs/guides/task_review.md
curl -sL "$base/codebase_review.md"   -o docs/guides/codebase_review.md
curl -sL "$base/ux_review.md"         -o docs/guides/ux_review.md
curl -sL "$base/design_workflow.md"   -o docs/guides/design_workflow.md
curl -sL "$base/design_review.md"     -o docs/guides/design_review.md
```

Re-run the same lines to pull the latest after editing the canonical here.

## Bootstrap a new idea (agent instructions)

When pointed at this gist and asked to bootstrap or prepare the gauntlet:

1. Find the user's ideas home: a repo whose root `AGENTS.md` says it is one (the
   user's global agent instructions may name it). If there's none, offer to set
   one up where the user chooses, private by default, with the layout in
   `idea_gauntlet.md` § *The ideas home*: its root `AGENTS.md` (the template
   there), `archived.md`, `graduated.md`, `active/`, `archive/`, and this gist
   mirrored into `docs/guides/` (block above).
2. Check `archived.md`: if this idea, or a close variant, was killed before, show
   the line — re-opening needs new facts against the logged reason.
3. Create `active/<idea>/IDEA.md` from the fenced Template body in
   `docs/guides/idea_gauntlet.md`; fill `{{name}}` and the Captured date, set
   `Status: captured`.
4. Stop there. The answers in `IDEA.md`, the bar and every verdict belong to the
   user — never fill them or call a gate. On request, do the legwork into the
   idea's artifacts: Phase 1 research (`docs/product/competitors.md`,
   `docs/product/feasibility.md`) and draft CUJs for the user to agree; Phase 2's
   competitor walk sheet and the low-fidelity picture in `design/`; the Phase 3
   spike in `spike/`.

When the user kills the idea: move its folder to `archive/<YYYY-MM-DD>-<idea>/`,
set its Status, and add the line to `archived.md` in the user's words.

When the user says the idea passed and asks to start the project: move the folder
into the project's own repo (`git subtree split --prefix=active/<idea>` keeps its
history), add a line to `graduated.md`, mirror the guides into the new repo, then
follow `docs/guides/project_kickstart.md` seeded from `IDEA.md` and its artifacts
(done statement → v0.1 milestone, IN list → first issues, the spike's stack choice
and the decisions recorded in `IDEA.md` → first ADRs); gauntlet Phase 4 covers the
`IDEA.md` → `docs/product/idea.md` + `vision.md` handoff.

## Edit the canonical

- Web: edit this gist in the browser.
- CLI: `gh gist edit d288ef4ec7dcb37a4cd3e9ae2019c037`
- Clone: `git clone https://gist.github.com/d288ef4ec7dcb37a4cd3e9ae2019c037.git`

When a project discovers a reusable pattern (not project-specific), fold it back
into the relevant file *here* so every project inherits it on the next sync.
A new file here needs the same justification as a new dependency — prefer
extending an existing doc over adding another file.
