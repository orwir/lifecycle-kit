# lifecycle-kit

The maintainer's project lifecycle in one versioned repository: the method every project follows, the mechanics that carry it out, and a thin Claude Code plugin over both. It is for the maintainer's own repositories first; how it is shared comes later. It does not hold anything one project owns: a project's design language, its release checklist and its `AGENTS.md` stay in that project.

## Layers

| Layer | Holds | Run by |
|---|---|---|
| `method/` | the guides: kickstart, task review, the review kinds, the templates | anyone who reads |
| `tools/lifecycle/` | the `lifecycle` command: settings, doctor, upgrade, guide push, board, guards, hooks | any agent, a git hook, CI, a person |
| `skills/`, `agents/` | clarify, review, handback, complete, release, upgrade; the read-only reviewer | any agent that loads Agent Skills |
| `.claude-plugin/`, `hooks/`, `bin/` | the Claude Code adapter: marketplace, plugin manifest, hook wiring, the command on PATH | Claude Code |

The skills keep to what every Agent Skills tool reads; anything only Claude Code understands sits in the adapter. Outside Claude Code, the command is `bin/lifecycle` in a checkout of the kit (`bin/lifecycle.cmd` from cmd or PowerShell), and `lifecycle where` names the kit's folder, so an agent finds the reviewer definition in `agents/`. The tools are standard-library Python 3.11 or later, so they run wherever a repository does.

## A repository on the kit

Three files hold a repository's side of it:

- `.lifecycle.toml` — hand-written settings (below).
- `.lifecycle.lock` — written by `lifecycle upgrade` (the kit release the repository is on and the digest of each guide it copied) and by `lifecycle guides push` (each guide pushed since, with the release that took it, which the next upgrade waits for).
- the guides folder (`docs/guides/` by default) — a copy of `method/` at that release, so the repository reads on its own, on GitHub and for any agent.

`lifecycle doctor` runs at every session start through the plugin and names each finding's fix, with what the kit changed since the repository's release. A repository behind the installed kit upgrades as a tracked task's first step, on any release; an untracked task meets a minor or major one at its work round. The upgrade replaces the issue and PR templates a repository kept word for word, and the agent ports the rest and makes each change a `Repositories:` line of the kit's CHANGELOG requires; it lands as its own commit ahead of the task's where it can. Once a day, `doctor` also asks the kit's remote for its newest release, and says so when this machine's kit is older.

A guide edit starts in the repository whose task found it, is reviewed in that task's diff, and goes to the kit at the task's *Complete* with `lifecycle guides push`, which replays it onto the kit's latest and releases it as a patch.

### Settings

```toml
# .lifecycle.toml
[branches]
integration = "develop"   # where tasks land
protected = "master"      # takes only release-PR merges; the push and deploy guards hold it

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

[review]
allow = ["dotnet format --verify-no-changes"]   # read-only checks the reviewer may run

[review.lenses.person-facing]
paths = ["src/App/"]
read = ["docs/guides/design_language.md — every new screen line reuses its components"]
```

### Turning it on in Claude Code

Once per machine, with git able to read the private repository (`gh auth setup-git`, or Git Credential Manager):

```
claude plugin marketplace add orwir/lifecycle-kit
claude plugin install lifecycle@lifecycle-kit
```

The plugin is off by default. A repository turns it on in its committed `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "lifecycle-kit": { "source": { "source": "github", "repo": "orwir/lifecycle-kit" }, "autoUpdate": true }
  },
  "enabledPlugins": { "lifecycle@lifecycle-kit": true }
}
```

Then `.lifecycle.toml`, and `lifecycle upgrade` (`--adopt` for guides with no recorded source). The skills are `/lifecycle:clarify`, `/lifecycle:review`, `/lifecycle:handback`, `/lifecycle:complete`, `/lifecycle:release` and `/lifecycle:upgrade`; the reviewer is the `lifecycle:reviewer` agent.

## Working on the kit

[AGENTS.md](AGENTS.md).
