# Changelog

What each kit release changed, newest first. A guide push from a project adds its own line.

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
