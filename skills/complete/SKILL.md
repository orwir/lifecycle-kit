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

`lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit. `lifecycle config` gives the integration branch (`branches.integration`), the gate (`gate.commands`) and whether there is a board. Read AGENTS.md § Task workflow too, and do any step it adds or replaces (a check before the push, a push in place of the plain one) where it says.

## 1. Before anything lands

1. **The hand-back's answers,** by `task_review.md` § The work round, step 5: each answer to the hand-back's D-rows given with this go-ahead or before it; each D-row left unanswered, which takes its recommendation, written as taken at the go-ahead; each choice taken alone the maintainer vetoed. The gate runs again after them. A pick bigger than the size its option stated, or any veto, stops the batch: render the brief again by the handback skill and wait for a new go-ahead. A `Watch:` line the maintainer named is no veto: § 2 files it.
2. **The gate** — `gate.commands`, else AGENTS.md § Commands' lint and tests — passed in this session after the last edit; if not, run it now. A red gate stops the batch. A repository with no gate says so in the report.
3. `git status --short` lists only this task's files. Anything else is someone's in-progress work: leave it out and name it in the report.

## 2. Kit gaps and named `Watch:` lines

Each `Watch:` line the maintainer named in the hand-back is filed now, the way an issue past the bar is filed (`task_review.md` § Developer rules): a gap in a kit guide by `lifecycle gap`, any other as a capture labelled as AGENTS.md says, with `lifecycle board <new> Backlog` where the settings name a board; its reference, marked named, takes the line's place in the plan.

A gap this task found in a kit guide was filed by `lifecycle gap` when it was found (`task_review.md` § Developer rules), and the hand-back's *Taken alone* names it. Each gap not filed — a `Not filed:` entry in the plan, or in an untracked task's hand-back — is filed now, by `lifecycle gap --title <its title> --body-file <its body>`, the body in a file outside the tree (`task_review.md` § Developer rules), and its reference replaces the plan's entry; one `lifecycle gap` still cannot file stays where it is, and the report gives its title and why. Nothing of the kit's lands from this repository.

## 3. Commit

1. Stage the task's files by name; never `git add -A`.
2. One Conventional Commit (AGENTS.md § Branching and commits): the body says why, names every decision taken alone with its reason (the plan's `Taken:` lines, the hand-off's and the hand-back's), every departure, every `Watch:` line still standing, each answer to the hand-back and each spend with its amount, and ends `Closes #<issue>` on a tracked task. A fix for an exploitable finding in released code keeps its location and detail out of every public record `task_review.md` § Return packet lists, until its fix ships.
3. The message goes in a file in a scratch folder outside the tree, passed with `-F`.
4. A failing hook is fixed at its cause and the commit made again; never `--no-verify`, never amend a pushed commit.
5. A hook that passed but printed that a check did not run, its tool missing, is no failure: here or at the push, its line is kept for the report (§ 8).

## 4. Land

Where the shell's interpreter is not the project's, put the project's environment first on `PATH` for the commit and the push: its hooks run its own tools (AGENTS.md § Commands).

- **On the integration branch, or a worktree branch whose work lands on it directly:** `git push origin HEAD:<integration>`, or the push AGENTS.md § Task workflow gives in its place. The pre-push hook runs the gate. A push refused because the branch moved: `git fetch origin`, rebase onto `origin/<integration>`, push again; a conflict stops for the maintainer. Then *The primary checkout follows*, and the push's CI, below, on `<integration>`.
- **On a `hotfix/<name>` branch:** `git push -u origin <branch>`, then the push's CI, below, on the branch, and nothing more: no PR and no merge. Write § 5's comment, naming the branch and the CI's last line, and skip the rest of §§ 5 to 7: the release reads that CI again and ships the branch, its merge into the integration branch closes the issue by its `Closes #<issue>`, and the release skill moves the card and deletes the branch.
- **On a feature branch:**
  1. `git push -u origin <branch>`.
  2. `gh pr view <branch> --json number,state`: an `OPEN` PR is `<PR>`. With none, or only a closed or merged one from an earlier use of the branch name, `gh pr create --base <integration> --title "<subject>" --body-file <file>`, the body `.github/pull_request_template.md` filled for a reader who never saw the review rounds; `<PR>` is the number in the URL it prints.
  3. `lifecycle ci --pr <PR>` waits on the PR's checks, with up to five reads a minute apart where a workflow runs on its pull requests but no check has appeared yet. Its last line says how it ended, and its exit code matches:
     - 0, `passed`, or `no PR CI` where no workflow runs on its pull requests: step 4;
     - 1 with `failed` (a check failed or was cancelled), or 3, `missing` (no check appeared): stop for the maintainer, the PR left open;
     - 1 with a `lifecycle:` line (a read that failed: unread, not red), 4, `running`, or a last line of `ci: waiting on …` or none at all (the shell cut the wait off): the PR stays open; read its checks again by the same command, and merge nothing on a result nobody read.
  4. `lifecycle merge <PR>` squash-merges it, reads how that ended from the PR's state, never from gh's exit code, then deletes its branch on GitHub and here wherever nothing on it is lost, a line per step: run it where a long command may run. Its exit code says how it ended:
     - 0, merged, whatever the cleanup did: its lines go in the report. Then *The primary checkout follows*, below;
     - 1 with a line saying the PR is not merged (a conflict, a required review, a closed PR): stop for the maintainer, the PR left as it is;
     - 1 with a `lifecycle:` line, or no line at all (the shell cut it off): the PR's state is unread, never refused. Run it again, which reads the state first and merges only a PR still open. Still unread, the batch stops before § 5: the report gives the PR's link and that command, and once it reads, on the maintainer's go-ahead, this skill goes on from that reading.

**The primary checkout follows.** Once the work is on the integration branch (the direct push accepted, or the PR merged, which `lifecycle merge` fetched, since the merge happened on GitHub; where it printed that its fetch failed, `git fetch origin` first, and a failure of that goes in the report), `lifecycle tidy` fast-forwards the primary checkout's integration branch to origin's where git allows it, and lists the linked worktrees whose own work has landed and the landed branches no checkout holds. Its first line and its last go in the report; a refusal it prints (exit 1) is that line, and the batch goes on, the landing standing. It removes nothing: `lifecycle tidy --remove` runs only on the maintainer's word, since another session may still have a landed worktree open.

**The push's CI:** `lifecycle ci <the pushed commit> --ref <branch>` waits on the CI that push started, for as long as it runs: run it where a long command may run, in the background where you can. Its last line says how it ended, and its exit code matches:

- 0, `passed`, or `no CI` where no workflow runs on a push to the branch; 3, `missing` (CI is expected, but no run appeared, a `paths` filter skipping it most often); 5, `superseded` (a later push to the branch cancelled its run, the line naming that push's run): § 5 follows, and the report carries the line;
- 1 with `failed`: the task is held, by § 5's *A red push*;
- 1 with a `lifecycle:` line (a read that failed), 4, `running`, or a last line of `ci: waiting on …` or none at all (the shell cut the wait off): CI is unread, never red. Read it again by the same command, and go on by its outcome as above. Still unread, the batch stops before § 5: the report gives each run's link and that command, and once it reads, on the maintainer's go-ahead, this skill goes on from that reading.

## 5. Close the issue

1. A pushed `Closes #<issue>` closes the issue only when it lands on the repository's default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`), and a PR merge only into it. Where the work landed on another branch, `gh issue close <issue>` too.
2. Comment with `gh issue comment <issue> --body-file <file>`, quoting at most the hand-back brief's *What changed*: no round tally or finding id.

**A red push** holds the task, landed but not done, whether its own change turned CI red or it landed on a branch red already. In place of steps 1 and 2 (an untracked task has no issue or card: its report names the failure):

1. Where its `Closes #<issue>` closed the issue on the default branch, `gh issue reopen <issue>`.
2. Comment, as in step 2, with each failed job, step and link from `lifecycle ci`'s line.
3. Where the settings name a board, `lifecycle board <issue> "In Progress"`; §§ 6 and 7 are skipped.

The fix is the maintainer's next call: a fix landed through the task workflow, or the run re-run where its failure was not the commit's (`gh run rerun <id> --failed`). Once `lifecycle ci <the branch's head> --ref <branch>` reads 0, on the maintainer's go-ahead, this skill goes on as § 4 sends the branch: from § 5 on the integration branch; on a hotfix branch, § 5's comment alone, its issue left open and its card where it is for the release.

## 6. Board

Where the settings name a board, `lifecycle board <issue> Done` puts the card in Done, at the top. An untracked task has no card.

## 7. Branches

- A merged feature branch: `lifecycle merge` deleted it on GitHub while it was still at the PR's head, and here where its tip was that head and no linked worktree holds it, switching the primary checkout it ran in to the integration branch first, and pruned its remote-tracking ref. A branch it left, it named with why: one at another commit than the PR's head stays for the maintainer.
- A linked worktree's own branch stays while its worktree exists, and goes with it, by `lifecycle tidy --remove` on the maintainer's word (§ 4); a branch no checkout holds, such as the one a worktree left when an archive detached it, goes by the same `--remove` once its own work has landed. A squash merge leaves the branch's commits off the integration branch, so tidy keeps that worktree, naming why, and `lifecycle merge` leaves its branch, saying so: both go by `git worktree remove <path>` and `git branch -D <branch>`, on the maintainer's word.

## 8. Report

One line per step with its coordinates: the named `Watch:` lines and the kit gaps filed, each where it landed, and any left unfiled with why, the commit, each line a hook printed saying a check did not run, where it was pushed, the PR and `lifecycle merge`'s lines, `lifecycle tidy`'s first and last lines, `lifecycle ci`'s last line on the push or the PR's checks, the issue's state, the board column. Anything skipped says why.
