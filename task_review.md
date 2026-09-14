# Task review

The review round between a task's *Implement & stop* phase and its hand-back to the maintainer: the developer session hands a **hand-off packet** to a reviewer session that has no author context, the reviewer reads the tree against it and hands a **return packet** back, and the developer's reply per finding rides with both into the hand-back. Written for the two AI roles and for the maintainer who reads the result. The packets are plain prompts, so any assistant can carry them; in Claude Code `/handoff` and `/review` (`.claude/commands/`) render them.

It does not cover the maintainer's own read of the diff, the comprehensive passes (`codebase_review.md`, `ux_review.md`, `design_review.md`), or a release gate.

## When it runs

Every task gets one round unless it is an untracked micro-task, and then the hand-back says so. It runs after the local gate is green and before the hand-back, in both flows: the packet points at the uncommitted tree on `develop`, or at the branch's diff against `develop`. Nothing is pushed for it — the PR, when the work rides a branch, is opened at *Complete* as before.

A second round is bought only by a `Real bug` in the first. Anything still disputed after that goes to the maintainer, never to a third round between agents.

The round answers what the gate cannot. Lint, format, the suite and the coverage floor are settled by the push hook, so neither packet re-argues them; the reviewer's questions are the ones only a reader can answer — scope, decisions, invariants, tests, prose, docs, and what could go.

## The loop

1. **Developer** — `/handoff <issue or PR number>` in the session that did the work renders the hand-off packet. Paste it into a fresh session.
2. **Reviewer** — `/review <packet>` in that fresh session. The reviewer reads the ticket and the tree, verifies every claim, and renders the return packet. Paste it back.
3. **Developer** — act on every finding the return marks required, then reply per finding id: `fixed <how>` / `disputed <why>` / `deferred #N`.
4. **Hand-back** — the hand-off, the return and the reply together are what the maintainer reads at the gate before *Complete*. The disputed ids and every `Decision pending` row are the maintainer's part; the rest is already settled.

## Hand-off packet

Claims with coordinates, never the diff: the reviewer reads the tree itself, and a pasted diff is the author's framing of it. Self-contained — no "as discussed" — because the reader saw none of the discussion.

```
Review request: #<N> <title>        Flow: direct on develop | branch <name> | PR #<M>
Diff: git diff (uncommitted; base <sha>) | git diff develop...HEAD | gh pr diff <M>
New files: <paths, which git diff does not show> | none
Ticket: gh issue view <N> | untracked: <one line of intent>

Summary: <what and why, one paragraph; what was removed, or why nothing could go>

Reconciliation (one line per ticket box):
- [MODIFY] <path> — landed | dropped: <why> | added beyond the ticket: <why>
- Deviation from the ticket's mechanism: <named> | none

Decisions taken alone: <options picked early; hypotheses left untested and where they are marked; spend> | none

Where to look (2-3 hunks):
- <path:line> — relies on <invariant>; enforced by <test> | stated only

Verification: <N passed, coverage X%, lint clean>; fails without the change: <test ids>
NOT RUN: <what and why> | nothing
Docs: <files touched per the change → doc mapping>; CHANGELOG: "<the line>" | none, because <why>

Return the review in the return-packet shape from docs/guides/task_review.md. Read-only on the tree.
```

## Return packet

Every finding is a commitment: a location, a severity from the seven-label vocabulary in [codebase_review.md § Severity vocabulary](codebase_review.md#severity-vocabulary), evidence, and the action it requires. `Real bug` and `Drift` are required; `Cleanup` and `Minor` are fixed only inside the diff; `Acceptable` is recorded; `Decision pending` goes to the maintainer with a recommended option.

```
Verdict: approve | corrections | split: <what lands now, what is filed>

Findings:
| id | location    | severity | claim | evidence | required action |
| R1 | <path:line> | Real bug | ...   | ...      | ...             |

Verified clean: scope yes | decisions yes | invariants yes | tests yes | prose yes | docs yes | simplicity yes
  (a finding id in place of "yes" where it is not)
For the maintainer: <questions the reviewer could not settle; every Decision pending with a recommended option> | none

Developer: act on Real bug and Drift; reply per id — fixed <how> | disputed <why> | deferred #N.
```

## Developer rules

- The packet is claims with coordinates. Never paste the diff or a file's contents; point at the command that shows them.
- Every section is filled or says `none`. An empty *Decisions* is a claim too, and the reviewer checks it.
- `NOT RUN` is honest: a gate that did not run in this session after the last edit runs before the packet is rendered, and what still could not run is listed with its reason.
- Do not pre-argue findings; the reviewer has not made any.
- Reply per id, and a disputed finding stays disputed in the hand-back. It is the maintainer's call, not a second argument to the reviewer.

## Reviewer rules

- Fresh session, read-only on files. `git diff`, `git show`, `git log`, `gh issue view`, `gh pr diff`, `gh pr view`, `ruff check` and `ruff format --check` are allowed; `ruff format`, any `--fix`, `git stash`, `git checkout` and every edit are not — the developer's session shares the tree. `pytest` is the developer's too: two `--cov` runs on one tree share the coverage files, and the second erases the first's number.
- The packet is the map; the tree is the territory. Read the whole diff by the command the packet gives and every new file it lists, in full. Verify every claim against them: read the test the packet says fails without the change, open the doc it says it updated, check the ticket box it says landed.
- Ask, in this order:
  1. **Scope** — does the diff do what the ticket asked, and only that? Drive-by changes are findings even when correct.
  2. **Decisions** — would the maintainer have made each one the packet lists, and each one it omits?
  3. **Invariants** — is every invariant the change relies on enforced by a test or a loader check, or only stated in prose?
  4. **Tests** — does each new behaviour have a test that fails without it, and is the database real where it could be?
  5. **Prose** — comments within budget, present tense, why not what, no tombstones or issue-number changelogs.
  6. **Docs** — the change → doc mapping applied, and the CHANGELOG line one claim, user-visible, under the cap.
  7. **Simplicity** — what could go, and does any abstraction the diff touches still earn its shape?
- Every finding cites `path:line` and says what breaks or which rule it breaks. A finding without evidence is a question, and goes under *For the maintainer*.
- Name what was verified clean, so silence is never ambiguous.
- Never fix, rewrite or propose a redesign; the round is a read. A simplification is a `Decision pending` with the smaller shape named.
- A built-in bug finder (`/code-review` in Claude Code) may run as a first pass; its findings enter the table like any other, with the reviewer's own evidence.

## Where the packets land

Chat carries both packets in both flows, and nothing reaches GitHub before the maintainer's approval. At *Complete*, a feature branch's PR takes the hand-off as its body with a `Closes #N` line added and the return as a comment (`gh pr review --comment --body-file <file>`); on `develop` the close-out comment may quote the verdict.
