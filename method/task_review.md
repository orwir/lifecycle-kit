# Task review

A task's two review rounds, each read by a reviewer agent with no author context, and the two briefs the maintainer reads; written for those agents and that maintainer. It does not cover the maintainer's own read of the diff, the comprehensive reviews (`codebase_review.md`, `ia_review.md`, `ux_review.md`, `design_review.md`, `llm_review.md`, all on `review_machinery.md`), or a release gate.

The kit's `clarify` skill runs the plan round, its `review` skill the work round, its `handback` skill the hand-back brief and its `complete` skill the close-out; the reviewer's instructions are the kit's `agents/reviewer.md`.

## Terms

- **Round:** the **plan round**, at *Clarify*, before any code; or the **work round**, between *Implement & stop* and *Complete*. Nothing else is a round.
- **Pass:** one reviewer's read within a round. In the work round only a `Real bug` buys that reviewer a **second pass**, and there is never a third: what it leaves disputed is a D-row.
- **Lens:** the questions a reviewer asks: `base`, `person-facing` or `model-facing`; a **lens reviewer** is a person- or model-facing one (*Lens reviewers*).
- **Packet:** the developer's plan packet and hand-off packet, and the reviewer's plan return and return packet. A packet is never shown to the maintainer.
- **Brief:** what the maintainer reads of a round, the Clarify or the hand-back brief.
- **D-row:** a question a brief puts to the maintainer, with options and a recommended one.
- **Required:** a finding the severity table marks so (*Return packet*).
- **Accepted:** a plan whose status reads `accepted <date>`, set at the maintainer's "go", or where *The plan round* awaits none.
- **Launch:** a reviewer starts as a fresh agent whose whole task is its packet: a subagent where the assistant can launch one, otherwise a fresh session the packet is pasted into, with the return pasted back. From the launch until the return arrives, the plan or the tree is the reviewer's: nothing in it is edited.
- **The operating contract:** the repository's `AGENTS.md`. **Triage:** the maintainer's validation of an issue as ready to work, on a board its move from Backlog to Ready. **Spend:** money a task spent or asks to spend, such as a paid check.

In the templates, `<…>` is a slot, `[…]` an optional part and `|` between alternatives a choice; inside a table's cells, alternatives are joined by "or".

## When it runs

| Task | Plan round | Work round |
| --- | --- | --- |
| tracked, the plan has one of the four shapes | runs | runs |
| tracked, the plan has none | skipped: the plan is still written into the issue, and the Clarify brief says so | runs |
| untracked | skipped: no issue holds a plan | runs, with an `untracked:` packet |
| untracked micro-task: one obvious change, nothing to decide | skipped: no plan | skipped, and the hand-back brief says so |

- **The four shapes,** where plans have shipped holes: a rule that must hold at more than one entry point; persisted, billed, auth or safety state; a wait, retry or failure the user sees; a decision that wants an ADR. One plan round per plan; what it leaves disputed is the maintainer's.
- **The work round** runs once the local gate is green, its review before the hand-back and its step 5 before *Complete*, on the uncommitted tree or a branch's diff. Nothing is pushed for it; on a branch, the PR is opened at *Complete*.
- **An untracked task** puts nothing on the board, and its hand-back brief is its only record, so it finishes in its session. One that needs a second session, or makes a decision worth keeping, gets an issue then and is tracked from there.
- **The rounds answer what the gate cannot:** lint, format, the suite and the coverage floor are the push hook's, and no packet re-argues them.

## The plan round

The developer session runs the whole round. The maintainer sees one line when the reviewer launches and the Clarify brief when the round ends, and nothing else.

1. **Plan.** The developer reads the ticket and the code the change touches, and writes the issue's *Plan* with `Status: proposed`, before the round.
2. **Hand off.** The developer launches the reviewer with the plan packet.
3. **Review.** The reviewer reads the plan against the code (*Reviewer rules*) and returns the plan return.
4. **Act.** The developer folds every required finding into the plan, an exploitable one with no location or detail (*Return packet*). A disputed finding becomes a D-row (*Brief rules*). A `split`: the part split off is filed as its own issue, and the plan narrowed to what it keeps.
5. **Accept.** The developer renders the Clarify brief. The maintainer answers its D-rows and says "go"; the developer writes each answer into the plan's *Decisions*, sets `Status: accepted <date>`, and only then writes code.

A skipped round runs steps 1 and 5. When a skipped round's brief has nothing to answer, the plan is clear, the task having passed triage, so no "go" is awaited: the developer sets the plan accepted and goes straight on. A plan that carries a drawing still waits for "go", which accepts the drawing.

## Plan packet

Read by the reviewer. Claims with coordinates, never the plan pasted: the reviewer reads it in the issue. Self-contained.

```
Plan review: #<N> <title>
Ticket: <the command or link that shows issue N>
Shape: <which of the four, and where the plan meets it>
Read first: <the docs, ADR sections or guides the plan is held to> | none
Rests on: <facts about the code the plan assumes, each with a coordinate — "<rule> is enforced only in <path:line>"> | none
Taken alone: <choices in the plan the maintainer has not made> | none
Open: <what the developer could not settle> | none
```

## Plan return

Read by the developer: the return packet's form, with the plan questions. Only findings that change the plan count: `Real bug` (the plan as written ships a defect), `Drift` (it contradicts the code, a doc or an ADR), `Decision pending` (the maintainer's call, with a recommended option). Wording and taste are not findings.

```
Verdict: approve | corrections | split: <what this issue keeps, what is filed>

Findings:
| id | location                    | severity | claim | evidence | action |
| P1 | <plan section or path:line> | Real bug | ...   | ...      | ...    |

Verified clean: scale yes · seams yes · defaults yes · state yes · changes yes · decisions yes · reuse yes
  (a finding id in place of "yes" where it is not)
For the maintainer: <questions the reviewer could not settle; every Decision pending with a recommended option> | none
```

## Clarify brief

What the maintainer reads before any code: the issue holds the plan, and the brief what must be answered and what may be vetoed, by *Brief rules*.

```
**Plan #<N>** <title>
<the shape | no shape> · plan round <approve | corrections | split: <what this issue keeps, what is filed> | skipped>[ (no guard) | (pasted)] · <n> decision(s) to answer | nothing to answer

**The plan**
- Visible: <what a user or operator will see differently | nothing>
- Under it: <the approach, in a sentence or two>
- Seams: <where the rule holds | one surface>

**Scenarios to check** | none
- WHEN <situation> THEN <outcome>

**Decisions pending** (a letter each) | none
**D1.** <the question, naming its part, ending in "?">
- A: <option>. <consequence>
- B: <option>. <consequence>
- Recommended A: <why>.

**Taken alone** (veto by naming the row) | none
- <what> — <why>.

**Round** <k> findings · <n> folded into the plan · <n> to answer (D…) · <D… disputed | none disputed> | skipped, no shape

**Next** <answer D1, then | > "go" | nothing to answer, no shape: going ahead.
```

## The work round

The developer session runs the whole round. The maintainer sees one line when the reviewers launch, the hand-back brief when the round ends, and the brief again only where step 5 renders it; nothing else.

1. **Hand off.** The developer renders the hand-off packet and launches the reviewers its lenses call for (*Lens reviewers*) at once, each with the packet and its own *Lens* line.
2. **Review.** Each reviewer reads the tree against the packet (*Reviewer rules*) and returns its return packet.
3. **Act.** The developer fixes every required finding and every `Cleanup` and `Minor` inside the diff — one defect two returns report is one finding — and re-runs the gate. What the brief must ask becomes a D-row (*Brief rules*). A `Real bug`'s reviewer gets its second pass: a reply per finding id — `fixed <how>` / `disputed <why>` / `deferred #N` / `reported privately` — to the same reviewer, which keeps its context, and its second return is acted on the same way. A `disputed` reply is for the reviewer's information: the dispute goes to the brief. Without a second pass, no reply is written: the brief's *Round* line carries the tally.
4. **Hand back.** The developer renders the hand-back brief.
5. **Land.** The maintainer answers the brief's D-rows, may veto a *Taken alone* row by naming it, and gives *Complete*'s go-ahead, in one message or several. Before anything lands, the developer makes each answer: its pick and reason go under the plan's *Departures* (for an untracked task, into the commit body alone), the tree is made the pick where it is not, and the gate runs again. A pick bigger than the size the brief stated, and any veto, which the brief gives no size, end in the brief rendered again, and *Complete* waits for a new go-ahead. That brief shows a made answer or veto only in *In the tree*.

### Lens reviewers

Every diff is read by the base reviewer, and a diff that touches what a person or a model reads by that lens's reviewer too, one per lens however many of its surfaces the diff touches, asking what the comprehensive reviews would otherwise find months later:

| Lens          | Launched when the diff touches                                                   | Asks                                                                          |
| ------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| base          | anything                                                                         | the work-round questions (*Reviewer rules*), then `codebase_review.md` § At task time |
| person-facing | what a person reads or drives: `[web]` `[desktop]` `[tui]` `[cli]` `[bot]`       | § At task time of `ia_review.md`, `ux_review.md` and `design_review.md`       |
| model-facing  | what a language model reads, or the eval that scores its replies: `[llm]`        | `llm_review.md` § At task time                                                |

- The surface tags are `review_machinery.md`'s; the table's rule decides which lens a diff launches, and `review.lenses` in `.lifecycle.toml` names each lens's usual paths and its references.
- A lens reviewer asks only its lens's questions, against the references they name — the intent doc's IA section, the design-language reference, the prompt documentation — so no question is asked twice. A question the diff's surface does not have reads `n/a` in *Verified clean*, with why.

## Hand-off packet

Read by the reviewer: claims with coordinates, never the diff, and self-contained. The diff command shows every edit, uncommitted ones included, in a form the reviewer's read-only guard runs. Never paste a file's contents either: point at the command that shows them.

```
Review request: #<N> <title> | untracked: <one line of intent>
Lens: base | person-facing | model-facing
Flow: direct on <integration>, uncommitted (base <sha>) | branch <name> | PR #<M>, checked out here
Diff: git diff HEAD | git diff --merge-base <integration>
New files: <paths, which git diff does not show> | none
Ticket: <the command or link that shows issue N> | untracked
Read first: <the docs, ADR sections or guides the diff is held to, beyond the operating contract> | none

Summary: <what and why, one paragraph; what was removed, or why nothing could go>

Reconciliation (one line per box in the plan):
- <the box's tag> <path> — landed | dropped: <why> | added beyond the plan: <why>
- Departures from the accepted plan: <as recorded in the issue> | none

Scenarios (one line per scenario in the plan):
- WHEN <situation> — <test id> | not covered: <why>

Decisions taken alone: <options picked without the maintainer; hypotheses left untested and where they are marked; spend> | none

Where to look (2-3 hunks):
- <path:line> — relies on <invariant>; enforced by <test> | stated only

Verification: <N passed, coverage X%, lint clean>; fails without the change: <test ids>
NOT RUN: <what and why> | nothing
Docs: <files touched per the change → doc mapping>; CHANGELOG: "<the line>" | none, because <why>
```

## Return packet

Read by the developer. Every finding is a commitment: a location, a severity from the seven labels of [review_machinery.md § Severity vocabulary](review_machinery.md#severity-vocabulary), evidence, and its action. In a task the action is this table's, in place of the vocabulary's defaults:

| Severity         | In a task                                                                     |
| ---------------- | ----------------------------------------------------------------------------- |
| Real bug         | required: fixed before the hand-back                                          |
| Drift            | required: fixed before the hand-back                                          |
| Drift-prone      | deferred: filed with its trigger and plan, fixed when it fires                |
| Cleanup          | fixed inside the diff; outside it, left                                       |
| Minor            | fixed inside the diff; outside it, left                                       |
| Acceptable       | recorded in the return                                                        |
| Decision pending | a D-row, with a recommended option                                            |

- **An exploitable finding**, whatever its label, is fixed in the task or goes by [review_machinery.md § The private route](review_machinery.md#the-private-route), never into a filed issue; one sent by the private route is counted in the hand-back as reported privately, with the channel and the report's private link. Where the repository names no private channel, an unfixed one becomes a D-row in the hand-back, which is private, and counts as reported privately. A fix for one the diff introduced is described like any other. For one in released code, no public record carries its location or detail until its fix ships: the issue and its plan, the commit, the PR's title and body, the CHANGELOG and the close-out comment.
- **The verdict:** `approve` with no required finding and nothing for the maintainer; `corrections` with either; `split` when the diff does two things that should land apart.

```
Verdict: approve | corrections | split: <what lands now, what is filed>

Findings:
| id | location    | severity | claim | evidence | action |
| R1 | <path:line> | Real bug | ...   | ...      | ...    |

Verified clean: scope yes · decisions yes · invariants yes · tests yes · truth yes · docs yes · simplicity yes · code at task time yes
  (a finding id in place of "yes" where it is not; a lens reviewer names its own questions by their leads)
For the maintainer: <questions the reviewer could not settle; every Decision pending with a recommended option> | none
```

## Hand-back brief

What the maintainer reads of the work round: a reader who was at *Clarify* but saw nothing of the round, and answers or vetoes from the brief alone, by *Brief rules*.

```
**Hand-back #<N>** <title> | **Hand-back** untracked: <one line of intent>
<approve | corrections | split proposed: D… | round skipped: untracked micro-task> · <k> pass(es) · <the lenses that read the tree, each[ (no guard) | (pasted)] | no reviewer> · <<integration>, uncommitted on <sha> | branch <name> | PR #<M>> · gate <green | not run> · <n> decision(s) to answer | nothing to answer

**In the tree**
- Visible: <what a user or operator sees differently | nothing>
- Under it: <what changed beneath that>
- Removed: <what is gone | nothing>

**Decisions pending** (a letter each) | none
**D1.** <the question, ending in "?">
- A: <option>. <consequence>
- B: <option>. <consequence>
- Recommended A: <why>. Tree now: <untouched, and A is <size in lines or files>, B is <size> | already A, and B is a <size> revert>.

**Taken alone** (veto by naming the row) | none
- <what> — <why>.
- Filed #<M> <title> — <what was found; why not here>.

**Verified** <N passed · coverage X% · lint clean · <n> tests fail without the change (<where checked>)>
**Not run** <what, why> | nothing
**Round** <k> findings · <n> fixed · <n> deferred (#…) · <n> reported privately (<channel and link>…) · <n> recorded · <n> to answer (D…) · <D… disputed | none disputed> | skipped, untracked micro-task

**Next** <answer D1, then | > "lgtm". <non-routine Complete steps | Nothing unusual at Complete.>
```

## Brief rules

Both briefs:

- **Chat markdown, exactly as the template shows:** the task, then its status; every lead bold, a list on the line after its lead, other content on the lead's line; nothing before the first line or after *Next*, and no headings, tables or fenced blocks.
- **Every row stands on its own, and names no finding id:** a row says in words what it rests on — "the reviewer asked", "disputed: the reviewer holds A, I hold B". "I" is the developer, "you" the maintainer.
- **A D-row is answerable from the brief alone:** a question ending in "?", one bullet per option with its consequence, and a last bullet with the recommended letter and its reason. The Clarify brief's question names the part of the system it touches, as `AGENTS.md` § Task workflow names them, or none for a docs or process choice. The hand-back's last bullet adds what the tree does now, with each option's size. Every `Decision pending` of a return, every disputed finding (A the reviewer's position, B the developer's), every *For the maintainer* question the developer could not settle and every work-round `split` (A the split, B the diff landed whole) is a D-row.
- **"go" or "lgtm" with a D-row left open** takes its recommended option, written into the plan as taken at the go-ahead.
- **A reviewer subagent launched without the kit's guard** is marked `(no guard)` where the status line shows it; one read in a pasted session, `(pasted)`.
- ***Taken alone*** holds only choices the maintainer has not made and might reverse. At *Clarify*: scope added to or dropped from the ticket, a mechanism the ticket did not name, a follow-up to file. At the hand-back: scope moved beyond or dropped from the accepted plan, a departure from it, a filed follow-up by number and title, a hypothesis left untested and where it is marked, spend. One sentence each, what and why, at most five; a sixth is a D-row or the close-out comment. Not a row: a description of the implementation, a choice made at *Clarify* or answered at the hand-back, a fix inside the plan's scope (a count in *Round*).
- **Nothing in a brief that is not in a packet, the plan or the tree, and no new argument.**

The Clarify brief points at the plan instead of repeating it. Its *Scenarios to check* holds the scenarios a reader might argue with — a failure path, a wait, a default — not all of them. About fifteen lines; past twenty-five, the task wants a split. "go" opens implementation, never landing.

The hand-back brief's verdict is the strictest of the returns — split over corrections over approve — its lenses are the reviewers that read the tree, its count of passes is the most any one reviewer made, and *Round* counts the findings of every return. *In the tree* is the tree after the round's fixes: three bullets with those leads, one or two sentences each. *Next* names the maintainer's action and only the non-routine *Complete* steps. About twenty-five lines; past that, the task wants a split.

## Developer rules

- A gap the task finds in one of the kit's guides is filed on the kit as an issue when it is found: what the guide says, what the task met, and the gap, in the kit's words and naming no issue or surface of the repository. It is carried in *Taken alone* as a filed follow-up, named `<kit owner>/<kit repository>#M`. The guide changes by the kit's own task, never in the repository.
- Every section is filled or says `none`. An empty *Decisions* is a claim too, and the reviewer checks it.
- `NOT RUN` is honest: a gate that did not run in this session after the last edit runs before the packet or the brief is rendered, and what still could not run is listed with its reason.
- Do not pre-argue findings.
- The plan is in the issue before the plan round, and the maintainer's answers are in it before any code: a session that picks the task up cold continues from the issue, its ticked boxes and the tree, never from a conversation it did not see.
- After acceptance the plan changes only by its *Departures*: what changed and why, written when it happens. A departure that is user-visible, hard to undo or changes scope stops for the maintainer first.

## Reviewer rules

- A fresh agent with no author context, read-only on files: the developer's session shares the tree. Commands that read are allowed, the linter and the formatter in check mode among them. Anything that rewrites the tree or its index is not: a formatter or fixer that writes, a stash, a checkout, any edit. The test suite is the developer's: two coverage runs on one tree share their coverage files. `agents/reviewer.md` and the repository's `review.allow` name the commands. In the plan round the issue is read-only too.
- In the work round the packet is the map; the tree is the territory. Read the whole diff by the command the packet gives and every new file it lists, in full. The base reviewer verifies every claim against them: reads the test the packet says fails without the change, opens the doc it says it updated, checks the ticket box it says landed. A lens reviewer verifies only the claims its own questions rest on.
- In the plan round the plan is the map and the code is the territory. Read the plan in full and every path it names, check each fact the packet says it rests on, and look for what the plan does not name: the rule's other callers, the other transports and write paths, whatever depends on the behaviour it changes.
- In the plan round, ask, in this order:
  1. **Scale** — does each scenario say what the user sees at real scale, including while it waits, retries or fails?
  2. **Seams** — does the plan name every entry point the rule must hold at — each transport, route, write path, job — and cover each, or reuse the one function that owns the rule?
  3. **Defaults** — what do absence, a cap, a truncation or an unknown value mean, and is that right for every case they cover?
  4. **State** — where does each piece of state come from, and when is it read or resolved?
  5. **Changes** — who depends on what the plan changes or removes, and is each one named?
  6. **Decisions** — is every choice the maintainer should make asked, with a recommended option, and none taken silently?
  7. **Reuse** — does existing code already do part of this, and is there a smaller shape?
- In the work round, the base reviewer asks, in this order:
  1. **Scope** — does the diff do what the accepted plan says, and only that, with every departure recorded under its *Departures*? Drive-by changes are findings even when correct.
  2. **Decisions** — would the maintainer have made each one the packet lists, and each one it omits?
  3. **Invariants** — is every invariant the change relies on enforced by a test or a loader check, or only stated in prose? Does each rule the diff adds hold at every sibling — the other entry point, writer, route, transport or reply site?
  4. **Tests** — does each scenario in the plan, and each other new behaviour, have a test that fails without it, the refused, failed, empty and capped paths included, each asserting its true reason? Can every new test fail, with no skip, glob or parametrize that can run empty? Is the database real where it could be?
  5. **Truth** — is every sentence the diff adds, or leaves beside what it changes, true of the code for each reader and state it reaches: copy, messages, help, model-facing text, docs, comments? Comments within the repository's comment budget, present tense, why not what, no tombstones or issue-number changelogs.
  6. **Docs** — the change → doc mapping applied, the CHANGELOG line one claim, user-visible, under the cap, and nothing outside the diff still naming what it removed or renamed.
  7. **Simplicity** — what could go, and does any abstraction the diff touches still earn its shape? Did the diff bolt a special case or a one-off flag onto a flow whose shape should change instead? Does a restructure delete concepts, or only move them?

  Then it asks the code review's *At task time* questions (`codebase_review.md`).
- A lens reviewer asks its lens's *At task time* questions (*Lens reviewers*), in the order each guide lists them, and none of the base reviewer's.
- Every finding cites `path:line`, or in the plan round the plan's section, and says what breaks or which rule it breaks. A finding without evidence is a question, and goes under *For the maintainer*.
- Name what was verified clean, so silence is never ambiguous.
- Never fix, rewrite or propose a redesign; the round is a read. Dead code, a stale comment or an unused export is `Cleanup`; a smaller shape for a flow is a `Decision pending`, with the shape named.
- The return is the only output: nothing before it, nothing after it.
- A built-in bug finder, where the assistant has one, may run first; its findings enter the table like any other, with the reviewer's own evidence.

## Where the packets land

The packets sit in each reviewer's task and its result, and nothing of them reaches GitHub, before the maintainer's approval or after: the rounds are the team's own process. The plan is not a packet: it lives in the issue, where the developer writes it and the maintainer accepts it, and a plan-round finding reaches GitHub only as the change it made to the plan. At *Complete*, a feature branch's PR body follows the repository's PR template, written for a reader who never saw the round: no packet field, finding id or reviewer verdict in it. What that reader needs, such as a decision, a deviation or a follow-up, goes into the PR body or an issue in their words. On the integration branch the close-out comment may quote the brief's *In the tree* bullets.
