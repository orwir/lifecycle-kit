# lifecycle-kit

How your projects run, from an idea to its releases, kept in one place: the method every repository follows, and the agent skills and command that carry it out. It is private and built for your own repositories, so this page is written for you.

- **A plan reviewed before the code.** A task's plan goes into its issue. Where it has a shape that has shipped holes before, a reviewer agent with none of the author's context reads it against the code first.
- **The work reviewed before you read it.** Once the gate is green, fresh reviewers read the diff against the plan, one more for each surface a person or a model reads. You read one hand-back brief: what changed, what was checked, what is yours to decide.
- **Nothing lands without your word.** The agent commits, pushes, closes the issue and ships a release only on your go-ahead.
- **Every repository on one method.** Each keeps a copy of the guides pinned to a kit release, and a session start says when it is behind. A guide improved in one project comes back here and reaches the rest at their next upgrade.

## Install

Paste this into your agent, Claude Code or any other, started in the repository:

```text
Put this repository on my lifecycle kit, the private GitHub repository
orwir/lifecycle-kit: read its docs/guide.md with gh and follow
"Put a repository on the kit". Commit nothing.
```

The agent sets the kit up on this machine if it is missing, turns it on in the repository, writes the repository's settings from what it finds there, asking you what it cannot tell, copies the method in, ports its templates into the repository's `AGENTS.md`, `CONTRIBUTING.md` and issue and PR templates, and hands you the diff. Anything outside the repository, such as a branch on GitHub, waits for your go-ahead. A new project starts from its idea instead: your ideas home moves the idea into the new repository and runs the method's kickstart, which does this same setup.

## A task, end to end

In Claude Code the skills are `/lifecycle:<name>`; with another agent, ask for the skill by name ("run the lifecycle kit's clarify skill on issue 12").

1. **Open an issue** from the task template.
2. **Clarify** (`/lifecycle:clarify <N>`). The agent writes the plan into the issue, runs the plan round, and hands you the Clarify brief. Answer what it asks and say "go".
3. **The work.** The agent builds it and runs the gate.
4. **Review** (`/lifecycle:review <N>`). The work round, ending in the hand-back brief.
5. **"lgtm".** The agent lands it: the commit, the push, the issue closed, and any guide edit sent back to the kit as a release.

A change with no issue skips step 2 and runs step 4 with no number; one obvious change with nothing to decide skips both rounds, and its brief says so. Releases run by the release skill (`/lifecycle:release`), which stops for your "proceed" before it ships. When the kit moves on, the session start says so and the next task upgrades first; ask the agent to upgrade any time with the upgrade skill.

## More

- [docs/guide.md](docs/guide.md): what the kit keeps in a repository, how it stays current, every setting, and how the kit is built.
- [method/](method/README.md): the guides themselves, from an idea's gauntlet to releases and reviews.
- [AGENTS.md](AGENTS.md): changing the kit itself.
