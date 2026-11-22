---
name: clarify
description: Run the plan round at Clarify for an issue (the method's task_review.md) — the plan in the issue, the plan packet, the reviewer, the Clarify brief
argument-hint: "<issue number>"
---

Task: $ARGUMENTS — the issue number given with the invocation (where nothing substitutes `$ARGUMENTS`, the number the maintainer named). A task with no issue has no plan and skips this round; the review skill runs its work round untracked.

You are the developer and you run the whole round here, before any code. The maintainer reads only the brief at the end, so print nothing but the one line in § 3.

## 0. Before anything

1. `lifecycle` is the kit's command: on PATH where the kit's Claude plugin is on, otherwise `bin/lifecycle` in a checkout of the kit.
2. Where the settings name a board (`lifecycle config`), `lifecycle board <N> "In Progress"`.
3. `lifecycle doctor --json`:
   - a finding whose fix is `upgrade`, with no task's edits in the tree: run the upgrade skill now, alone; it lands by its own *Complete*, and this round starts after it;
   - the same, with an accepted plan's edits in the tree: the upgrade waits until this task lands;
   - a `block` whose fix is `adopt` or `update-kit`, or a failure of the command: stop and tell the maintainer what it printed;
   - anything else: carry on.
4. `lifecycle config` prints the settings. Below, `<method>` is `method/` in the folder `lifecycle where` prints, and *§* a section of `<method>/task_review.md`.
5. Read `<method>/task_review.md`: the plan round, the plan packet, the plan return, the Clarify brief, the brief rules and the developer rules are there; the plan's sections are the repository's issue templates (`.github/ISSUE_TEMPLATE/`). Read `AGENTS.md` § Task workflow too, and do any step it adds to this round (a drawing, an evidence source) where it says.

## 1. Write the plan into the issue — gather, don't recall

1. **The ticket.** `gh issue view <N>` and the code the change touches: every path, caller and entry point it meets. A *Plan* already in the issue is where this session continues:
   - `proposed`, unmarked: check it against the code, then run its round;
   - `proposed, plan round …` (§ The plan round, step 4): the round ran; render the Clarify brief (§ 5) from the mark and the plan;
   - `accepted`: *Clarify* is over, and the work continues from its ticked boxes and the tree.
2. **The root cause.** A bug's root cause is a hypothesis until real data confirms it, from the evidence sources AGENTS.md § Task workflow names (logs, the database, a live probe). The issue's *Root cause* says what holds, with the evidence as coordinates. Where the data does not confirm it, *Root cause* says so, and the plan's first box takes the next evidence; where how to get it is a one-way door (§ Terms), a D-row asks.
3. **The plan.** The template's `## Plan`, with `**Status:** proposed`, as the body's last section. An issue in an older shape gets its plan now: its technical details, options and verification move in, checked against the code.
   - A WHEN … THEN line per scenario, failure paths included; *Seams*; a box per path; a D-row per one-way door the ticket leaves open and a `Taken:` line per two-way choice you make (§ Terms, § Developer rules); *Verification*; *Departures* `none`.
   - Every D-row names the part it touches, one AGENTS.md § Task workflow names, or none for a docs or process choice.
   - *Verification* names a test per WHEN line; a scenario no test can score names how it is scored, or says `not covered: <why>`. That each test fails without the change is the work round's to prove.
   - Coordinates, never payload: an attack is described by its shape and where the evidence sits. No live person is named: invent a name of the same shape, or give a count.
4. **Write it.** `gh issue view <N> --json body -q .body`, fresh; the whole new body, everything outside the plan as it stands, to a file in a scratch folder outside the tree; then `gh issue edit <N> --body-file <file>`. Every later change to the plan is written the same way.
5. **The drawing.** Where AGENTS.md § Task workflow names drawn surfaces and the change touches one, draw it now, as part of the plan, by `design_workflow.md`. Each open decision is a D-row, and the brief's *You see* links the drawing. The reviewer cannot see it, so the packet states its region and decisions in words.
6. **The shape:** which of § When it runs' four shapes the plan has, and where it meets it.
   - One or more: the round runs (§ 2).
   - None: the round is skipped; go to the Clarify brief (§ 5), the round marked skipped.

## 2. Render the plan packet

By § Plan packet's shape and rules, line for line.

## 3. Launch the reviewer

Launch one reviewer with the plan packet as its whole task, by the review skill's § 2 (`skills/review/SKILL.md` in the folder `lifecycle where` prints), and print its one line. Edit nothing until the return arrives (§ Terms, *Launch*).

## 4. Act on the return

By § The plan round, step 4:

- first check each finding's evidence, by § Developer rules: one whose locations do not show what its evidence says they show, or an `inferred` or unmarked one you cannot prove, is disputed on evidence;
- fold every `Real bug` and `Drift` that holds into the plan, which stays `proposed`; an exploitable one goes in with no location or detail;
- every `Decision pending`, and every *For the maintainer* question you cannot settle, goes by its door (§ Terms): a one-way one becomes a D-row with its recommended option; a two-way one is taken, at the reviewer's recommendation or at your own pick with the reviewer's option named, and written as a `Taken:` line (§ Developer rules); a question with no option goes the same way, your answer as its recommendation;
- a finding you dispute becomes a D-row naming its kind (§ Brief rules): the reviewer's position as A, yours as B;
- a `split`: file the part split off as a capture, the template's sections above the plan, labelled as the repository's `AGENTS.md` says, and, where the settings name a board, `lifecycle board <new> Backlog`; narrow this plan to what it keeps, and name `<new>` on the brief's *Reviewed* line;
- write the plan back as in § 1 step 4, with the round's mark in the same write;
- one plan round per plan: what stays disputed goes to the maintainer, never to a second pass.

## 5. The Clarify brief

Render it by § Clarify brief's template and § Brief rules:

1. The first line links the issue, from `gh issue view <N> --json url -q .url`, and names the task in a few plain words; the goal is the issue's *Goal* in one plain sentence.
2. *Taken alone*, by § Brief rules: the plan's `Taken:` lines that might draw the maintainer's attention, and every follow-up filed, its title and link by `gh issue view <M> --json title,url`. A gap in a kit guide is named as `lifecycle gap` printed it, its title and link read with `--repo` on the repository it landed in, and each `Not filed:` entry in the plan is carried with its title and why (§ Developer rules).
3. *Reviewed* is read off the round's mark.

## 6. On "go"

1. Write each answer into the plan: the pick and its reason in place of the recommendation, and whatever it changes in the scenarios or the boxes. A D-row left unanswered takes its recommendation, written as taken at "go". A vetoed choice taken alone: its `Taken:` line gives way to the maintainer's pick, and the plan is made that way.
2. Set `**Status:** accepted <YYYY-MM-DD>`, write the body back as in § 1 step 4, and only then write code.
3. A correction to the drawing before "go" is a redraw and a brief rendered again, not a new round.
4. A skipped round with nothing to answer awaits no "go" (§ The plan round): set the plan accepted and go on, unless it carries a drawing.
5. "go" opens implementation, never landing: *Complete* waits for its own go-ahead. From here the plan changes only by its *Departures* (§ Developer rules).
