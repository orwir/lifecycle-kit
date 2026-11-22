# The lifecycle method

This folder is the method of the lifecycle kit (`orwir/lifecycle-kit`): the reusable
guides every project follows, from an idea's gauntlet to its releases and reviews. A
project keeps no copy: its agents read the guides from the installed kit, in `method/`
of the folder `lifecycle where` prints, so every project reads the installed release
from its next session. How a repository uses the kit is the kit's `docs/guide.md`; a
gap a project finds in a guide is filed with `lifecycle gap`, by `task_review.md`
§ Developer rules, and the kit's own task changes the guide.

## Files (lifecycle order)

- **`idea_gauntlet.md`** — pre-project stage-gate: an evening on whether the idea is
  worth its cost (its journeys, the best existing option tried by hand), an evening
  shaping it (the IA, a picture only where needed), then one decision — make, park,
  or kill. Covers software, hardware, and mixed builds, and games built from any
  of them. Every idea lives in a private ideas home repo: one folder each, with
  `IDEA.md` and its evidence (`docs/product/`, `design/`). A graduated idea moves
  out into its own repo with its kill criteria, `IDEA.md` freezes into
  `docs/product/idea.md`, and the home checks the project on a schedule; a killed
  one moves to the home's `archive/`.
- **`ideas_home_template.md`** — the ideas home's `AGENTS.md`, which a home adapts: its
  layout and how to capture, kill, graduate and check, for any agent opened in it.
  Setting a home up where there is none is `idea_gauntlet.md` § The ideas home.
- **`project_kickstart.md`** — language-agnostic playbook for standing up and
  growing a project (branching, releases, CI, docs layers, tracking, the
  user-facing-surface foundation, what to grow / what to skip).
- **`agents_template.md`** — copy-and-fill skeleton for a new repo's `AGENTS.md`
  (the operating contract AI assistants read).
- **`contributing_template.md`** — copy-and-fill skeleton for a new repo's
  `CONTRIBUTING.md`: local setup, the release checklist and hotfixes.
- **`issue_template_bug.md`** / **`issue_template_task.md`** — copy-and-fill issue
  templates; install to `.github/ISSUE_TEMPLATE/` as `bug.md` / `task.md`.
- **`pr_template.md`** — copy-and-fill PR template; install to
  `.github/pull_request_template.md`.
- **`task_review.md`** — a task's two review rounds, each read by a reviewer agent
  with no author context (a subagent, where the assistant can launch one). The plan
  round, at Clarify, reads the plan in the issue against the code when the plan has a
  shape that has shipped holes before, and ends in the Clarify brief; the work round,
  before the hand-back, reads the tree against the accepted plan, with a lens reviewer
  for each of the person- and model-facing lenses the diff touches, and ends in the hand-back
  brief. The packets between the agents, the briefs, and each role's rules;
  the same rounds whether the work rides a PR or lands on the integration branch.
- **`review_machinery.md`** — what every comprehensive review shares: the five kinds,
  the order they run in and when each is due; a parent issue per review; a lead with
  phase agents in waves; findings and the seven-label severity vocabulary; action items
  and how they close; the private route for exploitable findings; the close-out (record
  frozen, issues carry the follow-through) and the Decision register.
- **`codebase_review.md`** — comprehensive-review template (13 phases, 0–12, in the default
  layout) for solo-maintained repos; the method is language-agnostic and the shell
  recipes are shown for Python. Run after a heavy build phase to catch
  drift, dead code, and quiet bugs. Runs on `review_machinery.md`.
- **`ux_review.md`** — CUJ-driven review of the user-facing surface (web, desktop,
  TUI, CLI, chat bot): expert walkthroughs beside a real-user source, error paths,
  consistency, latency, accessibility floor, surface diet. Runs on `review_machinery.md`.
- **`ia_review.md`** — information-architecture review of the user-facing surface:
  which screens, commands and messages exist, what each shows and for which reader's
  decision, where each fact lives, and what is missing. Ends in a target structure
  written back to the intent doc, an ADR, and filed work. Runs on `review_machinery.md`.
- **`llm_review.md`** — review of what a product tells its language model and how it
  knows the replies are good: the text the model reads, the model settings, and the
  eval that measures the replies. Runs on `review_machinery.md`.
- **`design_workflow.md`** — the design lifecycle (the *how*): found the foundation
  before screen 2, codify every design round back into it, and evolve it on a
  trigger. Companion to each project's own `design_language.md` (the *what* — tokens,
  components, patterns), which is project-specific and not part of the method.
- **`design_review.md`** — the runnable design-language pass: establish or evolve the
  visual system (baseline → north-star → foundations → components & states →
  conformance audit → codify). The design counterpart of the code and UX reviews;
  runs on `review_machinery.md`.
