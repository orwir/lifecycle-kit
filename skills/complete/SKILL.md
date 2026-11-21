---
name: complete
description: Close out a task on the maintainer's explicit go-ahead ("lgtm", "complete the task") — guides to the kit, commit, push, close the issue, board to Done at the top, delete a merged branch
argument-hint: "[issue number; empty for an untracked task]"
---

Task: $ARGUMENTS — the issue number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named).

This is the *Complete* phase of AGENTS.md § Task workflow. It runs only on the maintainer's explicit go-ahead to complete this task, in their own latest message: "complete the task", "lgtm", "ship it" or the like. "go", "proceed", "start" or "implement" authorize code, never landing, and an earlier approval covers only what it named. Without one, stop and ask. With one, every step below runs as one batch, with no prompt between steps.

`lifecycle` is the kit's command (on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit); `lifecycle config` gives the integration branch (`branches.integration`), the gate (`gate.commands`) and whether there is a board. Read AGENTS.md § Task workflow too: a repository may add a step here or replace one (a release tag pushed with the work), and you do it where it says.

## 1. Before anything lands

- The gate — `gate.commands`, else AGENTS.md § Commands' lint and tests — passed in this session after the last edit; if not, run it now. A red gate stops the batch. A repository with no gate at all says so in the report.
- `git status --short` lists only this task's files, and an upgrade's when `lifecycle upgraded` reports one, the files its upgrade steps name included. Anything else is someone's in-progress work: leave it out and name it in the report.

## 2. Guides

When `lifecycle guides check` lists guides this task changed: write the push's message file in a scratch folder outside the tree and run `lifecycle guides push -F <file>`. Its first line is the line: the patch's entry in the kit's changelog, so it follows that changelog's style, one claim of at most 120 characters, no reason, no issue. Below a blank line comes the reason, the kit commit's body: the gap or failure the edit closes, which the task's plan or hand-back holds. Write both in the kit's words, as § Change a guide of the `README.md` in the guides folder (`lifecycle config` → `guides.path`) says: every repository on the kit reads the line in its session-start notes and *Upgrade* lines, so neither names the project's own issue or surface. The push refuses a line over the cap, one with a semicolon or a lone dash, a file with no line or no reason, and an issue in either in a form GitHub links; the rule is no issue at all. It replays each edit onto the kit's latest from the release its copy came from and releases them as a patch; a conflict stops the batch for the maintainer before anything lands. A pushed guide takes the released text, with any change another project made to it meanwhile, and `.lifecycle.lock` records the release: both ride the task's commit. A guide edit is never left unpushed past this step.

## 3. Commit

- When `lifecycle upgraded` reports an upgrade in the tree, it is the first commit: `.lifecycle.lock`, the guides and installed templates it lists, the files it ported into, and the files its `required` changes name, staged by name, as `docs(guides): upgrade to kit <release>`. It rides the task's commit instead where the task also changed one of those files or the upgrade carried the task's guide edits, and on a feature branch it rides the squash merge; the task's commit body or PR body then says so. A session that did not run the upgrade cannot tell a port from the task's own change to a file a template ports into (`lifecycle config` → `templates`): there, a changed file whose template the upgrade rewrote rides the task's commit. Guides it lists as deleted are staged with it.
- Stage the task's files by name, the pushed guides and `.lifecycle.lock` among them when step 2 ran; never `git add -A`.
- One Conventional Commit (AGENTS.md § Branching and commits): the body says why, names every decision taken alone and every departure, and ends `Closes #N` on a tracked task. Write the message to a file in a scratch folder outside the tree and pass it with `-F`.
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

- A merged feature branch: `git checkout <integration> && git pull && git branch -d <branch> && git fetch --prune`. `--delete-branch` removed only the remote copy.
- A worktree's own branch stays while its worktree exists, and goes with it.

## 8. Report

One line per step with its coordinates: the kit release the guides went out in, with the line it carried and its reason quoted below that step's line, the commit, where it was pushed, the PR, the issue's state, the board column. Anything skipped says why. After a guide push, the repository's next upgrade waits until the installed kit holds the release it made.
