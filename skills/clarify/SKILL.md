---
name: clarify
description: Run the plan round at Clarify for an issue (the method's task_review.md) — the plan in the issue, the plan packet, the reviewer, the Clarify brief
argument-hint: "<issue number>"
---

Task: $ARGUMENTS — the issue number given with the invocation (where nothing substitutes `$ARGUMENTS`, the number the maintainer named). A task with no issue has no plan and skips this round; the review skill runs its work round with an `untracked:` packet.

## 0. Before anything

- `lifecycle` is the kit's command: on PATH where the kit's Claude plugin is on, otherwise `bin/lifecycle` in a checkout of the kit.
- When the settings name a board (`lifecycle config`), `lifecycle board <N> "In Progress"` first.
- `lifecycle doctor --json`. A finding whose fix is `upgrade`, with no task's edits in the tree: run the upgrade skill now, alone, before the ticket. It ends in its own hand-back and lands by its own *Complete*; this round starts once it has landed. With an accepted plan and its edits in the tree, the upgrade waits until the task lands, as the upgrade skill's opening says. A `block` whose fix is `adopt` or `update-kit`, or any failure of the command: stop and tell the maintainer what it printed. Anything else: carry on.
- `lifecycle config` prints the repository's settings. Below, `<method>` is the `method/` folder in the folder `lifecycle where` prints: the kit's guides, served from the installed kit.
- Read `<method>/task_review.md`: the plan packet, the plan return, the Clarify brief and the developer rules are there, and the plan's sections are the repository's issue templates (`.github/ISSUE_TEMPLATE/`). Read `AGENTS.md` § Task workflow too: a repository may add steps to this round (a drawing, an evidence source), and you do them where it says.

You are the developer and you run the whole round here, before any code. The maintainer reads only the brief at the end, so print nothing else but the one line in step 3.

## 1. Write the plan into the issue — gather, don't recall

1. **The ticket.** `gh issue view <N>` and the code the change touches: every path, caller and entry point it meets. A *Plan* already in the issue is where this session continues: `proposed` is checked against the code and goes on to its round; `accepted` means *Clarify* is over, and the work continues from its ticked boxes and the tree.
2. **The root cause.** A bug's root cause is a hypothesis until real data confirms it — the evidence sources AGENTS.md names (logs, the database, a live probe). Before the plan is written, the issue's *Root cause* says what holds, with the evidence as coordinates.
3. **The plan.** The template's `## Plan` with `**Status:** proposed`, as the body's last section, where the template puts it. A WHEN … THEN line per scenario, failure paths included; *Seams*; a box per path; the D-rows; *Verification*; *Departures* `none`. An issue in an older shape gets its plan now: its top-level technical details, options and verification move into it, re-checked against the code.
   - Every D-row names the layer it touches — one AGENTS.md names, such as the runtime, a prompt or an eval — or none, for a docs or process choice.
   - *Verification* names a test per WHEN line. A scenario a test cannot score names how it is scored, or says `not covered: <why>`. That each test fails without the change is proven at the work round, on a worktree of the base; it is not claimed here.
   - Coordinates, never payload: an attack is described by its shape and where the evidence sits, never quoted. No live person is named: invent a name of the same shape, or give a count.
4. **Write it.** Fetch the body fresh with `gh issue view <N> --json body -q .body`; write the whole new body to a file in a scratch folder outside the tree, everything outside the plan as it stands; then `gh issue edit <N> --body-file <file>`. Every later change to the plan goes in the same way.
5. **The drawing.** When AGENTS.md puts the change under a design workflow (what a person sees on a surface), draw it now, as part of the plan, by that workflow. Each open decision is a D-row; the brief's *Visible* links the drawing. The reviewer cannot see it, so the packet states the drawing's region and decisions in words.
6. **The shape.** Which of the guide's four shapes the plan has, and where it meets it — or none. No shape skips the round: go straight to the Clarify brief (§ 5), the round marked skipped. A drawn plan always ends at the brief, since its "go" accepts the drawing.

## 2. Render the plan packet

The guide's shape, line for line. *Read first*: the docs, ADR sections or guides the plan is held to, or `none`. *Rests on*: each fact about the code the plan assumes, with its `path:line`. *Taken alone*: the plan's choices the maintainer has not made. *Open*: what you could not settle.

Claims with coordinates, never the plan pasted: the reviewer reads it in the issue. Self-contained, with no reference to this conversation; no pre-arguing.

## 3. Launch the reviewer

Launch it in the background with the plan packet as its whole task. The reviewer definition carries both rounds' rules, so add nothing to the packet. The first of these the agent can do:

1. **The kit's reviewer agent** — in Claude Code, `Agent` with `subagent_type: "lifecycle:reviewer"` and `run_in_background: true`. The kit's hook holds it to commands that read.
2. **A general-purpose subagent** whose task is the definition — `agents/reviewer.md` in the folder `lifecycle where` prints, without its front matter — above the packet. Use it where the first is not listed (a plugin installed in this session is not always picked up at once). No guard fires for it: the brief's status line marks that lens `(no guard)`.
3. **A fresh session the maintainer opens**: write the definition and the packet to one file in a scratch folder outside the tree, ask the maintainer to paste it into a new session and paste the return back. The brief's status line marks that lens `(pasted)`.

Print one line: the reviewer is reading the plan for the task and the Clarify brief follows — or, for a pasted session, the request to paste the file, with its path. Do not print the packet. Edit nothing until the return arrives; the reviewer is reading the plan in the issue.

## 4. Act on the return

- Fold every `Real bug` and `Drift` into the plan, which stays `proposed`. Every `Decision pending`, and every *For the maintainer* question you cannot settle, becomes a D-row with its recommended option.
- A finding you dispute becomes a D-row too: the reviewer's position as A, yours as B.
- `split`: file the part split off as a capture — the template's sections above the plan, labelled as the repository's `AGENTS.md` says, and, when the settings name a board, `lifecycle board <new> Backlog` — narrow this plan to what it keeps, and name the new issue on the brief's status line.
- One plan round per plan: what stays disputed goes to the maintainer, never to a second round. Write the plan back as in step 1.

## 5. The Clarify brief

Render it by the guide's template, exactly, as chat markdown: no headings, tables or fenced block, nothing before the first line and nothing after *Next*. It points at the plan instead of repeating it. No finding ids — a row says in words what it rests on; "I" is the developer, "you" the maintainer; each D-row's question names its layer. About fifteen lines; past twenty-five, the task wants a split.

## 6. On "go"

- Write each answer into the plan — the pick and its reason in place of the recommendation, and whatever the answer changes in the scenarios or the boxes — set `**Status:** accepted <YYYY-MM-DD>`, and write the body back as in step 1. Only then write code.
- A correction to the drawing before "go" is a redraw and a brief rendered again, not a new round.
- A skipped round with nothing to answer awaits no "go": set the plan accepted and go straight on — unless the plan carries a drawing, which waits for one.
- "go" opens implementation, not landing: *Complete* waits for its own go-ahead. From here the plan changes only by its *Departures*, written when they happen; one that is user-visible, hard to undo or changes scope stops for the maintainer first.
