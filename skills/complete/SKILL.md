---
name: complete
description: Close out a task on the maintainer's explicit go-ahead ("lgtm", "complete the task") — commit, push, close the issue, board to Done at the top, delete a merged branch
argument-hint: "[issue number; empty for an untracked task]"
---

Task: $ARGUMENTS — the issue number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named).

This is the *Complete* phase of AGENTS.md § Task workflow. It runs only on the maintainer's explicit go-ahead to complete this task, in their own latest message: "complete the task", "lgtm", "ship it" or the like. "go", "proceed", "start" or "implement" authorize code, never landing, and an earlier approval covers only what it named. Without one, stop and ask. With one, every step below runs as one batch, with no prompt between steps.

`lifecycle` is the kit's command (on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit); `lifecycle config` gives the integration branch (`branches.integration`), the gate (`gate.commands`) and whether there is a board. Read AGENTS.md § Task workflow too: a repository may add a step here or replace one (a release tag pushed with the work), and you do it where it says.

## 1. Before anything lands

- **The hand-back's answers.** Each answer the maintainer gave to the hand-back's D-rows, with this go-ahead or before it, and each *Taken alone* row they vetoed, is made first, by `task_review.md` § The work round, step 5, and the gate run again. A pick bigger than the size the brief stated, or any veto, stops the batch: render the brief again by the handback skill and wait for a new go-ahead.
- The gate — `gate.commands`, else AGENTS.md § Commands' lint and tests — passed in this session after the last edit; if not, run it now. A red gate stops the batch. A repository with no gate at all says so in the report.
- `git status --short` lists only this task's files. Anything else is someone's in-progress work: leave it out and name it in the report.

## 2. Kit issues

A gap this task found in a kit guide was filed on the kit when it was found (`task_review.md` § Developer rules, in the kit's `method/`): the hand-back carries each as a *Taken alone* row, and the report names it. One found and not yet filed is filed now, on the repository the kit's `.claude-plugin/plugin.json` names (in the folder `lifecycle where` prints), in the kit's words. Nothing of the kit's lands from this repository.

## 3. Commit

- Stage the task's files by name; never `git add -A`.
- One Conventional Commit (AGENTS.md § Branching and commits): the body says why, names every decision taken alone, every departure and each answer to the hand-back, and ends `Closes #N` on a tracked task. Write the message to a file in a scratch folder outside the tree and pass it with `-F`.
- A failing hook is fixed at its cause and the commit made again; never `--no-verify`, never amend a pushed commit.

## 4. Land

- **On the integration branch, or a worktree branch whose work lands on it directly:** `git push origin HEAD:<integration>`, or the push AGENTS.md § Task workflow gives in its place. The pre-push hook runs the gate. A push refused because the branch moved is rebased onto `origin/<integration>` and pushed again; a conflict stops for the maintainer.
- **On a `hotfix/<name>` branch:** `git push -u origin <branch>`, and nothing more: no PR and no merge. Write step 5's comment, naming the branch, and skip the rest of steps 5 to 7: the release ships the branch, and its merge into the integration branch closes the issue by its `Closes #N`; the release skill moves the card and deletes the branch.
- **On a feature branch:** `git push -u origin <branch>`; `gh pr create --base <integration> --title "<subject>" --body-file <file>` with `.github/pull_request_template.md` filled for a reader who never saw the review rounds; read `gh pr checks <N>` until it is green; `gh pr merge --squash --delete-branch`.
- Hooks that run the project's own tools need its environment: where the shell's interpreter is not the project's, put the project's environment first on `PATH` for the commit and the push (AGENTS.md § Commands).

## 5. Close the issue

- A pushed `Closes #N` closes the issue only when it lands on the repository's default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`), and a PR merge only into it. Comment with `gh issue comment <N> --body-file <file>`; where the work landed on another branch, also `gh issue close <N>`.
- The comment quotes at most the hand-back brief's *In the tree*: no round tally, verdict or finding id.

## 6. Board

When the settings name a board, `lifecycle board <N> Done` puts the card in Done, at the top. An untracked task has no card.

## 7. Branches

- A merged feature branch: `--delete-branch` deleted it on GitHub and here, after switching to the integration branch and pulling it. `git fetch --prune` drops its remote-tracking ref. Where gh warned that it could not fast-forward, the integration branch has diverged from its remote: stop, and report `git status -sb`.
- A worktree's own branch stays while its worktree exists, and goes with it: in a linked worktree, gh leaves the local branch.

## 8. Report

One line per step with its coordinates: the issues filed on the kit, the commit, where it was pushed, the PR, the issue's state, the board column. Anything skipped says why.
