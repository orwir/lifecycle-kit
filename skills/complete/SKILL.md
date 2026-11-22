---
name: complete
description: Close out a task on the maintainer's explicit go-ahead ("lgtm", "complete the task") — commit, push, close the issue, board to Done at the top, delete a merged branch
argument-hint: "[issue number; empty for an untracked task]"
---

Task: $ARGUMENTS — the issue number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named). A PR number is told from an issue, and its issue found, as the review skill's § 0 step 6 says (`skills/review/SKILL.md` in the folder `lifecycle where` prints). Below, `<issue>` is that issue, and `<PR>` a feature branch's pull request.

This is the *Complete* phase of AGENTS.md § Task workflow. It runs only on the maintainer's explicit go-ahead to complete this task, in their own latest message: "complete the task", "lgtm" or the like.

- "go", "proceed", "start" or "implement" authorize code, never landing.
- "ship it" is a go-ahead for neither this skill nor the release skill: ask whether it means landing this task.
- An earlier approval covers only what it named.
- Without a go-ahead, stop and ask. With one, every step below runs as one batch, with no prompt between steps.

`lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit. `lifecycle config` gives the integration branch (`branches.integration`), the gate (`gate.commands`) and whether there is a board. Read AGENTS.md § Task workflow too, and do any step it adds or replaces (a release tag pushed with the work) where it says.

## 1. Before anything lands

1. **The hand-back's answers,** by `task_review.md` § The work round, step 5: each answer to the hand-back's D-rows given with this go-ahead or before it; each D-row left unanswered, which takes its recommendation, written as taken at the go-ahead; each choice taken alone the maintainer vetoed. The gate runs again after them. A pick bigger than the size the brief stated, or any veto, stops the batch: render the brief again by the handback skill and wait for a new go-ahead.
2. **The gate** — `gate.commands`, else AGENTS.md § Commands' lint and tests — passed in this session after the last edit; if not, run it now. A red gate stops the batch. A repository with no gate says so in the report.
3. `git status --short` lists only this task's files. Anything else is someone's in-progress work: leave it out and name it in the report.

## 2. Kit issues

A gap this task found in a kit guide was filed on the kit when it was found (`task_review.md` § Developer rules), and the hand-back's *Taken alone* names it. One found and not yet filed is filed now, on the repository the kit's `.claude-plugin/plugin.json` names (in the folder `lifecycle where` prints), in the kit's words. Nothing of the kit's lands from this repository.

## 3. Commit

1. Stage the task's files by name; never `git add -A`.
2. One Conventional Commit (AGENTS.md § Branching and commits): the body says why, names every decision taken alone with its reason (the plan's `Taken:` lines, the hand-off's and the hand-back's), every departure, each answer to the hand-back and each spend with its amount, and ends `Closes #<issue>` on a tracked task. A fix for an exploitable finding in released code keeps its location and detail out of every public record `task_review.md` § Return packet lists, until its fix ships.
3. The message goes in a file in a scratch folder outside the tree, passed with `-F`.
4. A failing hook is fixed at its cause and the commit made again; never `--no-verify`, never amend a pushed commit.

## 4. Land

Where the shell's interpreter is not the project's, put the project's environment first on `PATH` for the commit and the push: its hooks run its own tools (AGENTS.md § Commands).

- **On the integration branch, or a worktree branch whose work lands on it directly:** `git push origin HEAD:<integration>`, or the push AGENTS.md § Task workflow gives in its place. The pre-push hook runs the gate. A push refused because the branch moved: `git fetch origin`, rebase onto `origin/<integration>`, push again; a conflict stops for the maintainer.
- **On a `hotfix/<name>` branch:** `git push -u origin <branch>`, and nothing more: no PR and no merge. Write § 5's comment, naming the branch, and skip the rest of §§ 5 to 7: the release ships the branch, its merge into the integration branch closes the issue by its `Closes #<issue>`, and the release skill moves the card and deletes the branch.
- **On a feature branch:**
  1. `git push -u origin <branch>`.
  2. `gh pr view <branch> --json number,state`: an `OPEN` PR is `<PR>`. With none, or only a closed or merged one from an earlier use of the branch name, `gh pr create --base <integration> --title "<subject>" --body-file <file>`, the body `.github/pull_request_template.md` filled for a reader who never saw the review rounds; `<PR>` is the number in the URL it prints.
  3. `gh pr checks <PR> --watch`:
     - every check passed or was skipped: step 4;
     - a check failed or was cancelled: stop for the maintainer, the PR left open;
     - "no checks reported" where a workflow under `.github/workflows/` has a `pull_request` trigger: run it again, up to five times a minute apart; still none, stop for the maintainer;
     - "no checks reported" where no workflow has one: the repository runs no PR CI; the report says so, and step 4 follows;
     - the shell cut the wait off: the PR stays open; read the checks again, and merge nothing on a result nobody read.
  4. `gh pr merge <PR> --squash --delete-branch`. A refused merge (a conflict, a required review) stops for the maintainer, the PR left open.

## 5. Close the issue

1. A pushed `Closes #<issue>` closes the issue only when it lands on the repository's default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`), and a PR merge only into it. Where the work landed on another branch, `gh issue close <issue>` too.
2. Comment with `gh issue comment <issue> --body-file <file>`, quoting at most the hand-back brief's *What changed*: no round tally or finding id.

## 6. Board

Where the settings name a board, `lifecycle board <issue> Done` puts the card in Done, at the top. An untracked task has no card.

## 7. Branches

- A merged feature branch: `--delete-branch` deleted it on GitHub and here, after switching to the integration branch and pulling it. `git fetch --prune` drops its remote-tracking ref. Where gh warned that it could not fast-forward, the integration branch has diverged from its remote: stop, and report `git status -sb`.
- A worktree's own branch stays while its worktree exists, and goes with it: in a linked worktree, gh leaves the local branch.

## 8. Report

One line per step with its coordinates: the issues filed on the kit, the commit, where it was pushed, the PR, the issue's state, the board column. Anything skipped says why.
