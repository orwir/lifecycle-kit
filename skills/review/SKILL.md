---
name: review
description: Run the work round for the task done in this session (the method's task_review.md) — hand-off packet against the accepted plan, a reviewer per lens, fixes, hand-back brief
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for a task with no issue, whose packet opens `untracked:` (where nothing substitutes `$ARGUMENTS`, what the maintainer named). An untracked micro-task skips the round, and the handback skill renders its brief.

## 0. Before anything

- `lifecycle` is the kit's command: on PATH where the kit's Claude plugin is on, otherwise `bin/lifecycle` in a checkout of the kit.
- `lifecycle doctor --json`. A finding whose fix is `upgrade` waits: the task's edits are in the tree, and the round needs nothing a port brings, since the method is served from the installed kit. The session start carries it to the next task, where the upgrade skill runs alone. A `block` whose fix is `adopt` or `update-kit`, or any failure of the command: stop and tell the maintainer what it printed.
- `lifecycle config` prints the repository's settings, and the lenses are its `review.lenses`. Below, `<method>` is the `method/` folder in the folder `lifecycle where` prints: the kit's guides, served from the installed kit.
- **The gate** is `gate.commands`, in order; where the settings name none, the commands AGENTS.md § Commands gives for lint and tests; with neither, the gate is `not run`, and the brief says so.
- Read `<method>/task_review.md`: the packet shapes, the brief and the developer rules are there. This round reads the tree against the plan accepted at *Clarify* (the clarify skill). Read `AGENTS.md` § Task workflow too: a repository may add a step before the hand-back (a design close, a sync check), and you do it where it says.

You are the developer and you run the whole round here. The maintainer reads only the brief at the end, so print nothing else but the one line in step 2.

## 1. Render the hand-off packet — gather, don't recall

1. **Coordinates.** `git status --short`, `git diff --stat`, `git rev-parse --short HEAD` (the base). State the flow — direct on the integration branch (`branches.integration`), a feature branch, or an existing PR (`gh pr view --json number,url,baseRefName`) — and the diff command that matches it. List every new file by path: `git diff` does not show them.
   - *Lenses*, from the changed and new paths (`task_review.md` § Lens reviewers). `base` always. `person-facing` when the diff changes what a person reads or drives; `model-facing` when it changes what a model reads, how it is asked, or the eval that scores it. The rule decides; each lens's `paths` in the settings are where those changes usually sit, not the whole list, and where a path's lens is unclear, launch it. An upgrade's port into agent-instruction text (`AGENTS.md`, `CONTRIBUTING.md`) takes the base lens only.
2. **The plan.** `gh issue view <N>`: the tree is held to its `## Plan`, accepted at *Clarify* (`**Status:** accepted <date>`). A plan still `proposed` was never accepted: stop and tell the maintainer before rendering anything.
   - *Reconciliation*: one line per box of the plan's technical details — `landed` or `dropped: <why>` — and an `added beyond the plan: <why>` line per path the tree changed outside them. Tick every landed box still open: write the body to a file in a scratch folder outside the tree with those boxes ticked, then `gh issue edit <N> --body-file <file>`.
   - *Departures*: the plan's *Departures* section copied as it stands, or `none`.
   - No `## Plan` — an issue filed before the plan round: copy the ticket's technical-details boxes into *Reconciliation* one per line, and mark each landed / dropped / added beyond the ticket. Name any deviation from its mechanism as one. *Departures* and *Scenarios* read `none: no plan`.
   - Untracked: one line of intent on the first line; *Reconciliation*, *Departures* and *Scenarios* read `none: untracked`.
3. **Scenarios.** One line per WHEN line of the plan's *Behaviour*: the id of the test that fails without the change, or `not covered: <why>`. A scenario a test cannot score names how it is scored. The same ids go on the *Verification* line. Prove "fails without" on a worktree of the base, never by `git stash`:
   - `git worktree add --detach <scratch folder>/<dir> <base>` — `HEAD` on the integration branch, `git merge-base <integration> HEAD` on a branch — with the new or changed test files copied in;
   - run those tests there by `gate.targeted`, with `{root}` the worktree and `{tests}` the new or changed tests in the form that command takes; with no `gate.targeted`, by the targeted-run command AGENTS.md § Commands gives, pointed at the worktree; with neither, the scenario reads `not covered: no targeted run`;
   - the run must load the code under test from the worktree, not from this tree: check where it imported from. A run that collected no tests proves nothing;
   - `git worktree remove --force <worktree>`.
4. **Read first.** The docs, ADR sections or guides the diff is held to beyond AGENTS.md, or `none`.
5. **The gate.** If the gate did not run in this session after the last edit, run it now. Report the numbers; anything that still could not run goes under `NOT RUN` with its reason.
6. **Decisions taken alone.** Every option picked without the maintainer, every hypothesis left untested and where it is marked, every spend, and every issue filed on the kit for a gap in a kit guide, as `<kit owner>/<kit repository>#M`. `none` is a claim the reviewer checks.
7. **Where to look.** The two or three hunks you are least sure of, the invariant each relies on, and the test that enforces it — or `stated only`.
8. **Docs.** The files touched per AGENTS.md's change → doc mapping, and the CHANGELOG line quoted, or why there is none. Then what AGENTS.md's added steps produced (a design page closed, a sync check's reading), or `none`.

Claims with coordinates, never the diff or file contents; self-contained, with no reference to this conversation; no pre-arguing of findings.

## 2. Launch the reviewers

One reviewer per lens, all at once, in the background, each with the packet carrying its lens on the `Lens:` line as its whole task. The reviewer definition carries the rules, so add nothing to the packet. The first of these the agent can do:

1. **The kit's reviewer agent** — in Claude Code, one `Agent` call per lens in one message, `subagent_type: "lifecycle:reviewer"`, `run_in_background: true`. The kit's hook holds it to commands that read.
2. **A general-purpose subagent** per lens whose task is the definition — `agents/reviewer.md` in the folder `lifecycle where` prints, without its front matter — above the packet. Use it where the first is not listed (a plugin installed in this session is not always picked up at once). No guard fires for it: the brief's status line marks that lens `(no guard)`.
3. **A fresh session per lens the maintainer opens**: write the definition and that lens's packet to one file in a scratch folder outside the tree, ask the maintainer to paste each into a new session and paste the return back. The brief's status line marks that lens `(pasted)`.

Print one line: the reviewers launched for the task, by lens, and that the brief follows — or, for pasted sessions, the request to paste each file, with its path. Do not print the packet. Edit nothing until every return arrives; the reviewers are reading the tree.

## 3. Act on the returns

- Fix every `Real bug` and `Drift`; `Cleanup` and `Minor` only inside the diff; `Acceptable` is recorded. One defect two returns report is one finding. Every `Decision pending`, every *For the maintainer* question you cannot settle, every finding you dispute and a `split` go to the brief.
- A fix that leaves the accepted plan is a departure: write it into the issue's *Departures* when you make it. One that is user-visible, hard to undo or changes scope stops for the maintainer first.
- An exploitable finding, whatever its label, is fixed here or goes by the private route (`task_review.md` § Return packet) — where the repository names no private channel, to the brief as a D-row — never into an issue. Before any other finding is deferred, file it, labelled as the repository's `AGENTS.md` says, and, when the settings name a board, `lifecycle board <new> Backlog` — the brief's row carries the number and title.
- A `Real bug` in a return buys that reviewer a second pass: after the fixes, send the same reviewer the reply per finding id — `fixed <how>` / `disputed <why>` / `deferred #N` / `reported privately` — wait for its second return, and act on it the same way. The same reviewer keeps its context: in Claude Code, `SendMessage` to the subagent; for a pasted session, a second file the maintainer pastes into the same session. No third pass: what is still disputed is a D-row.
- Re-run the gate after the last edit.

## 4. Hand back

Render the brief by the handback skill, exactly. The packets are not printed: they stay in the reviewer calls' prompts and results.
