# Changelog

What each kit release changed, newest first.

Format: [Semantic Versioning](https://semver.org/)

Style: one claim per entry, at most 120 characters before the `(#N)`, what a repository on the kit or its maintainer meets (a guide, a template, a skill, a `lifecycle` subcommand, a setting). A semicolon or dash welding a second claim means two entries, not a longer one. Link the issue (`(#N)`, an issue of `orwir/lifecycle-kit`) when the change has one: details live there, not here. A release groups its entries under Added / Changed / Fixed / Removed, each once, below `## [<version>] — <date>`, the day its release commit was made; a task's entries wait under `## Unreleased` at the top until a release dates them. An entry that starts `Repositories:` names a change every repository makes beyond its templates, and its steps are in [UPGRADING.md](UPGRADING.md). `tests/test_changelog.py` holds every release to this style, and [method/project_kickstart.md § CHANGELOG style](method/project_kickstart.md) is the long form.

---

## Unreleased

### Fixed
- `lifecycle home` takes back all a failed or timed-out setup wrote or staged, on Linux and macOS too (#58)
- An upgrade leaves accepted ADRs, released changelog sections and frozen records as written, whatever a step lists (#42)

## [0.17.1] — 2026-11-23

### Changed
- A kit release ships every task landed on `next` since the last one, not one release per task (#54)

## [0.17.0] — 2026-11-23

### Added
- `lifecycle board setup` creates a board or fixes one in place, keeping each Status option's id, so no card loses it (#53)
- `lifecycle board setup` links the repository and puts its open issues, and cards with no Status, in their column (#53)
- `lifecycle board setup` names each built-in workflow to turn on or confirm in the web UI, with its value (#53)

### Changed
- The kickstart's Ready is triaged and ordered, the top card next: its order is the plan, with no milestone (#53)
- The kickstart keeps a milestone only for a release whose scope something outside the project fixes (#53)
- The kickstart makes a board optional, kept where the open issues outnumber what one maintainer holds in mind (#53)
- The kickstart's board keeps the Item closed, Item added, Auto-add and Auto-archive workflows on (#53)
- The kickstart's board takes no custom field by default (#53)
- The CONTRIBUTING template's release checklist has no milestone steps: a release ships what has landed (#53)
- The AGENTS template files an issue into no milestone (#53)
- The AGENTS template reads Ready's order as the plan, the top card next (#53)
- The issue templates keep work state on the board where the repository keeps one, otherwise in the issue (#53)
- `lifecycle board` brings an archived card back when it moves one (#53)
- Repositories: a repository's own milestone steps stay in `CONTRIBUTING.md` only while a milestone holds open work (#53)
- Repositories: a repository with a board runs `lifecycle board setup` on it, then sets its workflows in the web UI (#53)

## [0.16.0] — 2026-11-23

### Added
- The capture skill interviews a person about a new idea, one plain question at a time, into their ideas home (#36)
- `lifecycle home` sets up an ideas home in a folder, in one commit (#36)
- `lifecycle home --check` names the home it finds, or the folder a new one would go in (#36)
- `lifecycle home --github` backs an ideas home up to a new private GitHub repository (#36)

### Changed
- The ideas home template's Capture takes its answers by the capture skill (#36)
- The ideas home template's Capture never writes over an idea already in `active/` under the same name (#36)
- An ideas home pushes where it has a remote, and stays on its machine where it has none (#36)
- The gauntlet sets an ideas home up by `lifecycle home`, which writes its lock, in place of the upgrade skill (#36)

## [0.15.0] — 2026-11-22

### Added
- `lifecycle gap` files a gap in a kit guide on the kit, or here labelled `kit-gap` where you cannot push to the kit (#35)

### Changed
- Every guide, skill and template files a gap in a kit guide, or a reusable pattern, with `lifecycle gap` (#35)
- A gap no issue could be filed for waits in the task's plan as a `Not filed:` entry until a later filing (#35)
- A `kit-gap` issue in a repository takes none of its own issue rules: no template, no label from its list, no card (#35)
- Repositories: a sentence that files a kit-guide gap on the kit files it with `lifecycle gap` instead (#35)

## [0.14.4] — 2026-11-22

### Changed
- The idea gauntlet fits a game: a `[game]` line under an item asks what a game is judged on (#17)
- The gauntlet's Phase 0 asks for an idea's type with its appetite, before its other questions (#17)

## [0.14.3] — 2026-11-22

### Changed
- The kit's repository is public, under the MIT license (#14)

### Removed
- Putting a repository on the kit no longer sets up git's credential helper (#14)

## [0.14.2] — 2026-11-22

### Fixed
- Each change line `lifecycle doctor` shows opens with its group, so a removal no longer reads as a feature (#23)

## [0.14.1] — 2026-11-22

### Changed
- A reviewer's return opens with the count of its required findings and their ids, in place of the verdict (#33)
- A finding in a return is a short block: id, severity and location, then a line each for claim, evidence and action (#33)
- A finding marks its evidence `seen` or `inferred` (#33)
- A return's paths are relative to the repository root (#33)
- The developer reads every location a finding cites before acting on it, and disputes one that does not hold (#33)
- An `inferred` finding is proven before its fix: by a search, a failing test, or the run or read that shows it (#33)
- A dispute is on evidence or on scope, and the plan round's mark and both briefs' *Reviewed* name its kind (#33)

### Removed
- The reviewer's verdict and the findings table (#33)

## [0.14.0] — 2026-11-22

### Changed
- A brief opens with the issue's link, the task in plain words and its goal, then what you do next (#32)
- A brief shows the plan, or what changed, before its questions (#32)
- A brief keeps a blank line between blocks and between questions, so a chat never runs them together (#32)
- A D-row puts its question, each option and the recommendation on lines of their own (#32)
- A choice you haven't made is a D-row only when it is a one-way door: user-visible, hard to undo, scope or spend (#32)
- A two-way choice, a reviewer's included, is taken and written into the plan as a `Taken:` line, open to veto (#32)
- *Taken alone* shows only the choices that might draw your attention, and every follow-up filed (#32)
- A brief's *Reviewed* line says what the round asked for and what became of it, never the verdict (#32)
- A hand-back names each spend, its amount and where it was asked, and so does the commit (#32)
- A brief's size is about 400 words, not a count of lines (#32)
- A hand-back always says how many tests fail without the change, a zero in words with its reason (#32)
- The hand-back's *In the tree* is *What changed*, and both briefs' *Visible* is *You see* (#32)
- The task and bug templates' *Decisions* hold the one-way doors and a `Taken:` line per choice taken alone (#32)
- A plan round's mark carries what it required in place of the verdict (#32)

### Removed
- The briefs' status line, *Round* and *Next*, whose content moves to *For you* and *Reviewed* (#32)
- The Clarify brief's *Seams*, which stays in the plan (#32)
- *Taken alone*'s five-row cap (#32)

## [0.13.1] — 2026-11-22

### Added
- The sections the guides, skills, reviewer and upgrade steps cite are held by a test to exist

## [0.13.0] — 2026-11-22

### Changed
- The AGENTS template's *Clarify* points to `task_review.md` for when a plan is accepted without "go" (#30)

### Fixed
- A drawn plan waits for "go" in every repository's contract, as the guide and the clarify skill say (#30)
- The Clarify brief says "going ahead" only for a skipped round's plan with no drawing (#30)

## [0.12.2] — 2026-11-22

### Changed
- Each skill's steps hold one rule per line, each with what to do when it fails (#25)
- The skills cite `task_review.md` for the packet, brief, drawing and departures rules (#25)
- The review skill holds the three ways to launch a reviewer, and the clarify skill points at it (#25)
- A plan whose round ran is marked `proposed, plan round <date>: …`, so a cold session renders its brief (#25)
- "ship it" is a go-ahead for neither the complete nor the release skill, which each ask (#25)
- The upgrade skill accounts for every step and template doctor listed before its hand-back (#25)

### Fixed
- The review and handback skills tell a PR number from an issue's and find the issue a PR closes (#25)
- The complete skill opens a PR only where no open one exists (#25)
- The complete skill's wait on a PR's checks has an else for each outcome (#25)
- A refused push fetches before it rebases (#25)
- The release skill counts only dispatched runs to tell a workflow's first release (#25)
- A hotfix merge that conflicts only in `CHANGELOG.md` keeps both sections (#25)
- The reviewer definition sends only a lens reviewer to `review.lenses` (#25)
- The reviewer definition allows a formatter in check mode that `review.allow` lists (#25)

## [0.12.1] — 2026-11-22

### Changed
- `task_review.md` defines its terms once, at its top (#28)
- `task_review.md` gives a task's action for each of the seven severities in one table (#28)
- A reviewer's second read in the work round is a second pass: only the plan and work rounds are rounds (#28)
- A D-row left open at "go" or "lgtm" takes its recommended option (#28)
- A task defers a `Drift-prone` finding to a filed issue, with its trigger and plan (#28)
- An exploitable finding is fixed in the task or reported privately, never filed as an issue (#28)
- A work-round `split` becomes a D-row (#28)
- A disputed finding goes to the brief, never to a third pass (#28)
- The hand-back brief counts passes and the findings reported privately (#28)

### Fixed
- The hand-off packet's diff shows uncommitted edits, in a form the reviewer's guard runs (#28)
- The briefs' templates hold the `(no guard)` and `(pasted)` marks and an option's size unit (#28)
- The Clarify brief's D-row names the part of the system it touches (#28)
- Each review guide's § At task time holds only the questions a task asks (#28)

## [0.12.0] — 2026-11-22

### Changed
- The AGENTS template's body is a sixth shorter, with every rule kept (#29)
- The AGENTS template leaves the comment rules' reasons to `codebase_review.md` § Phase 2 (#29)
- The AGENTS template's commit gate allows WIP commits on a feature branch (#29)
- The AGENTS template's release gate holds a release that ships without a workflow (#29)
- The AGENTS template moves a board card only where `.lifecycle.toml` names a board (#29)
- The AGENTS template writes a new doc file where the accepted plan has a box for it, an ADR among them (#29)
- The AGENTS template lands a feature branch by the complete skill (#29)
- The AGENTS template holds the parts, evidence sources, drawn surfaces and test command the skills read (#29)
- The clarify skill has each D-row name the part of the system it touches (#29)
- The README says what the install changes on this machine without asking (#29)
- *Put a repository on the kit* stops at an empty repository before it installs anything (#29)
- A clone install writes its pull into the maintainer's global agent instructions (#29)

### Fixed
- The ideas home commits an upgrade's changes only on the user's go-ahead (#29)
- The ideas home's graduation freezes `IDEA.md` and deletes its split branch (#29)
- The AGENTS template's placeholder instructions and project-type notes match its body (#29)

## [0.11.0] — 2026-11-22

### Changed
- `lifecycle upgrade --adopt` deletes only a guide that is the kit's text, and prints the rest it keeps (#27)
- The AGENTS template's feature-branch flow waits for checks and merges, as the complete skill does (#27)
- The AGENTS template reads every link to the kit from the folder `lifecycle where` prints (#27)
- The maintainer's answers to a hand-back are made before *Complete* lands anything (#27)
- A release refused as moved checks its version, milestone and changelog again before review (#27)
- The session start's findings each say when their fix runs, under a lead that names no time (#27)

### Fixed
- The complete skill's close-out no longer fails on the branch `gh pr merge --delete-branch` deleted (#27)
- The upgrade skill keeps a first move's `--adopt` output for its round (#27)
- A hotfix release by the CONTRIBUTING template pushes to its own branch and leaves the milestone (#27)
- The release skill closes the milestone only on the integration branch (#27)
- The 0.4.0, 0.8.0 and 0.10.0 upgrade steps say where each applies and where a link goes (#27)

## [0.10.0] — 2026-11-22

### Changed
- The CONTRIBUTING template holds local setup, the release checklist and hotfixes only (#22)
- The AGENTS template keeps the gates and the rules applied on every change, and points at the rest (#22)
- The AGENTS template holds the repository's labels and changelog cap as placeholders (#22)
- `project_kickstart.md` keeps why for releases, branching and commits, and points at the templates (#22)
- `method/README.md` is the method's index alone (#22)
- `idea_gauntlet.md` § The ideas home says how an agent sets a home up (#22)
- `docs/guide.md` names the `lifecycle` commands a repository runs (#22)
- The clarify and review skills label an issue as the repository's `AGENTS.md` says (#22)
- The kit's model-facing reviewer reads `method/`, `UPGRADING.md` and `CHANGELOG.md` too (#22)
- Repositories: a pointer at a removed section of the method's README points at that section's new home (#22)

## [0.9.0] — 2026-11-22

### Changed
- `project_kickstart.md`'s release recipe runs its refusals with `shell: bash` on a Windows runner (#24)
- Repositories: each release job refuses a moved head and a tagged version before it ships, as 0.4.2's recipe does (#24)

## [0.8.0] — 2026-11-22

### Added
- `method/ideas_home_template.md` holds the ideas home's `AGENTS.md`, word for word (#21)

### Changed
- A repository reads the guides from the installed kit and keeps no copy of them (#21)
- `.lifecycle.lock` holds the release and the text of each template the repository follows (#21)
- `lifecycle doctor` asks for an upgrade only for a changed template or an upgrade step, never for guide wording (#21)
- `lifecycle upgrade` prints each template left to port with its diff and reads nothing over the network (#21)
- The first upgrade from a copy deletes the kit's files in the guides folder and keeps the repository's own (#21)
- An owed upgrade runs alone before a task's plan, and one due while a task is in the tree waits for it (#21)
- The upgrade skill owns a first move: it compares the copy with the kit, then runs `lifecycle upgrade --adopt` (#21)
- A gap a task finds in a kit guide is filed on the kit as an issue when it is found (#21)
- The skills and the reviewer read the guides from `method/` in the folder `lifecycle where` prints (#21)
- The templates link the kit's guides on GitHub (#21)
- `[guides] path` is retired, read only to find a copy of the method from before 0.8.0 (#21)
- A change to a recipe a repository instantiates ships with an upgrade step naming the file (#21)
- Repositories: the ideas home follows `ideas_home_template.md` in place of `idea_gauntlet.md` (#21)
- Repositories: every link to a kit guide in the guides folder opens the kit's guide on GitHub (#21)
- Repositories: `AGENTS.md` and `CONTRIBUTING.md` say a gap in a kit guide is filed on the kit (#21)
- Repositories: `.claude/settings.json` allows `lifecycle where` and drops the two removed commands (#21)

### Removed
- `lifecycle guides check` and `lifecycle guides push` (#21)
- `lifecycle upgraded` (#21)
- The *Upgrade* line in both briefs and in the hand-off packet (#21)

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
