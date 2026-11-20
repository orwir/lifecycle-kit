# Agent instructions — lifecycle-kit

You are working in `orwir/lifecycle-kit`: the maintainer's project lifecycle — the method in `method/`, the `lifecycle` command in `tools/`, and the skills, reviewer and Claude Code adapter over them ([README.md](README.md)). Every repository on the kit runs what lands here, so a change here is a change to all of them.

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

## Releases

The version's one home is `.claude-plugin/plugin.json`, and every change that should reach repositories is a release, tagged `v<version>`:

- **patch** — guide wording; `lifecycle guides push` cuts these from a project.
- **minor** — a skill, the settings schema, a template, or anything else a repository must upgrade to before its next review round.
- **major** — a change a repository cannot take by `lifecycle upgrade` alone.

Repositories stay on their cached copy until the version changes, so a commit without a bump reaches no one. A project's guide push refuses while `main` has commits after its release's tag, since its patch would ship them: release what is on `main` before projects push again.
