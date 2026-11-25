---
name: handback
description: Render the hand-back brief of the work round for the task done in this session (the method's task_review.md) — the one thing the maintainer reads
argument-hint: "[issue or PR number; empty for an untracked task]"
---

Task: $ARGUMENTS — an issue number, a PR number, or empty for an untracked task (where nothing substitutes `$ARGUMENTS`, what the maintainer named). A PR number is told from an issue, and its issue found, as the review skill's § 0 step 6 says (`skills/review/SKILL.md` in the folder `lifecycle where` prints); below, `<issue>` is the issue that holds the plan.

Read `task_review.md` in the kit's `method/`, in the folder `lifecycle where` prints (`lifecycle` is on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit): § Hand-back brief's template and § Brief rules are there. This renders the work round's brief; the plan round's is the clarify skill's. You are the developer; the reader is the maintainer. The review skill ends with this render; run it on its own to render again after a correction or an answer.

## Gather, don't recall

1. **Coordinates.** `git status --short`, `git branch --show-current`; the flow and, on a branch or PR, `gh pr view --json number,url,baseRefName,state`, an `OPEN` PR being the flow's. The issue's link by `gh issue view <issue> --json url -q .url`; the task in a few plain words, and its goal in one plain sentence from the issue's *Goal*, or for an untracked task from what was asked, with a few sentences of detail. From this session's return packets:
   - the lenses that read the tree, each marked `(read-only guard off)` or `(pasted)` as it was launched, and whether any made a second pass;
   - `round skipped` for an untracked micro-task.
2. **What changed** is the tree after the round's fixes, not the hand-off's summary, a bullet with nothing to say left out; *You see* links each drawing the task closed.
   - *Under it*: `as planned`, or each departure from the accepted plan in a few words with why — every *Departures* entry in `<issue>`, every box dropped or added beyond the plan, and each entry of the build's ledger for a drawing (`design_workflow.md` step 4); for an untracked task or an issue with no `## Plan`, what changed beneath, with any box dropped or added beyond the ticket's.
   - *Size*: `lifecycle base` prints `<base>`; `git diff --shortstat <base>` gives the changed files and lines, a staged new file among them, and each path `git ls-files --others --exclude-standard` prints, every untracked file one by one, adds one file and its lines.
   - *Risk*, only where landing does what a revert does not undo (§ Hand-back brief): what it does, and how it is undone.
3. **Decisions pending,** numbered D1, D2, …: every one-way door left open (§ Terms) — a return's `Decision pending`, a *For the maintainer* question you could not settle — every finding you disputed, its kind named (§ Brief rules), every work-round `split` and every exploitable finding left unfixed where the project it is in names no private channel; none the maintainer already answered at this hand-back. Each option ends with what it takes against the tree.
4. **Taken alone.** Gather:
   - the plan's `Taken:` lines written since its acceptance, and the hand-off's *Decisions taken alone*, spend aside;
   - every fix that picked an option or moved scope;
   - every follow-up filed past the bar (§ Developer rules), its title verbatim and its link by `gh issue view <new> --json title,url`; one reported privately has no issue, and *Reviewed* counts it with its channel and private link;
   - every `Watch:` line, by its risk and its trigger;
   - every gap in a kit guide filed by `lifecycle gap`, named as it printed it (`<kit owner>/<kit repository>#M` on the kit from another repository, `#M` in this one), its title and link by `gh issue view <M> --repo <the repository it landed in> --json title,url`; and every `Not filed:` entry in the plan, with its title and why.

   Then drop what was settled at *Clarify* (the maintainer's answers and the `Taken:` lines that stood at "go") or answered or vetoed at this hand-back (*What changed* shows it), what only describes the implementation, every departure (*Under it* names it), and every fix inside the plan's scope. Of the rest, show every filed issue, every `Not filed:` entry still in the plan, every `Watch:` line, and only the choices that might draw the maintainer's attention (§ Brief rules); the others stay in the plan's `Taken:` lines and go to the commit body. An untracked task shows every one.
5. **Spent:** each spend the task made, from the hand-off's *Decisions taken alone*: its amount, on what, and where it was asked.
6. **The gate** is `gate.commands`, else AGENTS.md § Commands' lint and tests. If the tree changed after its last run in this session, run it now; a red gate goes back to the review skill's § 3, and no brief is rendered on it. *Verified* reads `gate green` and how many tests fail without the change, from the hand-off's *Verification*, the gate's own numbers left in the packet; what still could not run goes under *Not run*, with its reason; a repository with no gate reads `gate not run`.
7. **Reviewed.** Count the required findings of every return, one defect two returns report counted once, by each outcome that occurred (fixed, disputed by its D-number and kind, reported privately); after `also`, every other dispute by its D-number and kind; and every other finding sent by the private route, whatever its label, with its channel and private link.
8. **For you,** the last block: the maintainer's action, where "lgtm" lands the work when it is not the integration branch, then only the non-routine *Complete* steps. The first line ends in the status: how many D-rows step 3 found, or `ready`.

## Output

The brief alone, by § Brief rules, asked its two questions before it is printed, with nothing after *For you*.
