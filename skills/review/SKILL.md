---
name: review
description: Run the work round for the task done in this session (the method's task_review.md) — hand-off packet against the accepted plan, a reviewer per lens, fixes, hand-back brief
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for a task with no issue (where nothing substitutes `$ARGUMENTS`, what the maintainer named). An untracked micro-task skips the round, and the handback skill renders its brief.

You are the developer and you run the whole round here. The maintainer reads only the brief at the end, so print nothing but the one line in § 2.

## 0. Before anything

1. `lifecycle` is the kit's command: on PATH where the kit's Claude plugin is on, otherwise `bin/lifecycle` in a checkout of the kit.
2. `lifecycle doctor --json`:
   - a finding whose fix is `upgrade` waits: the task's edits are in the tree, and the round needs nothing a port brings; the session start carries it to the next task;
   - a `block` whose fix is `adopt` or `update-kit`, or a failure of the command: stop and tell the maintainer what it printed;
   - anything else: carry on.
3. `lifecycle config` prints the settings; the lenses are its `review.lenses`. Below, `<method>` is `method/` in the folder `lifecycle where` prints, and *§* a section of `<method>/task_review.md`.
4. **The gate** is `gate.commands`, in order; with none, the lint and test commands AGENTS.md § Commands gives; with neither, the gate is `not run`, and the brief says so.
5. Read `<method>/task_review.md`: the hand-off packet, the return packet, the brief rules and the developer rules are there. Read `AGENTS.md` § Task workflow too, and do any step it adds before the hand-back (a design close, a sync check) where it says.
6. **The task.** An empty argument is an untracked task. A number is told by `gh pr view <N> --json number,headRefName,closingIssuesReferences`, which succeeds only for a PR:
   - it fails: `<N>` is an issue, `<issue>`;
   - a PR closing exactly one issue: `<PR>` is the number and `<issue>` the issue it closes;
   - a PR closing none or several: ask the maintainer which issue holds the plan; review it untracked only on their word;
   - a PR whose `headRefName` is not `git branch --show-current`: stop and tell the maintainer.

## 1. Render the hand-off packet — gather, don't recall

1. **Coordinates.** `git status --short`, `git diff --stat`, `git rev-parse --short HEAD` (the base). On a branch with no `<PR>` from § 0, `gh pr view --json number,state,baseRefName`: an `OPEN` one is `<PR>`. The flow and its diff command are § Hand-off packet's: the integration branch (`branches.integration`), a branch, or `<PR>` checked out here. List every new file by path.
2. **Lenses** (§ Lens reviewers):
   - `base` always;
   - `person-facing` where the diff changes what a person reads or drives;
   - `model-facing` where it changes what a model reads, how it is asked, or the eval that scores it;
   - the rule decides, each lens's `paths` in the settings showing where those changes usually sit; where a path's lens is unclear, launch it;
   - an upgrade's port into `AGENTS.md` or `CONTRIBUTING.md` takes the base lens only.
3. **The plan.** `gh issue view <issue>`, the tree held to its `## Plan`:
   - accepted (`**Status:** accepted <date>`): carry on;
   - still `proposed`: never accepted; stop and tell the maintainer before rendering anything;
   - no `## Plan`, an issue filed before the plan round: *Reconciliation* takes the ticket's technical-details boxes, each landed, dropped or added beyond the ticket, any deviation from its mechanism named as one; *Departures* and *Scenarios* read `none: no plan`;
   - untracked: one line of intent first; *Reconciliation*, *Departures* and *Scenarios* read `none: untracked`.
4. **Reconciliation.** One line per box of the plan, `landed` or `dropped: <why>`, and an `added beyond the plan: <why>` line per path the tree changed outside them. Tick every landed box still open: the body to a file in a scratch folder outside the tree, then `gh issue edit <issue> --body-file <file>`.
5. **Departures:** the plan's section as it stands, or `none`.
6. **Scenarios.** One line per WHEN line of the plan's *Behaviour*: the test that fails without the change, or `not covered: <why>`, a scenario no test can score naming how it is scored. The same ids go on *Verification*. "Fails without" is proven on a worktree of the base, never by `git stash`:
   1. `git worktree add --detach <scratch folder>/<dir> <base>` — `HEAD` on the integration branch, `git merge-base <integration> HEAD` on a branch — with the new or changed test files copied in;
   2. run those tests there by `gate.targeted`, `{root}` the worktree and `{tests}` the tests in the form it takes; with none, by the targeted run AGENTS.md § Commands gives, pointed at the worktree; with neither, the scenario reads `not covered: no targeted run`;
   3. check the run loaded the code under test from the worktree: one that loaded this tree is run again from the worktree, or reads `not covered: the targeted run loaded this tree`; a run that collected no tests reads `not covered: the targeted run collected none`;
   4. `git worktree remove --force <worktree>`.
7. **Read first:** the docs, ADR sections or guides the diff is held to beyond AGENTS.md, or `none`.
8. **The gate.** If it did not run in this session after the last edit, run it now; a red gate is fixed before the packet, since the round runs on a green one (§ When it runs). Report the numbers; what still could not run goes under `NOT RUN`, with its reason.
9. **Decisions taken alone:** the plan's `Taken:` lines and every option picked without the maintainer since, every hypothesis left untested and where it is marked, every spend and where it was asked, every issue filed (a gap in a kit guide as `lifecycle gap` named it), every `Watch:` line and every `Not filed:` entry in the plan. `none` is a claim the reviewer checks.
10. **Where to look:** the two or three hunks you are least sure of, the invariant each relies on and the test that enforces it, or `stated only`.
11. **Docs:** the files touched per AGENTS.md's change → doc mapping and the CHANGELOG line quoted, or why there is none; then what AGENTS.md's added steps produced, or `none`.

The packet follows § Hand-off packet's shape and rules.

## 2. Launch the reviewers

One reviewer per lens, all at once, in the background, each with the packet carrying its lens on the `Lens:` line as its whole task; the reviewer definition carries the rules. The first of these the agent can do:

1. **The kit's reviewer agent:** in Claude Code, one `Agent` call per lens in one message, `subagent_type: "lifecycle:reviewer"`, `run_in_background: true`. The kit's hook holds it to commands that read.
2. **A general-purpose subagent** per lens, whose task is the definition — `agents/reviewer.md` in the folder `lifecycle where` prints, without its front matter — above the packet. Use it where the first is not listed: a plugin installed in this session is not always picked up at once. No guard fires for it: the brief marks that lens `(no guard)`.
3. **A fresh session per lens the maintainer opens:** the definition and that lens's packet in one file in a scratch folder outside the tree, which the maintainer pastes into a new session, pasting the return back. The brief marks that lens `(pasted)`.

The clarify skill launches its one plan reviewer by this list too.

Print one line: the reviewers launched, by lens, and that the brief follows; for pasted sessions, the request to paste each file, with its path. Edit nothing until every return arrives (§ Terms, *Launch*).

## 3. Act on the returns

By § The work round, step 3, and § Return packet's table:

- first check each finding's evidence, by § Developer rules: one whose locations do not show what its evidence says they show, or an `inferred` or unmarked one you cannot prove, is disputed on evidence;
- fix every finding that holds: each required one, and each `Cleanup` and `Minor` inside the diff; one defect two returns report is one finding;
- every `Decision pending` and every *For the maintainer* question you cannot settle goes by its door (§ Terms): a two-way one is made in the tree, at the reviewer's recommendation or at your own pick with the reviewer's option named, and written as a `Taken:` line (§ Developer rules); a one-way one, every finding you dispute, on evidence or on scope (§ Terms), and a `split` go to the brief as D-rows;
- a fix that leaves the accepted plan is a departure, by § Developer rules;
- an exploitable finding is fixed here or goes by the private route (§ Return packet) — where the repository names no private channel, to the brief as a D-row — never into an issue;
- a follow-up a return asks for goes by the bar (§ Developer rules): one that passes is filed first, labelled as the repository's `AGENTS.md` says, and, where the settings name a board, `lifecycle board <new> Backlog`, the brief's row carrying `<new>`'s number, title and link; one that does not goes as § Developer rules sends it;
- a `Real bug` buys its reviewer a second pass: after the fixes, send the same reviewer the reply per finding id — `fixed <how>` / `disputed: the evidence does not hold — <what the locations show>` / `disputed: <why it is not yours to act on>` / `deferred #<new>` / `watch: <trigger>` / `reported privately` — and act on its second return the same way, never buying a third (§ Terms, *Pass*); in Claude Code, `SendMessage` to the subagent; for a pasted session, a second file the maintainer pastes into the same session;
- re-run the gate after the last edit; a red gate is fixed before the hand-back.

## 4. Hand back

Render the brief by the handback skill. The packets stay in the reviewer calls' prompts and results.
