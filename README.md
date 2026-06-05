# orwir project templates — canonical source

This gist is the **single source of truth** for the reusable project lifecycle docs.
Each project keeps a *mirror* copy of the repo-facing files in `docs/guides/`; edit
here, then re-sync the mirrors.

## Files (lifecycle order)

- **`idea_gauntlet.md`** — pre-project stage-gate: idea → validated commitment, or a
  kill-log line. Covers software, hardware, and mixed builds. The filled copy lives
  at the project root as `IDEA.md`; on graduation it freezes into
  `docs/product/idea.md` as the origins artifact.
- **`project_kickstart.md`** — language-agnostic playbook for standing up and
  growing a project (branching, releases, CI, docs layers, tracking, the
  user-facing-surface foundation, what to grow / what to skip).
- **`agents_template.md`** — copy-and-fill skeleton for a new repo's `AGENTS.md`
  (the operating contract AI assistants read).
- **`codebase_review.md`** — comprehensive-review template (12 phases in the default
  layout) for solo-maintained Python repos. Run after a heavy build phase to catch
  drift, dead code, and quiet bugs; plan lives in `docs/reviews/` as a permanent
  record.
- **`ux_review.md`** — CUJ-driven review of the user-facing surface (web, desktop,
  TUI, CLI, chat bot): journey walkthroughs, error paths, consistency, latency,
  accessibility floor, surface diet. Shares the codebase review's machinery.

## Use in a project

Mirror the files into the repo and point `AGENTS.md` at the kickstart as the "why":

```
base=https://gist.githubusercontent.com/orwir/d288ef4ec7dcb37a4cd3e9ae2019c037/raw
curl -sL "$base/idea_gauntlet.md"     -o docs/guides/idea_gauntlet.md
curl -sL "$base/project_kickstart.md" -o docs/guides/project_kickstart.md
curl -sL "$base/agents_template.md"   -o docs/guides/agents_template.md
curl -sL "$base/codebase_review.md"   -o docs/guides/codebase_review.md
curl -sL "$base/ux_review.md"         -o docs/guides/ux_review.md
```

Re-run the same lines to pull the latest after editing the canonical here.

## Bootstrap a new idea (agent instructions)

When pointed at this gist from a new or empty project folder and asked to bootstrap
or prepare the gauntlet:

1. Mirror the files into `docs/guides/` (block above).
2. Create `IDEA.md` at the folder root from the fenced Template body in
   `docs/guides/idea_gauntlet.md`; fill `{{name}}` and the Captured date, set
   `Status: parked`.
3. Stop there. The gauntlet's answers and gates belong to the user — do not fill
   the Phase 0–2 judgments. On request, assist with Phase 1 research (existing
   solutions, costs) and the Phase 3 spike.

When the user says the idea passed and asks to start the project: follow
`docs/guides/project_kickstart.md` seeded from `IDEA.md` (done statement → v0.1
milestone, IN list → first issues, the spike's stack choice → first ADRs);
gauntlet Phase 4 covers the `IDEA.md` → `docs/product/idea.md` + `vision.md`
handoff.

## Edit the canonical

- Web: edit this gist in the browser.
- CLI: `gh gist edit d288ef4ec7dcb37a4cd3e9ae2019c037`
- Clone: `git clone https://gist.github.com/d288ef4ec7dcb37a4cd3e9ae2019c037.git`

When a project discovers a reusable pattern (not project-specific), fold it back
into the relevant file *here* so every project inherits it on the next sync.
A new file here needs the same justification as a new dependency — prefer
extending an existing doc over adding a seventh.
