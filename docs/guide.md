# The kit in a repository

What the kit keeps in a repository, how it stays current, and its settings. The first section is for the agent the front page's install prompt sends here; the rest is reference for it and for you.

## Put a repository on the kit

Agent instructions. Commit nothing: the maintainer reads the diff and gives the go-ahead. Change nothing beyond this machine's agent setup and the repository's tree; where a step below would, it stops for the maintainer.

1. **The kit on this machine.**
   - Claude Code: when `claude plugin list` has no `lifecycle@lifecycle-kit`, make sure git can read the private repository (`gh auth setup-git`, or Git Credential Manager), then:

     ```
     claude plugin marketplace add orwir/lifecycle-kit
     claude plugin install lifecycle@lifecycle-kit
     ```

   - Any other agent: clone `orwir/lifecycle-kit` where the maintainer says, and leave it where later sessions find it. Put the clone's `bin/` on PATH, so `lifecycle` answers (`bin/lifecycle.cmd` from cmd or PowerShell), and point the agent's skill loading at the clone's `skills/`; where the agent loads no skills, name the clone's path in the maintainer's global agent instructions. The reviewer's definition is in `agents/`, and `lifecycle where` names the folder.
2. **An empty repository** is a new project: stop and tell the maintainer. A new project starts from its idea, in the ideas home, which runs the method's `project_kickstart.md` in a run of its own; its day zero comes back to the steps below.
3. **Turn the kit on.** In Claude Code the plugin is off by default: merge these lines into the repository's committed `.claude/settings.json`.

   ```json
   {
     "extraKnownMarketplaces": {
       "lifecycle-kit": { "source": { "source": "github", "repo": "orwir/lifecycle-kit" }, "autoUpdate": true }
     },
     "enabledPlugins": { "lifecycle@lifecycle-kit": true }
   }
   ```

   Claude Code loads it on `/reload-plugins`: ask the maintainer to run it, and go on once `lifecycle version` answers. If it never answers, stop and report what it printed. A new session holds none of this: there the maintainer pastes the install prompt again, and the steps go on from the first one not done.
4. **Write `.lifecycle.toml`** at the root, by *Settings* below, from what the repository says: its integration branch, a board its `CONTRIBUTING.md` or `AGENTS.md` names, the gate its git hooks or CI run, a release workflow in `.github/workflows/`, the paths a person or a model reads. Leave out a table the repository has no use for, and ask the maintainer what the repository does not settle.
5. **Run the upgrade skill** (`/lifecycle:upgrade` in Claude Code, `skills/upgrade/SKILL.md` otherwise). It copies the method in, ports the templates into the repository's own files, and makes each step of the kit's `UPGRADING.md` that applies here, as `lifecycle doctor` prints them; a step that changes something outside the tree, such as a branch on GitHub, waits for the maintainer's go-ahead, as the skill says. Two things it does not say yet for a first move:
   - `lifecycle doctor` prints "not on the kit yet" and points at `lifecycle upgrade --help`. Follow the skill, not that pointer, or the template ports and the upgrade steps are skipped.
   - At the skill's step 2 a first move runs `lifecycle upgrade --adopt`, since a plain `lifecycle upgrade` refuses a repository with no `.lifecycle.lock`. `--adopt` overwrites each guide named as one in the kit's `method/`: where one already in the folder differs from the kit, show the difference to the maintainer first, who takes it into the kit or drops it. A project's own guide, such as `design_language.md`, stays as it is.
6. **Hand back** by the upgrade skill's last step, naming as well the settings files written at steps 3 and 4 and what the maintainer was asked. The work round it runs adds `.lifecycle.toml` and `.claude/settings.json` to its diff, so a reviewer reads the settings every later round runs on.

## What a repository holds

Three files hold a repository's side of it:

- `.lifecycle.toml`: hand-written settings (*Settings*).
- `.lifecycle.lock`: written by `lifecycle upgrade` (the kit release the repository is on and the digest of each guide it copied) and by `lifecycle guides push` (each guide pushed since, with the release that took it, which the next upgrade waits for).
- the guides folder (`docs/guides/` by default): a copy of `method/` at that release, so the repository reads on its own, on GitHub and for any agent.

## Staying current

`lifecycle doctor` runs at every session start through the plugin, and before a task by the repository's `AGENTS.md` where no plugin runs it. It names each finding's fix, with what the kit changed since the repository's release. A repository behind the installed kit upgrades as a tracked task's first step, on any release; an untracked task meets a minor or major one at its work round. The upgrade replaces each file a template ports into that the repository kept word for word (usually the issue and PR templates), and the agent ports the rest and makes each step the kit's `UPGRADING.md` asks of every repository, which `doctor` prints oldest release first; it lands as its own commit ahead of the task's where it can. Once a day, `doctor` also asks the kit's remote for its newest release, and says so when this machine's kit is older.

A guide edit starts in the repository whose task found it, is reviewed in that task's diff, and goes to the kit at the task's *Complete* with `lifecycle guides push`, which replays it onto the kit's latest and releases it as a patch. Its line is the patch's entry in the kit's changelog, so the push refuses one that breaks the changelog's style: over 120 characters, a second claim welded on by a semicolon or a dash, or an issue number.

## Settings

```toml
# .lifecycle.toml
[branches]
integration = "main"      # the one long-lived branch: where tasks land and releases are cut

[board]                   # omit when the repository tracks no board
owner = "orwir"
number = 9

[gate]                    # the local gate, in order
commands = ["scripts/check.sh"]
# A targeted run on a worktree of the base, to prove a new test fails without the change:
# {root} is the worktree, {tests} the new tests in the form the command takes (here a filter).
targeted = "dotnet test {root} --filter {tests}"

[guides]
path = "docs/guides"

[release]                 # omit when the repository ships no release by a workflow
workflow = "release.yml"  # what `lifecycle release <commit>` dispatches on the reviewed commit

[review]
allow = ["dotnet format --verify-no-changes"]   # read-only checks the reviewer may run

[review.lenses.person-facing]
paths = ["src/App/"]
read = ["docs/guides/design_language.md — every new screen line reuses its components"]

# [templates]             # an ideas home's; a project omits it for its five (below)
# "idea_gauntlet.md" = "AGENTS.md"   # the template, and the file it ports into
```

Without `[templates]`, a repository follows a project's templates: `agents_template.md` → `AGENTS.md`, `contributing_template.md` → `CONTRIBUTING.md`, and the issue and PR templates → `.github/ISSUE_TEMPLATE/bug.md`, `.github/ISSUE_TEMPLATE/task.md` and `.github/pull_request_template.md`. Naming any lists every template the repository follows: an ideas home follows only the one in `idea_gauntlet.md`, as the commented lines show.

## How the kit is built

| Layer | Holds | Run by |
|---|---|---|
| `method/` | the guides: kickstart, task review, the review kinds, the templates | anyone who reads |
| `tools/lifecycle/` | the `lifecycle` command: settings, doctor, upgrade, guide push, board, release, hooks | any agent, a git hook, CI, a person |
| `skills/`, `agents/` | clarify, review, handback, complete, release, upgrade; the read-only reviewer | any agent that loads Agent Skills |
| `.claude-plugin/`, `hooks/`, `bin/` | the Claude Code adapter: marketplace, plugin manifest, hook wiring, the command on PATH | Claude Code |

The skills keep to what every Agent Skills tool reads; anything only Claude Code understands sits in the adapter. `lifecycle where` names the kit's folder. The tools are standard-library Python 3.11 or later, so they run wherever a repository does.
