---
name: handback
description: Render the hand-back brief of the work round for the task done in this session (the method's task_review.md) — the one thing the maintainer reads
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named).

Read `task_review.md` in the guides folder (`lifecycle config` → `guides.path`; `lifecycle` is on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit) first: the brief's template and rules are there. This renders the brief of the work round; the plan round's brief is the clarify skill's. You are the developer; the reader is the maintainer, who was at *Clarify* but saw nothing of the round, and answers or vetoes from the brief alone. The review skill ends with this render; run it on its own to re-render after a correction.

## Gather, don't recall

1. **Coordinates.** `git status --short`, `git rev-parse --short HEAD`; the flow and, on a branch or PR, `gh pr view --json number,url,baseRefName`. The verdict — the strictest of the returns — the round count and the lenses that read the tree come from the return packets in this session — `round skipped` for an untracked micro-task. A lens whose reviewer ran without the kit's guard reads `<lens> (no guard)` on the status line's lens list, and one read in a pasted session `<lens> (pasted)`.
2. **The tree.** *Upgrade* is there while `lifecycle upgraded` reports one: the release move and the kit changes it lists, each change it required of the repository and what was done, the templates installed whole, and what was ported and left, from the hand-off packet's *Upgrade*. *In the tree* describes the tree after the round's fixes, not the hand-off's summary. *Visible* links each drawing the task closed, so it is judged with the code.
3. **Decisions pending.** Every `Decision pending` row of every return, every finding you disputed, every *For the maintainer* question you could not settle — numbered D1, D2, …
4. **Taken alone.** The hand-off's *Decisions taken alone*; every box dropped or added beyond the accepted plan — beyond the ticket's boxes, for an issue with no `## Plan` — and every *Departures* entry in the issue; every fix that picked an option or moved scope; every deferred finding with `gh issue view <N> --json title` for the title verbatim. Drop what the maintainer decided at *Clarify*, what only describes the implementation, and every fix inside the plan's scope — that is a count in *Round*.
5. **The gate.** The gate is `gate.commands`, else AGENTS.md § Commands' lint and tests. If the tree changed after its last run in this session, run it now. The numbers go under *Verified*; what still could not run under *Not run* with its reason, and a repository with no gate at all reads `gate not run`.
6. **Round.** Count the findings of every return, one defect two returns report counted once, by outcome — fixed, deferred, recorded, to answer — and name the disputed ones by their D-number.
7. **Next.** The maintainer's action, then only the non-routine *Complete* steps. When `lifecycle guides check` lists a guide this task changed, one of them is its push to the kit.

## Rules

- The template as chat markdown, exactly: the same bold leads, bullets and order, with a lead's content where the template puts it; no headings, tables or fenced block, nothing before the first line and nothing after *Next*.
- No finding ids: the maintainer never sees the packets, so a row says in words what it rests on.
- "I" is the developer, "you" the maintainer.
- Nothing that is not in a packet or the tree; no new argument.
- About twenty-five lines.

## Output

The brief alone.
