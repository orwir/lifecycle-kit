---
name: handback
description: Render the hand-back brief of the work round for the task done in this session (the method's task_review.md) — the one thing the maintainer reads
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named). A PR number is told from an issue, and its issue found, as the review skill's § 0 step 6 says (`skills/review/SKILL.md` in the folder `lifecycle where` prints); below, `<issue>` is the issue that holds the plan.

Read `task_review.md` in the kit's `method/`, in the folder `lifecycle where` prints (`lifecycle` is on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit): § Hand-back brief's template and § Brief rules are there. This renders the work round's brief; the plan round's is the clarify skill's. You are the developer; the reader is the maintainer. The review skill ends with this render; run it on its own to render again after a correction or an answer.

## Gather, don't recall

1. **Coordinates.** `git status --short`, `git rev-parse --short HEAD`; the flow and, on a branch or PR, `gh pr view --json number,url,baseRefName,state`, an `OPEN` PR being the flow's. From this session's return packets:
   - the verdict, the strictest of the returns;
   - the count of passes, the most any one reviewer made;
   - the lenses that read the tree, each marked `(no guard)` or `(pasted)` as it was launched;
   - `round skipped` for an untracked micro-task.
2. **The tree.** *In the tree* is the tree after the round's fixes, not the hand-off's summary; *Visible* links each drawing the task closed.
3. **Decisions pending,** numbered D1, D2, …: every `Decision pending` of every return, every finding you disputed, every *For the maintainer* question you could not settle and every work-round `split`; none the maintainer already answered at this hand-back.
4. **Taken alone:**
   - the hand-off's *Decisions taken alone*;
   - every box dropped or added beyond the accepted plan, or beyond the ticket's boxes for an issue with no `## Plan`;
   - every *Departures* entry in `<issue>`;
   - every fix that picked an option or moved scope;
   - every deferred finding, its title verbatim by `gh issue view <new> --json title`; one reported privately has no issue, and *Round* counts it with its channel and private link;
   - every issue filed on the kit for a gap in a kit guide, named `<kit owner>/<kit repository>#M`, its title by `gh issue view <M> --repo <kit owner>/<kit repository> --json title`, the repository being the one the kit's `.claude-plugin/plugin.json` names;
   - then drop what the maintainer decided at *Clarify* or answered or vetoed at this hand-back (*In the tree* shows it), what only describes the implementation, and every fix inside the plan's scope, a count in *Round*.
5. **The gate** is `gate.commands`, else AGENTS.md § Commands' lint and tests. If the tree changed after its last run in this session, run it now; a red gate goes back to the review skill's § 3, and no brief is rendered on it. The numbers go under *Verified*; what still could not run under *Not run*, with its reason; a repository with no gate reads `gate not run`.
6. **Round.** Count the findings of every return, one defect two returns report counted once, by outcome — fixed, deferred, reported privately, recorded, to answer — and name the disputed ones by their D-number.
7. **Next.** The maintainer's action, then only the non-routine *Complete* steps.

## Output

The brief alone, by § Brief rules.
