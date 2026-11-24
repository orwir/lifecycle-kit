# Security policy

Every repository on the lifecycle kit runs what is here, so a vulnerability in the kit reaches all of them at once.

## Reporting a vulnerability

Report it privately, through GitHub's private vulnerability reporting: [open a report](https://github.com/orwir/lifecycle-kit/security/advisories/new), or the repository's **Security** tab, **Report a vulnerability**. Never in a public issue, pull request or discussion: a public report shows the vulnerability to every repository on the kit before its fix ships.

Include:

- what is affected: the file, command, skill, guide, template or recipe, and the release `lifecycle version` prints, or the commit where the code is on `next` and not released yet;
- what an attacker can do with it, and what they need first;
- the shortest steps that show it.

## What to expect

- An acknowledgement within 7 days. With none by then, comment on the report to raise it again.
- A fixed release, or a published advisory saying what to do until one ships, within 90 days of the report.
- A report the kit declines, as no vulnerability or out of scope, is closed with its reason.

Both times are best effort: the kit has one maintainer.

## Supported versions

Only the latest release, which the plugin marketplace serves from `main`. A fix ships as a new release, which a machine takes by updating the plugin, or by pulling where it runs the kit from a clone. A vulnerability in code on `next` that is not released yet is reported the same way.

## Scope

In scope is everything the kit ships that an agent runs or follows, or that a repository instantiates:

- the `lifecycle` command (`tools/`, `bin/`);
- the Claude Code adapter (`hooks/`, `.claude-plugin/`);
- the skills and the reviewer agent (`skills/`, `agents/`), such as an instruction that makes an agent run an unsafe command or expose a secret;
- the method (`method/`): its guides, templates and recipes, such as a workflow, hook or script that is unsafe as written;
- the upgrade steps in `UPGRADING.md`;
- the steps that put a repository on the kit: the install prompt in `README.md` and `docs/guide.md` § Put a repository on the kit.

Out of scope, each reported to its own project:

- a repository on the kit, by its own security policy;
- Claude Code, GitHub and the other services the kit runs on;
- the third-party tools a recipe names, such as a scanner, a hook manager or a CI action.
