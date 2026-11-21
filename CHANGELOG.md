# Changelog

What each kit release changed, newest first. A guide push from a project adds its own line.

## v0.4.1

- `project_kickstart.md` and `idea_gauntlet.md` send turning the kit on to the kit's `docs/guide.md`, where its setup and settings moved.
- The kit's README is a front page with an install prompt any agent follows.

## v0.4.0

- Repositories: on GitHub and in every clone (its `.git/config`), a repository with a production branch and an integration branch moves to one `main`, as its own upgrade run alone: a task in flight waits with its files in the tree, and nothing else lands until the release that ends the move. `git fetch --prune origin`, then check that `origin/<production>` is an ancestor of `origin/<integration>`; where it is not, stop and list `git log origin/<integration>..origin/<production>`. On the maintainer's go-ahead, delete the production branch on GitHub, rename the integration branch to `main` there, and let a GitHub environment that limits deployments to the production branch take `main` and `hotfix/*`. In each clone: `git branch -D <production>`, `git branch -m <integration> main`, `git fetch --prune origin`, `git branch -u origin/main main`, `git remote set-head origin -a`. Land the rest of this release's lines on `main`. The release that ends the move is the maintainer's to ask for; as the first through the new workflow, the release skill probes the workflow before it ships.
- Repositories: in `.lifecycle.toml`, delete `protected` under `[branches]`, set `integration = "main"` where it names another branch, and add `[release]` with `workflow = "release.yml"` where the repository ships releases by a workflow.
- Repositories: in `.github/workflows/`, the workflow that ran on a push to the production branch becomes `release.yml` by `project_kickstart.md` § CI/CD recipe: dispatched on the reviewed commit, its refusal steps named as there, one run at a time, the tag created last. A check that ran only on the release PR moves into it, a job that guarded the production branch goes, and `ci.yml` runs on pushes to `main`.
- Repositories: in `.github/workflows/`, the git hooks (`.pre-commit-config.yaml` or `.githooks/`), `scripts/`, `README.md` and `docs/` outside `docs/adr/`, every other name of the old branches becomes `main` (`origin/develop`, badges and links included), and a push guard, a deploy guard or a branch-sync script is deleted with its tests.
- Repositories: in `.claude/settings.json`, a rule that denies a push to the production branch becomes one that asks before `gh workflow run`, `lifecycle release` and `bin/lifecycle release`.
- Repositories: an ADR in `docs/adr/` that records the release-PR trigger gets a successor ADR for the release workflow; the accepted one is not edited.
- The method keeps one long-lived branch, `main`: the release PR, its fast-forward and the hotfix forward-merge are gone.
- A release is a version-bump commit on `main`, reviewed on a compare link, then shipped by a dispatched workflow that creates the tag.
- `lifecycle release <commit>` dispatches the release workflow on a reviewed commit, watches the run and says why it was refused.
- A hotfix ships from a `hotfix/*` branch cut from the last tag, then merges into `main` with a merge commit, never squashed.
- `lifecycle guard` is gone: a push ships nothing, so no branch is left to guard.
- `branches.integration` defaults to `main`, and `branches.protected` is read and ignored until a repository removes it.
- The upgrade skill makes a `Repositories:` change outside the tree first, in a run of its own, on the maintainer's go-ahead.
- `task_review.md` names the integration branch where it said `develop`.

## v0.3.1

- On Windows, a hung kit remote no longer holds `lifecycle doctor` and the session-start note past the release check's 3 s timeout.
- A release check cut off at its timeout stops git and its remote helper instead of leaving them running.

## v0.3.0

- Repositories: where `AGENTS.md` follows a template other than `agents_template.md` (an ideas home follows `idea_gauntlet.md`), list each template the repository follows, with the file it ports into, under `[templates]` in `.lifecycle.toml`, and drop the sentence in `AGENTS.md` that says which template it follows.
- `.lifecycle.toml` names the templates a repository follows under `[templates]`, and `lifecycle upgrade` replaces and names those, each with the file it ports into.
- The upgrade skill makes a `Repositories:` change to `.lifecycle.toml` before the upgrade reads the settings.
- On a first move onto the kit, `lifecycle doctor` and `lifecycle upgraded` list every `Repositories:` line up to the release.
- The reviewer's guard refuses an option appended to a command `[review] allow` lists, so a read-only check cannot become a write.
- The ideas-home template names its template in `.lifecycle.toml` instead of a sentence in its *Checks*.

## v0.2.2

- An ideas home runs lifecycle doctor at session start, names the kit's files in its layout, and says which template its AGENTS.md follows; the bootstrap names .lifecycle.toml

## v0.2.1

- `lifecycle` writes UTF-8 whatever the console's code page, so the session-start note shows non-ASCII text and cannot crash on it.

## v0.2.0

- Repositories: where `.claude/settings.json` allow-lists the kit's read commands, add `Bash(lifecycle upgraded:*)` beside them.
- A repository behind the installed kit upgrades as the task's first step, and the brief's new Upgrade line says what it brought.
- `lifecycle doctor` names each finding's fix and lists the kit's changes since the repository's release; `--json` for agents.
- `lifecycle upgraded` reads an upgrade the integration branch lacks from the tree, so a task that spans sessions still lands it.
- Removed `lifecycle doctor --require-current`: the skills now read `doctor --json`.
- Once a day, `lifecycle doctor` asks the kit's remote for its newest release and notes when this machine's kit is older.
- A release states what every repository must change in `Repositories:` lines, which the upgrade skill applies.
- `lifecycle upgrade` replaces issue and PR templates a repository kept word for word, leaving adapted ones to port.
- The AGENTS template moves board cards with `lifecycle board`; the release skill finds the checklist AGENTS.md names.

## v0.1.0

- The method, imported from the lifecycle gist at f3b9b7e with its history.
- The `lifecycle` command: settings, doctor, upgrade, guide check and push, board, push and deploy guards, agent hooks.
- Skills: clarify, review, handback, complete, release, upgrade; the read-only reviewer agent.
- The Claude Code plugin and its marketplace.
