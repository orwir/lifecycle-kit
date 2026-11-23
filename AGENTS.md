# Agent instructions — lifecycle-kit

You are working in `orwir/lifecycle-kit`: the maintainer's project lifecycle — the method in `method/`, the `lifecycle` command in `tools/`, and the skills, reviewer and Claude Code adapter over them ([docs/guide.md](docs/guide.md#how-the-kit-is-built)). Every repository on the kit runs what lands here, so a change here is a change to all of them.

**Hard gates:** never commit, push or tag without the maintainer's explicit go-ahead; never bypass hooks with `--no-verify`; never commit or print secrets.

## Commands

- Test: `python -m pytest tests -q -p no:cacheprovider`
- Validate the plugin: `claude plugin validate . --strict`
- Lint: `ruff check tools tests && ruff format --check tools tests`
- The gate, all of the above: `.githooks/pre-push` (`git config core.hooksPath .githooks` once per clone)
- Run the command from a checkout: `bin/lifecycle <subcommand>` (`bin/lifecycle.cmd` from cmd or PowerShell)

## Rules

- **Tools are standard-library Python 3.11+.** No dependency: they run in every repository, in its git hooks and CI, whatever its stack.
- **Mechanics live in the tools, words in the skills.** A step a skill would have an agent re-derive each time — a board move, a version check, a guard — is a `lifecycle` subcommand with a test, and the skill calls it.
- **Skills keep to the portable Agent Skills subset**: `name`, `description`, and the body. A Claude-only field is harmless where others ignore it (`argument-hint`, `disable-model-invocation`), but no step may depend on one.
- **The adapter stays thin.** `.claude-plugin/`, `hooks/` and `bin/` wire the tools into Claude Code and hold no logic of their own.
- **A new file in `method/` needs the justification of a new dependency.** Extend an existing guide first.
- **Repository specifics never enter the kit.** A skill reads them from the repository: structured values from `.lifecycle.toml`, everything else from its `AGENTS.md`.
- Every new behaviour gets a test in `tests/` that fails without it.

## Task workflow

A kit issue runs the two review rounds every repository on the kit runs (`method/task_review.md`), by the kit's own skills: clarify writes the plan into the issue and runs the plan round, review runs the work round, and complete lands the task on the maintainer's go-ahead (Claude: `/lifecycle:clarify <N>`, `/lifecycle:review <N>`, `/lifecycle:complete <N>`). They read this repository's settings from `.lifecycle.toml`, and the method from the installed kit's `method/` (the folder `lifecycle where` prints), the release the rounds run on.

- **The plan** takes the shape of `method/issue_template_task.md`'s *Plan*: the kit keeps no `.github/` copy of it.
- **Labels:** an issue split off or deferred takes `enhancement`, `bug` or `documentation`.
- **The board** is [orwir's project 17](https://github.com/users/orwir/projects/17), named in `.lifecycle.toml`: the skills move its cards with `lifecycle board`, and moving a card from Backlog to Ready, and the order within Ready, are the maintainer's triage call.
- **A task starts on `next`**, where tasks land, while a session's worktree is cut from `main`, the last release. Before a task first reads the code in a fresh worktree — at clarify, as an untracked task's first step, or picking a task up cold — `git fetch origin` and `git rebase origin/next`, then read this file again: the session loaded the release's copy. A tree that holds a task's edits started on `next` already, and its push rebases; a `hotfix/<name>` branch starts at the last release's tag and stays off `next` (§ Releasing). The session start's `lifecycle doctor` notes a fresh branch behind `origin/next`.
- **A task lands on `next`** by the complete skill's plain push, with no release of its own: its entries under `## Unreleased` at the top of `CHANGELOG.md`, and of `UPGRADING.md` where it has steps, with no version bump and no tag. A release ships them (§ Releases).
- **The installed plugin runs the rounds**, not this checkout: `lifecycle doctor` notes when it is older than the release `main` serves, and how to update it. A fix to the method reaches the kit's own rounds once it is released.

## Branching and commits

Work lands on `next`, from a worktree branch or directly, and reaches `main` only by a release (§ Releases). GitHub's default branch stays `main`, which the marketplace serves; no branch is protected. One Conventional Commit per task (`feat:`, `fix:`, `docs:`, `refactor:`), the complete skill saying what its body holds; a release's commit is `chore(release): v<version>`.

## Change → docs

| Change | Also update |
|---|---|
| a `lifecycle` subcommand, its output, or a skill's steps | `README.md` and `docs/guide.md` where they describe them |
| how a repository goes on the kit | `docs/guide.md` § Put a repository on the kit, and the README's install prompt |
| a `.lifecycle.toml` key | `docs/guide.md` § Settings |
| anything a repository picks up | an entry under `## Unreleased` in `CHANGELOG.md`, in the style its header states |
| a change every repository must make beyond its templates | its steps under `## Unreleased` in `UPGRADING.md`, each naming the file it changes, and a `Repositories:` entry in `CHANGELOG.md` |
| a recipe a repository instantiates (a workflow, a hook, a script in `project_kickstart.md`) | a step under `## Unreleased` in `UPGRADING.md` naming the file each repository made from it, never a changelog fix alone |
| a guide added, renamed or removed | its line in `method/README.md` |

## Releases

The version's one home is `.claude-plugin/plugin.json`, and every change that should reach repositories is a release, tagged `v<version>`. The marketplace serves `main`, so `main` holds only released commits. A release ships everything that has landed on `next` since the last one, at the end of a working session or at once for a bug that reaches repositories, and the largest change among them sets its version:

- **patch** — guide wording, a skill or the tools, fixed or clarified: every repository reads it at once, and none owes an upgrade.
- **minor** — a new skill, subcommand or settings-schema change, or anything a repository owes an upgrade for: a template's text or a step in `UPGRADING.md`.
- **major** — a change that breaks what a repository already holds and that no upgrade step can carry, such as a lock or settings file the new kit cannot read.

Repositories stay on their cached copy until the version changes, so a commit without a bump reaches no one.

A change that requires a change in every repository beyond its templates — a setting, a hook, a CI step, a renamed settings key, a file a repository made from a recipe — writes its steps under `## Unreleased` in `UPGRADING.md`, one per line, worded so a repository's agent can make each and naming the file it changes, and says in the CHANGELOG what they do, in entries that start `Repositories:`. The release dates them; `lifecycle doctor` prints the steps a repository owes, and the upgrade skill makes each one.

### Releasing

The release skill runs these steps, in order, on the release branch: `next`, or, for a fix that must ship without what `next` holds, a `hotfix/<name>` branch cut from the last release's tag, wherever the steps name `next`.

1. **The version:** on a branch brought onto `origin/next` as a task starts (§ Task workflow), `git fetch --tags origin`, then by the list above, over what landed since the last tag (`git log v<last>..origin/next`).
2. **The release commit:** the version in `.claude-plugin/plugin.json`; `## Unreleased` renamed `## [<version>] — <date>`, dated the day of this commit, in `CHANGELOG.md` and, where it holds one, `UPGRADING.md`; those files committed by name as `chore(release): v<version>` and pushed with `git push origin HEAD:next`, which ships nothing.
3. **The review** reads the compare link from `v<last>` to the release commit, given as a full SHA. The head it shows holds no `## Unreleased` (`git show <sha>:CHANGELOG.md`, and the same for `UPGRADING.md`): where a correction or a task landed after the release commit, one more commit folds its entries into the release and picks the version again, never a second release commit, and the review reads the new head.
4. **— Checkpoint —** An assistant stops here for the maintainer's explicit "proceed": step 5 ships to every repository on the kit.
5. **Ship the reviewed commit,** not `next`'s head, so whatever landed since waits for the next release: `git tag v<version> <sha>`, then `git push --atomic origin <sha>:refs/heads/main v<version>`. `main` only fast-forwards; a push refused because `main` holds a commit `next` lacks ships nothing, its tag included: delete the local tag (`git tag -d v<version>`), which every worktree shares, and stop for the maintainer.
6. **A hotfix branch** is merged into `next` afterwards, by the release skill.
