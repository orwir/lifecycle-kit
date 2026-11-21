# Changelog

What each kit release changed, newest first.

Format: [Semantic Versioning](https://semver.org/)

Style: one claim per entry, at most 120 characters before the `(#N)`, what a repository on the kit or its maintainer meets (a guide, a template, a skill, a `lifecycle` subcommand, a setting). A semicolon or dash welding a second claim means two entries, not a longer one. Link the issue (`(#N)`, an issue of `orwir/lifecycle-kit`) when the change has one: details live there, not here. A release groups its entries under Added / Changed / Fixed / Removed, each once, below `## [<version>] — <date>`, the day its tag was made. An entry that starts `Repositories:` names a change every repository makes beyond its guides and templates, and its steps are in [UPGRADING.md](UPGRADING.md). A guide push from a project adds its own release. `tests/test_changelog.py` holds every release to this style, and [method/project_kickstart.md § CHANGELOG style](method/project_kickstart.md) is the long form.

---

## [0.7.0] — 2026-11-21

### Changed
- Repositories: docs that credit the kit with refusing a `cd <absolute path>` prefix or a here-string drop that credit (#20)
- The upgrade skill's clean `lifecycle doctor` reading no longer allows for a newer-kit note (#20)
- `docs/guide.md` says how the plugin and a clone of the kit each take a new release (#20)

### Removed
- `lifecycle doctor` no longer asks the kit's remote once a day whether a newer release is out (#20)
- A gist mirror no longer moves onto the kit by its `.gist-revision`: it adopts like any copy (#20)
- The kit's hook no longer refuses a here-string or a `cd <absolute path>` prefix in a session's command (#20)
- `lifecycle guides push` no longer takes `-m` (#20)

## [0.6.0] — 2026-11-21

### Changed
- `lifecycle guides push -F <file>` takes the changelog line and, below it, the reason the kit commit keeps as its body (#19)
- `lifecycle guides push` refuses a message with no line or no reason, or one naming an issue in a form GitHub links (#19)
- The method's README and the complete skill say what a push's reason holds: the gap the edit closes, in the kit's words (#19)

### Removed
- `lifecycle guides push -m`, which the message file replaces (#19)

## [0.5.0] — 2026-11-21

### Added
- `UPGRADING.md` holds the steps each release asks of every repository, which doctor and `lifecycle upgraded` print (#18)

### Changed
- The kit's changelog follows `project_kickstart.md`'s style: dated releases, grouped, one claim per entry (#18)
- `lifecycle doctor` lists each upgrade step a repository owes under its release, oldest release first (#18)
- A kit issue in a session-start note or an *Upgrade* line reads `orwir/lifecycle-kit#N`, never the repository's own (#18)
- `lifecycle guides push` adds a dated release to the kit's changelog with its line under Changed (#18)
- `lifecycle guides push` refuses a line over 120 characters, one that welds a second claim, or one naming an issue (#18)
- `lifecycle upgraded` prints each step a release requires on its own line (#18)

## [0.4.2] — 2026-11-21

### Fixed
- The release workflow recipe's ship job refuses a re-run once the branch has moved or the version is tagged

## [0.4.1] — 2026-11-21

### Changed
- `project_kickstart.md` and `idea_gauntlet.md` send turning the kit on to the kit's `docs/guide.md`
- The kit's setup and settings moved from its README to `docs/guide.md`
- The kit's README is a front page with an install prompt any agent follows

## [0.4.0] — 2026-11-21

### Added
- `lifecycle release <commit>` dispatches the release workflow on a reviewed commit and watches the run (#9)
- `lifecycle release` says why the release workflow refused a run (#9)

### Changed
- Repositories: a production and integration branch pair becomes one `main`, on GitHub and in every clone (#9)
- Repositories: `.lifecycle.toml` drops `[branches] protected` and names a release workflow under `[release]` (#9)
- Repositories: the workflow that ran on a push to the production branch becomes a dispatched `release.yml` (#9)
- Repositories: every other name of the old branches becomes `main`, in workflows, hooks, scripts and docs (#9)
- Repositories: `.claude/settings.json` asks before a release dispatch instead of denying a production push (#9)
- Repositories: an ADR that records the release-PR trigger gets a successor for the release workflow (#9)
- The method keeps one long-lived branch, `main` (#9)
- A release is a version-bump commit on `main`, reviewed on a compare link (#9)
- A dispatched release workflow ships the reviewed commit and creates its tag (#9)
- A hotfix ships from a `hotfix/*` branch cut from the last tag, then merges into `main` with a merge commit (#9)
- `branches.integration` defaults to `main` (#9)
- `branches.protected` is read and ignored until a repository removes it (#9)
- The upgrade skill makes a `Repositories:` change outside the tree first, in a run of its own (#9)
- The upgrade skill makes a change outside the tree only on the maintainer's go-ahead (#9)
- `task_review.md` names the integration branch where it said `develop` (#9)

### Removed
- The release PR, its fast-forward and the hotfix forward-merge (#9)
- `lifecycle guard` (#9)
- Repositories: a push guard, a deploy guard or a branch-sync script, with its tests (#9)

## [0.3.1] — 2026-11-21

### Fixed
- On Windows, a hung kit remote no longer holds `lifecycle doctor` past the release check's 3 s timeout (#6)
- A release check cut off at its timeout stops git and its remote helper instead of leaving them running (#6)

## [0.3.0] — 2026-11-20

### Added
- `[templates]` in `.lifecycle.toml` names the templates a repository follows, each with the file it ports into (#5)

### Changed
- Repositories: a repository whose `AGENTS.md` follows another template lists it under `[templates]` (#5)
- Repositories: `AGENTS.md` drops the sentence that says which template it follows (#5)
- `lifecycle upgrade` replaces and names the templates `[templates]` lists (#5)
- The upgrade skill makes a `Repositories:` change to `.lifecycle.toml` before the upgrade reads the settings (#5)
- On a first move onto the kit, `lifecycle doctor` and `lifecycle upgraded` list every `Repositories:` line (#5)
- The reviewer's guard refuses an option appended to a command that `[review] allow` lists (#5)
- The ideas-home template names its template in `.lifecycle.toml` instead of a sentence in its *Checks* (#5)

## [0.2.2] — 2026-11-20

### Changed
- An ideas home runs `lifecycle doctor` at session start
- An ideas home names the kit's files in its layout
- An ideas home's `AGENTS.md` says which template it follows
- The ideas-home bootstrap names `.lifecycle.toml`

## [0.2.1] — 2026-11-20

### Fixed
- The session-start note shows non-ASCII text whatever the console's code page, instead of crashing on it

## [0.2.0] — 2026-11-20

### Added
- Repositories: `.claude/settings.json` allow-lists `lifecycle upgraded` beside the kit's other read commands
- The briefs' *Upgrade* line says what an upgrade brought
- `lifecycle doctor` lists the kit's changes since the repository's release
- `lifecycle doctor --json` for agents
- `lifecycle upgraded` reads from the tree an upgrade the integration branch lacks
- Once a day, `lifecycle doctor` notes when the kit's remote has a newer release than this machine's kit
- A release states what every repository must change in `Repositories:` lines, which the upgrade skill makes

### Changed
- A repository behind the installed kit upgrades as its task's first step
- `lifecycle doctor` names each finding's fix
- `lifecycle upgrade` replaces the issue and PR templates a repository kept word for word, leaving adapted ones
- The AGENTS template moves board cards with `lifecycle board` (#3)
- The release skill finds the release checklist `AGENTS.md` names (#3)

### Removed
- `lifecycle doctor --require-current`, which the skills replaced with `doctor --json`

## [0.1.0] — 2026-11-20

### Added
- The method, imported from the lifecycle gist at f3b9b7e with its history
- The `lifecycle` command: settings, doctor, upgrade, guide check and push, board, push and deploy guards, agent hooks
- Skills: clarify, review, handback, complete, release, upgrade
- The read-only reviewer agent
- The Claude Code plugin and its marketplace
