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
- **Repository specifics never enter the kit.** A skill reads them from the repository: structured values from `.lifecycle.toml`, everything else from its `AGENTS.md`.
- Every new behaviour gets a test in `tests/` that fails without it.

## Task workflow

A kit issue runs the two review rounds every repository on the kit runs (`method/task_review.md`), by the kit's own skills: clarify writes the plan into the issue and runs the plan round, review runs the work round, and complete lands the task on the maintainer's go-ahead (Claude: `/lifecycle:clarify <N>`, `/lifecycle:review <N>`, `/lifecycle:complete <N>`). They read this repository's settings from `.lifecycle.toml`, and the method from the installed kit's `method/` (the folder `lifecycle where` prints), the release the rounds run on.

- **The plan** takes the shape of `method/issue_template_task.md`'s *Plan*: the kit keeps no `.github/` copy of it.
- **Labels:** an issue split off or deferred takes `enhancement`, `bug` or `documentation`. There is no board.
- **The release** rides the task's diff: the version in `.claude-plugin/plugin.json` and its CHANGELOG section (§ Releases). At *Complete* it replaces the plain push to `main`: rebase onto `origin/main`, date the release's heading with the day it is tagged, in `CHANGELOG.md` and, where the release has steps, in `UPGRADING.md`, amended into the task's commit, tag `HEAD` `v<version>`, then `git push --atomic origin HEAD:main v<version>`, so `main` never holds a commit no release's tag carries. A push refused because `main` moved: `git tag -d v<version>`, rebase, date and tag again, push again.
- **The installed plugin runs the rounds**, not this checkout: `lifecycle doctor` notes when it is older than the release on `main`, and how to update it.

## Branching and commits

Work lands on `main`, from a worktree branch or directly; no branch is protected. One Conventional Commit per task (`feat:`, `fix:`, `docs:`, `refactor:`); the complete skill says what its body holds.

## Change → docs

| Change | Also update |
|---|---|
| a `lifecycle` subcommand, its output, or a skill's steps | `README.md` and `docs/guide.md` where they describe them |
| how a repository goes on the kit | `docs/guide.md` § Put a repository on the kit, and the README's install prompt |
| a `.lifecycle.toml` key | `docs/guide.md` § Settings |
| anything a repository picks up | an entry under the release in `CHANGELOG.md`, in the style its header states |
| a change every repository must make beyond its templates | its steps under the release in `UPGRADING.md`, each naming the file it changes, and a `Repositories:` entry in `CHANGELOG.md` |
| a recipe a repository instantiates (a workflow, a hook, a script in `project_kickstart.md`) | a step under the release in `UPGRADING.md` naming the file each repository made from it, never a changelog fix alone |
| a guide added, renamed or removed | its line in `method/README.md` |

## Releases

The version's one home is `.claude-plugin/plugin.json`, and every change that should reach repositories is a release, tagged `v<version>`:

- **patch** — guide wording, a skill or the tools, fixed or clarified: every repository reads it at once, and none owes an upgrade.
- **minor** — a new skill, subcommand or settings-schema change, or anything a repository owes an upgrade for: a template's text or a step in `UPGRADING.md`.
- **major** — a change that breaks what a repository already holds and that no upgrade step can carry, such as a lock or settings file the new kit cannot read.

Repositories stay on their cached copy until the version changes, so a commit without a bump reaches no one.

A release that requires a change in every repository beyond its templates — a setting, a hook, a CI step, a renamed settings key, a file a repository made from a recipe — writes its steps under the release's heading in `UPGRADING.md`, one per line, worded so a repository's agent can make each and naming the file it changes, and says in the CHANGELOG what they do, in entries that start `Repositories:`. `lifecycle doctor` prints the steps a repository owes, and the upgrade skill makes each one.
