# The kit in a repository

What the kit keeps in a repository, how it stays current, and its settings. The first section is for the agent the front page's install prompt sends here; the rest is reference for it and for you.

## Put a repository on the kit

Agent instructions. Commit nothing: the maintainer reads the diff and gives the go-ahead. Change nothing beyond this machine's agent setup and the repository's tree; where a step below would, it stops for the maintainer.

1. **An empty repository** is a new project: stop and tell the maintainer, before anything is installed. A new project starts from its idea, in the ideas home, which runs the method's `project_kickstart.md` in a run of its own; its day zero comes back to the steps below.
2. **The kit on this machine.**
   - Claude Code: when `claude plugin list` has no `lifecycle@lifecycle-kit`:

     ```
     claude plugin marketplace add orwir/lifecycle-kit
     claude plugin install lifecycle@lifecycle-kit
     ```

   - Any other agent: clone `orwir/lifecycle-kit` where the maintainer says, and leave it where later sessions find it. Put the clone's `bin/` on PATH, so `lifecycle` answers (`bin/lifecycle.cmd` from cmd or PowerShell), and point the agent's skill loading at the clone's `skills/`. In the maintainer's global agent instructions, name the clone's path (where the agent loads no skills, it finds them there) and a pull of it, `git -C <clone> pull`, run at a task's start before `lifecycle doctor`; a pull that fails is reported to the maintainer, and the task goes on with the release the clone holds. The reviewer's definition is in `agents/`, and `lifecycle where` names the folder.
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
5. **Run the upgrade skill** (`/lifecycle:upgrade` in Claude Code, `skills/upgrade/SKILL.md` otherwise). A first move compares each guide in the repository named like one in the kit's `method/` with the kit's and shows the maintainer every difference, then runs `lifecycle upgrade --adopt`, which deletes each one whose text is the kit's and keeps the rest; an older copy among them goes by hand once compared. The repository reads the kit's guides from the installed kit, and its own guides, such as `design_language.md` or its own `README.md` index, stay. It ports the templates into the repository's own files and makes each step of the kit's `UPGRADING.md` that applies here, as `lifecycle doctor` prints them; a later step can undo an earlier one, so it makes their net effect. A step that changes something outside the tree, such as a branch on GitHub, waits for the maintainer's go-ahead, as the skill says.
6. **Hand back** by the upgrade skill's last step, naming as well the settings files written at steps 3 and 4. The work round it runs adds `.lifecycle.toml` and `.claude/settings.json` to its diff, so a reviewer reads the settings every later round runs on.

## What a repository holds

Two files hold a repository's side of it, beside the files its templates port into:

- `.lifecycle.toml`: hand-written settings (*Settings*).
- `.lifecycle.lock`: written by `lifecycle upgrade`, holding the kit release the repository last upgraded to and the text of each template it follows at that release.

The guides are not copied in: every agent reads them from the installed kit, in `method/` of the folder `lifecycle where` prints, and links on GitHub point at the kit. A repository's own guides, such as `design_language.md`, keep their folder.

## Staying current

`lifecycle doctor` runs at every session start through the plugin, and before a task by the repository's `AGENTS.md` where no plugin runs it. A release that changes only guide wording, a skill or the tools asks nothing of a repository: it reads the release at once. One that changes a template the repository follows, or writes a step in the kit's `UPGRADING.md`, asks for an upgrade, and `doctor` names its fix with the steps, the templates and what the kit changed, each change by its group (Added, Changed, Fixed or Removed). The upgrade runs alone, with its own round and commit, before a task's plan or an untracked task's first edit; one that comes due while a task's edits are in the tree waits until that task lands. It replaces each file a template ports into that the repository kept word for word (usually the issue and PR templates), and the agent ports the rest and makes each step, oldest release first. This machine's kit takes a new release on its own route from step 2: the plugin by the marketplace's `autoUpdate` that step 3 turns on, and a clone by the pull step 2 writes into the maintainer's global agent instructions, run before a task. Nothing checks the kit's remote for you, so a clone that is never pulled stays on its release.

The command behind it: `lifecycle doctor` says what a repository needs before its next task; `lifecycle upgrade` brings its templates and lock to the installed release when the kit asks; `lifecycle upgrade --adopt` is a first move, which the upgrade skill runs.

A gap a task finds in one of the kit's guides, or a pattern reusable across projects, is filed as soon as the task finds it, and `lifecycle gap` files it: on the kit where the signed-in `gh` user can push to it, otherwise in the repository itself, labelled `kit-gap`. It is in the kit's words either way, so the kit's maintainer lifts it onto the kit from any repository they can read; where no issue can be filed, it waits in the task's plan until one can. The kit's own task changes the guide (`method/task_review.md` § Developer rules).

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

[release]                 # omit when the repository ships no release by a workflow
workflow = "release.yml"  # what `lifecycle release <commit>` dispatches on the reviewed commit

[review]
allow = ["dotnet format --verify-no-changes"]   # read-only checks the reviewer may run

[review.lenses.person-facing]
paths = ["src/App/"]
read = ["docs/guides/design_language.md — every new screen line reuses its components"]

# [templates]             # an ideas home's; a project omits it for its five (below)
# "ideas_home_template.md" = "AGENTS.md"   # the template, and the file it ports into
```

Without `[templates]`, a repository follows a project's templates: `agents_template.md` → `AGENTS.md`, `contributing_template.md` → `CONTRIBUTING.md`, and the issue and PR templates → `.github/ISSUE_TEMPLATE/bug.md`, `.github/ISSUE_TEMPLATE/task.md` and `.github/pull_request_template.md`. Naming any lists every template the repository follows: an ideas home follows only `ideas_home_template.md`, as the commented lines show.

`[guides] path` is retired: it named the folder that held a copy of the method before 0.8.0, and the upgrade reads it only to find that copy (`docs/guides/` by default). A later release stops reading it.

## How the kit is built

| Layer | Holds | Run by |
|---|---|---|
| `method/` | the guides: kickstart, task review, the review kinds, the templates | anyone who reads |
| `tools/lifecycle/` | the `lifecycle` command: settings, doctor, upgrade, board, release, gap, hooks | any agent, a git hook, CI, a person |
| `skills/`, `agents/` | clarify, review, handback, complete, release, upgrade; the read-only reviewer | any agent that loads Agent Skills |
| `.claude-plugin/`, `hooks/`, `bin/` | the Claude Code adapter: marketplace, plugin manifest, hook wiring, the command on PATH | Claude Code |

The skills keep to what every Agent Skills tool reads; anything only Claude Code understands sits in the adapter. `lifecycle where` names the kit's folder. The tools are standard-library Python 3.11 or later, so they run wherever a repository does.
