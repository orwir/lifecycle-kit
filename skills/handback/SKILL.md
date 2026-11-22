---
name: handback
description: Render the hand-back brief of the work round for the task done in this session (the method's task_review.md) — the one thing the maintainer reads
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named). A PR number is told from an issue, and its issue found, as the review skill's § 0 step 6 says (`skills/review/SKILL.md` in the folder `lifecycle where` prints); below, `<issue>` is the issue that holds the plan.

Read `task_review.md` in the kit's `method/`, in the folder `lifecycle where` prints (`lifecycle` is on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit): § Hand-back brief's template and § Brief rules are there. This renders the work round's brief; the plan round's is the clarify skill's. You are the developer; the reader is the maintainer. The review skill ends with this render; run it on its own to render again after a correction or an answer.

## Gather, don't recall

1. **Coordinates.** `git status --short`, `git branch --show-current`; the flow and, on a branch or PR, `gh pr view --json number,url,baseRefName,state`, an `OPEN` PR being the flow's. The issue's link by `gh issue view <issue> --json url -q .url`; the task in a few plain words, and its goal in one plain sentence from the issue's *Goal*, or for an untracked task from what was asked, with a few sentences of detail. From this session's return packets:
   - the lenses that read the tree, each marked `(no guard)` or `(pasted)` as it was launched, and whether any made a second pass;
   - `round skipped` for an untracked micro-task.
2. **What changed** is the tree after the round's fixes, not the hand-off's summary; *You see* links each drawing the task closed.
3. **Decisions pending,** numbered D1, D2, …: every one-way door left open (§ Terms) — a return's `Decision pending`, a *For the maintainer* question you could not settle — every finding you disputed, every work-round `split` and every exploitable finding left unfixed where the repository names no private channel; none the maintainer already answered at this hand-back. Each option ends with what it takes against the tree.
4. **Taken alone.** Gather:
   - the plan's `Taken:` lines written since its acceptance, and the hand-off's *Decisions taken alone*, spend aside;
   - every box dropped or added beyond the accepted plan, or beyond the ticket's boxes for an issue with no `## Plan`;
   - every *Departures* entry in `<issue>`;
   - every fix that picked an option or moved scope;
   - every deferred finding, its title verbatim and its link by `gh issue view <new> --json title,url`; one reported privately has no issue, and *Reviewed* counts it with its channel and private link;
   - every issue filed on the kit for a gap in a kit guide, named `<kit owner>/<kit repository>#M`, its title and link by `gh issue view <M> --repo <kit owner>/<kit repository> --json title,url`, the repository being the one the kit's `.claude-plugin/plugin.json` names.

   Then drop what was settled at *Clarify* (the maintainer's answers and the `Taken:` lines that stood at "go") or answered or vetoed at this hand-back (*What changed* shows it), what only describes the implementation, and every fix inside the plan's scope. Of the rest, show every filed issue and only the choices that might draw the maintainer's attention (§ Brief rules); the others stay in the plan's `Taken:` lines and go to the commit body. An untracked task shows every one.
5. **Spent:** each spend the task made, from the hand-off's *Decisions taken alone*: its amount, on what, and where it was asked.
6. **The gate** is `gate.commands`, else AGENTS.md § Commands' lint and tests. If the tree changed after its last run in this session, run it now; a red gate goes back to the review skill's § 3, and no brief is rendered on it. The numbers go under *Verified*; what still could not run under *Not run*, with its reason; a repository with no gate reads `gate not run`.
7. **Reviewed.** Count the required findings of every return, one defect two returns report counted once, by each outcome that occurred — fixed, disputed by its D-number, reported privately — and every other finding sent by the private route, whatever its label, with its channel and private link.
8. **For you.** The maintainer's action, where "lgtm" lands the work when it is not the integration branch, then only the non-routine *Complete* steps.

## Output

The brief alone, by § Brief rules.
