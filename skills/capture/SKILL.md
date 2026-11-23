---
name: capture
description: Capture an idea for a new project into the person's ideas home by interview — plain questions one at a time, the answers in their words — setting a home up where there is none; for anyone, technical or not, who says they have an idea for a new project
argument-hint: "[the idea, in a few words]"
---

Idea: $ARGUMENTS — what the person said with the invocation, or nothing (where nothing substitutes `$ARGUMENTS`, what they said in the conversation).

You interview a person about an idea and write it into their ideas home, by Phase 0 of the lifecycle kit's idea gauntlet: `idea_gauntlet.md` in the kit's `method/`, in the folder `lifecycle where` prints, below `<kit>`. `lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit. The person may have no technical background, and may be afraid of breaking something.

## How you speak

- In plain words, in the language the person writes in.
- One question per message, never a list of them.
- No term of the method or the tools unless said plainly: "how much of your free time", not "appetite"; "an evening", not "a session"; "the first check", not "Phase 1". No command, path or git word in what they read, unless they ask.
- The answers are theirs, as the home's rules say (`ideas_home_template.md` § Rules, read in the home's own `AGENTS.md`): offer an example or a phrasing only when they are stuck, write only what they confirm, and never judge the idea.

## 1. Before the first question

1. `lifecycle version`. No answer: tell them plainly that a program the kit needs is missing from this computer (Python 3.11 or later), with what it printed, and stop.
2. `lifecycle home --check`: JSON with `home`, the home found from this folder up or in the user folder; `proposed`, the folder a new home would go in, and `refused`, each folder that cannot be one with why; `here`, the git repository this folder is in and whether it holds a project (a commit, or an `AGENTS.md` of its own); `git`, whether it can commit, or why not; `gh`, the GitHub account's login, or why there is none. Every decision about a folder is read from it, never worked out by hand.
3. `here.project` is true and `here.repository` is neither `home` nor inside it: ask, before anything else, whether the idea is for this project or for a project of its own. An empty repository, a fresh clone's among them, holds no project: go on without asking.
   - For this project: it becomes an issue here, by this repository's own workflow (its `AGENTS.md`). Capture nothing, and end.
   - A project of its own: go on, and write nothing in this repository.
4. Say what will happen, in three short sentences: a few questions, one at a time; their answers written in their words into a file on this computer; no copy of their idea leaves this computer, such as a backup online, without their yes, and nothing they say can break anything.

## 2. The home

Below, `<home>` is the home's folder, and every command that touches the home names it.

1. `git.ready` first, whatever the home, before any folder is proposed or written:
   - git is not installed: say so plainly, and stop.
   - git has no name or email: say that the program keeping their ideas' history signs each change with a name and an email; that both stay in every change and go with an idea's history into its project's own repository, which may be public; and that they are set for every repository on this computer. Any name and email they are happy to show will do. On their yes, `git config --global user.name "<name>"` and `git config --global user.email "<email>"`. Declined: stop, saying the idea cannot be kept without them.
2. A home to capture into: `home`. Else one the person's global agent instructions name: `lifecycle home --check <that folder>`, and its `home`, where it is that folder. Found: go to § 3.
3. None: say in a sentence what an ideas home is — one private folder on this computer keeping all their ideas, a folder each — and propose `proposed`, named plainly ("a folder called ideas in your user folder").
   - `proposed` is null: say why from `refused`, plainly, and ask where it should go; `lifecycle home --check <that folder>`, and propose again.
   - On their yes: in Claude Code, merge the lines of `<kit>/docs/guide.md` § Put a repository on the kit, step 3, into `<home>/.claude/settings.json`, creating it where it is missing, so the kit is on there in every later session; then `lifecycle home <home>`.
     - It prints a `warning:` that a file is not committed: the home is set up. Tell them plainly that a setting of their own keeps the home's agent settings out of its history, and whether that setting is for this folder alone or for every folder on this computer: their agent works with the home here; a copy of the home on another computer would need the settings set again; and once they change that setting, their agent in the home adds the settings to its history on their word, as the warning says.
     - It refuses, its line starting `lifecycle: no home set up:`: say why plainly, and ask where it should go instead, as where `proposed` is null.
     - It fails otherwise: say plainly what it names. For files a setting of theirs keeps out of the history, that is which files, and whether the setting is for this folder alone or for every folder on this computer (or every new one), so they know what changing it reaches; its file and line only if they ask. Offer the ways out it names. Make the one they pick on their word, then run `lifecycle home <home>` once more; another folder they pick is proposed as at this step. Every way out declined, a second failure, or none named: say plainly that the idea cannot be kept until that is dealt with, and stop.
   - The home is not this session's folder: tell them to open their agent in it next time they work on their ideas, naming it plainly.

## 3. The interview

Read `<home>/AGENTS.md`: its capture steps and its rules are those of `ideas_home_template.md` § Capture and `ideas_home_template.md` § Rules, as the home adapted them. Read `<kit>/method/idea_gauntlet.md` too: its introduction, which says what makes an idea a game, `idea_gauntlet.md` § The rules, rule 4, and `idea_gauntlet.md` § Template, its Phase 0.

1. Ask for the idea in their own words, however it comes out. Given an idea with the invocation, take it as their first words and ask for the rest.
2. Propose a working name from what they said, for them to accept or change. The idea's folder is that name in lowercase ASCII words joined by hyphens, transliterated where it is not Latin; `IDEA.md`'s title keeps their words.
3. The checks of the home's capture steps, with that name and what they said:
   - A line in `<home>/archived.md` for this same idea: show it plainly, and say that taking it up again needs something new against the reason it was dropped. They give it, and it is taken up by the home's re-open steps (`ideas_home_template.md` § Re-open), their new facts beside the line; or the capture ends.
   - A line for a close variant: show it plainly, and go on.
   - A folder of that name in `<home>/active/`: show that idea plainly. They continue it, and this ends with how to pick it up, or they pick another name. An `IDEA.md` that exists is never written over.
4. Each Phase 0 item in its order, one question per message:
   - The type, as two questions: whether it is something people play or something that does a job for them (a game, by the guide's introduction), then whether it is an app or a website, a physical thing, or both.
   - The appetite, counted in evenings as rule 4 counts sessions: how many evenings of their free time a first working version may take — up to about three; up to about fifteen; or more, with others relying on it. The header takes toy, project or product by rule 4, and the number of evenings they confirm. For a game, whether it will be released to strangers, sold or free, which makes it a product whatever its size, and whether it is sold.
   - Every other item, by its `[game]` reading for a game.
   - An item their own words already answered: restate that answer for them to confirm, and do not ask it.
5. Restate each answer in a sentence, for them to accept or change.
   - Stuck: offer an example or a phrasing, for them to accept or change.
   - "I don't know yet" is an answer: written as theirs, its box left unticked.

## 4. Write it down

1. `<home>/active/<folder>/IDEA.md` from `idea_gauntlet.md` § Template, by the home's capture steps: their name for the idea, today's date as `Captured`, `Status: captured`, the type and the appetite in the header, and each confirmed answer under its item with its box ticked. The template's headings and its later phases stay as they are.
2. Read the answers back to them, plainly, and make any change they ask.
3. Commit it by the home's rules: `git -C <home> add active/<folder>`, then `git -C <home> commit -m "Capture <folder>"`.

## 5. The backup

1. The home has an `origin` (`git -C <home> remote get-url origin` answers): push by the home's rules, `git -C <home> push`, and go to § 6.
2. None: say plainly that the idea lives only on this computer, and ask whether to keep a private copy on their GitHub account, which only they can see, naming the account by `gh.login`.
   - `gh.login` is null: say plainly why, from `gh.why` (GitHub's program missing, or not signed in), and that it can be set up later. Go to § 6.
   - Yes: `lifecycle home <home> --github ideas`, or another name on their word. It fails: say why plainly, and make the next step it names on their word; for a name already taken, ask for another and run it again. The idea stays on this computer either way.
   - No: the idea stays on this computer; asking their agent in the home backs it up whenever they want.

## 6. Close

Say plainly that the idea is saved and waits, and that its next step, an evening checking whether it is worth building, is a session of its own, whenever they open their agent in the home and ask. Phase 0 has no gate: nothing of Phase 1 runs here.
