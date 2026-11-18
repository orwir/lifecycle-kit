# orwir project templates — canonical source

This gist is the **single source of truth** for the reusable project lifecycle docs.
Each project keeps a *mirror* copy of its files in `docs/guides/`. A change is made
in the mirror of the project that found it, reviewed in that project's diff, and
pushed here (*Edit the canonical*); the other mirrors re-sync.

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
  components, patterns), which is project-specific and not mirrored here.
- **`design_review.md`** — the runnable design-language pass: establish or evolve the
  visual system (baseline → north-star → foundations → components & states →
  conformance audit → codify). The design counterpart of the code and UX reviews;
  runs on `review_machinery.md`.

## Use in a project

Mirror the files into the repo (an ideas home mirrors them once, at its root) and
point `AGENTS.md` at the kickstart as the "why":

```
gist=d288ef4ec7dcb37a4cd3e9ae2019c037
rev=$(git ls-remote "https://gist.github.com/$gist.git" HEAD | cut -f1)
base="https://gist.githubusercontent.com/orwir/$gist/raw/$rev"
dl=$(mktemp -d)
for f in README.md idea_gauntlet.md project_kickstart.md agents_template.md \
         contributing_template.md issue_template_bug.md issue_template_task.md \
         pr_template.md task_review.md review_machinery.md codebase_review.md \
         ux_review.md ia_review.md llm_review.md design_workflow.md design_review.md; do
  curl -sfL "$base/$f" -o "$dl/$f" || { echo "failed: $f; nothing changed"; rm -rf "$dl"; break; }
done
[ -d "$dl" ] && cp "$dl"/* docs/guides/ && echo "$rev" > docs/guides/.gist-revision && rm -rf "$dl"
```

Re-run the block to re-sync, on a clean mirror only (*Edit the canonical*). It pins
every file to one revision, which also sidesteps the five-minute cache on the
unpinned raw links, and records that revision in `.gist-revision`: the point a push
starts from. It changes all or nothing: if any download fails, it names the file
and leaves the mirror and its revision as they were.

A mirror runs the block from its own copy of this README, so a file added to the
gist after that copy arrives on the second re-sync: the first one fetches the README
that names it. Between the two, the check lists that file as `missing`.

A mirror from before `.gist-revision` has no recorded revision to check against:
compare it with the gist's current files, push anything only the mirror has, then
re-sync.

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

When a project discovers a reusable pattern (not project-specific), it comes back
here so every project inherits it on the next re-sync. The change starts in the
mirror of the project that found it, inside the task that found it, so it is
reviewed in that project's diff with the rest of the task.

1. **Sync first.** Before the first edit, re-sync the mirror (*Use in a project*).
2. **Edit the mirror** inside the task. The task's hand-back names the push to the
   gist as a step of its *Complete*.
3. **Push at *Complete***, on the task's go-ahead: the check below, then the push
   block. Git replays the change onto anything pushed since the recorded revision;
   a conflict stops the push and goes back to the maintainer.
4. **Re-sync the mirror**, so it matches the revision just pushed.

Two rules keep every mirror safe:

- **A mirror edit never outlives its task.** It is pushed at *Complete* or
  reverted, so a re-sync, which overwrites, never meets an unpushed edit.
- **A push starts from the recorded revision**, not from whatever the gist holds
  now, so a mirror that fell behind cannot revert anyone else's change.

The check lists what differs from the recorded revision: before a re-sync nothing
may, before a push these are the files to push. A file the mirror's re-sync block
names but the gist does not hold yet is listed as `new`, and pushed like the rest.
A file the gist holds but the mirror lacks is listed as `missing`: it reached the
gist after the mirror's block, the next re-sync fetches it, and it does not block
one. Run it from the project root:

```
gist=d288ef4ec7dcb37a4cd3e9ae2019c037
tmp=$(mktemp -d) && git clone -q "https://gist.github.com/$gist.git" "$tmp" &&
git -C "$tmp" checkout -q "$(cat docs/guides/.gist-revision)" &&
for f in $(git -C "$tmp" ls-files); do
  [ -e "docs/guides/$f" ] || { echo "missing: $f"; continue; }
  tr -d '\r' < "docs/guides/$f" | cmp -s - "$tmp/$f" || echo "differs: $f"
done &&
for f in $(tr -d '\r' < docs/guides/README.md |
           sed -n '/^for f in README\.md /,/; do$/p' | grep -oE '[A-Za-z_]+\.md'); do
  [ -e "$tmp/$f" ] || echo "new: $f"
done
```

The push, in the same shell, with the files the check listed as `differs` or `new`
(`tr` keeps the gist LF whatever the project's checkout uses):

```
git -C "$tmp" switch -q -c push
for f in <the differing and new files>; do tr -d '\r' < "docs/guides/$f" > "$tmp/$f"; done
git -C "$tmp" add -A && git -C "$tmp" commit -qm "<what changed and why, one line>"
git -C "$tmp" pull -q --rebase origin main
git -C "$tmp" push -q origin HEAD:main
```

The maintainer can still edit the gist directly (web, `gh gist edit`, a clone):
mirrors pick that up at their next re-sync, and pushes rebase onto it.

A new file here needs the same justification as a new dependency — prefer
extending an existing doc over adding another file. A new file also joins the
re-sync block, and the check lists it as new until it is pushed.
