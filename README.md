# lifecycle-kit

How your projects run, from an idea to its releases, kept in one place: the method every repository follows, and the agent skills and command that carry it out. It is orwir's personal kit, built for their own repositories and public so others can read and install it; its issues and pull requests come from orwir alone, and this page speaks to orwir as "you".

- **A plan reviewed before the code.** A task's plan goes into its issue. Where it has a shape that has shipped holes before, a reviewer agent with none of the author's context reads it against the code first.
- **The work reviewed before you read it.** Once the gate is green, fresh reviewers read the diff against the plan, one more for each of the person-facing and model-facing lenses the diff touches. You read one hand-back brief: what changed, what was checked, what is yours to decide.
- **Nothing lands without your word.** The agent commits the task, pushes, closes the issue and ships a release only on your go-ahead; on a feature branch it may save work in progress.
- **Every repository on one method.** Each reads the guides from the kit installed on this machine, so a release reaches every repository at once. A repository commits for a release only when it changes a template the repository follows or asks a step of it, and a session start says so.

## Install

Paste this into your agent, Claude Code or any other, started in the repository:

```text
Put this repository on my lifecycle kit, the GitHub repository
orwir/lifecycle-kit: read its docs/guide.md with gh and follow
"Put a repository on the kit". Commit nothing.
```

The agent:

- stops if the repository is empty: a new project starts from its idea instead, and your ideas home moves the idea into the new repository and runs the method's kickstart, which does this same setup;
- sets the kit up on this machine if it is missing, without your go-ahead: the Claude plugin, or a clone on PATH with the agent's skills and your global agent instructions pointed at it;
- turns the kit on in the repository (in Claude Code, you run `/reload-plugins` when it asks) and writes its settings from what it finds there, asking you what it cannot tell;
- deletes any copy of the kit's guides the repository holds, ports its templates into its `AGENTS.md`, `CONTRIBUTING.md` and issue and PR templates, and hands you the diff.

Anything else outside the repository, such as a branch on GitHub, waits for your go-ahead.

## A task, end to end

In Claude Code the skills are `/lifecycle:<name>`; with another agent, ask for the skill by name ("run the lifecycle kit's clarify skill on issue 12").

1. **Open an issue** from the task template.
2. **Clarify** (`/lifecycle:clarify <N>`). The agent writes the plan into the issue, runs the plan round, and hands you the Clarify brief. Answer what it asks and say "go": a question you leave unanswered takes its recommended option.
3. **The work.** The agent builds it and runs the gate.
4. **Review** (`/lifecycle:review <N>`). The work round, ending in the hand-back brief.
5. **Answer what it asks, and say "lgtm".** A question you leave unanswered takes its recommended option. The agent makes your answers, then lands it: the commit, the push, a read of the CI the push started, the issue closed, and any gap it found in a guide already filed by `lifecycle gap`. Where that CI is red, the issue stays open until a fix or a re-run turns it green and you say to go on. Landed from a linked worktree, it fast-forwards the primary checkout too, and counts the other worktrees whose work has landed: `lifecycle tidy --remove` removes them and their branches when you say so. A veto, or an answer bigger than the brief said, comes back as a new brief that waits for your "lgtm" again.

A change with no issue skips step 2 and runs step 4 with no number; one obvious change with nothing to decide skips both rounds, and its brief says so. An idea that is not a project yet goes to the capture skill (`/lifecycle:capture`): it asks you about it one plain question at a time and writes it into your ideas home, setting one up where you have none. Releases run by the release skill (`/lifecycle:release`), which reads CI on the commit it will ship and stops for your "proceed" before it ships, never shipping on red. When a new release asks something of a repository, the session start says so and the upgrade runs alone before the next task; ask the agent to upgrade any time with the upgrade skill.

## More

- [docs/guide.md](docs/guide.md): what the kit keeps in a repository, how it stays current, every setting, and how the kit is built.
- [method/](method/README.md): the guides themselves, from an idea's gauntlet to releases and reviews.
- [AGENTS.md](AGENTS.md): changing the kit itself.
