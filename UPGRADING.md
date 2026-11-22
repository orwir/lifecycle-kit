# Upgrading

What each kit release asks of every repository on the kit beyond its templates,
newest first, one step per line, each naming the file it changes. `lifecycle doctor`
prints the steps a repository owes, oldest release first, and the upgrade skill makes
them. The release's `Repositories:` entries in [CHANGELOG.md](CHANGELOG.md)
say in one claim each what its steps do.

## [0.10.0] — 2026-11-22

- in every tracked file, `AGENTS.md` and `CONTRIBUTING.md` among them, a pointer at the lifecycle kit's `method/README.md` takes the section's new home, in the form the file already links the kit: § Use in a project becomes the kit's own `docs/guide.md` (`https://github.com/orwir/lifecycle-kit/blob/main/docs/guide.md`), § Bootstrap a new idea becomes `idea_gauntlet.md` § The ideas home, and § Change a guide becomes `task_review.md` § Developer rules (`git grep -n -i -e "use in a project" -e use-in-a-project -e "bootstrap a new idea" -e bootstrap-a-new-idea -e "change a guide" -e change-a-guide` lists them, by heading or slug); accepted ADRs and released CHANGELOG sections stay as written.

## [0.9.0] — 2026-11-22

- in the workflow `[release] workflow` names in `.lifecycle.toml` (`.github/workflows/release.yml` by the recipe), every job that deploys, publishes or tags carries the two refusals of the recipe's `ship` job in `project_kickstart.md` § CI/CD recipe, copied from there word for word: right after the job's checkout and before anything it builds or ships, with the version from `refuse` in `VERSION`, and under the recipe's names, which `lifecycle release` reads. `Refuse a head the review did not read` reads the branch's live head with `git ls-remote`, not `$GITHUB_SHA`, against the reviewed commit, and `Refuse a version released already` reads the version's tag. Both run in bash, with `shell: bash` where the job runs on a Windows runner, since in pwsh they fail on every run and read as a moved branch. Every such job carries them, the build alone not being enough: re-running only the failed jobs keeps the first dispatch's head and skips `refuse` and every job that passed. Where every such job holds both already, nothing changes; a repository with no `[release]` has no step to make.

## [0.8.0] — 2026-11-22

- in `.lifecycle.toml`, where `[templates]` names `"idea_gauntlet.md" = "AGENTS.md"` (an ideas home), it names `"ideas_home_template.md" = "AGENTS.md"` instead.
- in every tracked file, the repository's own guides in the guides folder included (`AGENTS.md` and any nested one, `CONTRIBUTING.md`, `README.md`, `CHANGELOG.md`, `.claude/commands/`, `.claude/rules/`, `docs/` with `docs/README.md` and `docs/reviews/`, `scripts/`, the guides folder's own guides such as `design_language.md`, and an ideas home's idea folders, `archive/` and logs), a link or path to one of the kit's files in the guides folder, in any form (`docs/guides/<file>`, `guides/<file>`, `../guides/<file>`, or a bare `<file>` from a guide beside it), opens the kit's file on GitHub instead, as `https://github.com/orwir/lifecycle-kit/blob/main/method/<file>`: the kit's files are the copies gone from the guides folder once the upgrade skill has run its comparison (those the upgrade's output names deleted, and any older copy removed after it), `git grep -n -F -e <name>` for each name lists the candidates (`README.md` only where it follows `guides/`), and a link to a guide still in the folder, the repository's own, stays.
- in `AGENTS.md`, `CONTRIBUTING.md` and any other doc that says it (such as `docs/README.md`), a sentence that says the guides folder holds a copy of the lifecycle kit's method, or that a guide edit is pushed to the kit at Complete (`lifecycle guides push`), says instead that the kit's guides are read from the installed kit, and that a gap found in one is filed on the kit as an issue when it is found.
- in `.claude/settings.json`, the allow rules for `lifecycle guides check` and `lifecycle upgraded` go, and where it allow-lists the kit's other reads, `Bash(lifecycle where:*)` joins them.

## [0.7.0] — 2026-11-21

- in `AGENTS.md` and `CONTRIBUTING.md`, a sentence that only credits the lifecycle kit, its plugin or its hook with refusing a `cd <absolute path>` prefix or a PowerShell here-string goes, and one that holds a rule as well keeps the rule and drops the credit: the rule stays where the repository already states it, with its own reason, and names no machine's hook.

## [0.4.0] — 2026-11-21

- on GitHub and in every clone (its `.git/config`), a repository with a production branch and an integration branch moves to one `main`, as its own upgrade run alone: a task in flight waits with its files in the tree, and nothing else lands until the release that ends the move. `git fetch --prune origin`, then check that `origin/<production>` is an ancestor of `origin/<integration>`; where it is not, stop and list `git log origin/<integration>..origin/<production>`. On the maintainer's go-ahead, delete the production branch on GitHub, rename the integration branch to `main` there, and let a GitHub environment that limits deployments to the production branch take `main` and `hotfix/*`. In each clone: `git branch -D <production>`, `git branch -m <integration> main`, `git fetch --prune origin`, `git branch -u origin/main main`, `git remote set-head origin -a`. Land the rest of this release's lines on `main`. The release that ends the move is the maintainer's to ask for; as the first through the new workflow, the release skill probes the workflow before it ships.
- in `.lifecycle.toml`, delete `protected` under `[branches]`, set `integration = "main"` where the first step moved the repository to `main`, and add `[release]` with `workflow = "release.yml"` where the repository ships releases by a workflow.
- in `.github/workflows/`, the workflow that ran on a push to the production branch becomes `release.yml` by `project_kickstart.md` § CI/CD recipe: dispatched on the reviewed commit, its refusal steps named as there, one run at a time, the tag created last. A check that ran only on the release PR moves into it, a job that guarded the production branch goes, and `ci.yml` runs on pushes to the integration branch.
- where the first step moved the repository to `main`, in `.github/workflows/`, the git hooks (`.pre-commit-config.yaml` or `.githooks/`), `scripts/`, `README.md` and `docs/` outside `docs/adr/`, every other name of the old branches becomes `main` (`origin/develop`, badges and links included), and a push guard, a deploy guard or a branch-sync script is deleted with its tests.
- in `.claude/settings.json`, a rule that denies a push to the production branch becomes one that asks before `gh workflow run`, `lifecycle release` and `bin/lifecycle release`.
- an ADR in `docs/adr/` that records the release-PR trigger gets a successor ADR for the release workflow; the accepted one is not edited.

## [0.3.0] — 2026-11-20

- where `AGENTS.md` follows a template other than `agents_template.md` (an ideas home follows `idea_gauntlet.md`), list each template the repository follows, with the file it ports into, under `[templates]` in `.lifecycle.toml`, and drop the sentence in `AGENTS.md` that says which template it follows.

## [0.2.0] — 2026-11-20

- where `.claude/settings.json` allow-lists the kit's read commands, add `Bash(lifecycle upgraded:*)` beside them.
