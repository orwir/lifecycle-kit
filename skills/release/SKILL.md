---
name: release
description: Run a release in its three phases — Prepare, Review (stop for "proceed"), Ship — by the repository's own release checklist, with any paid check on its own go-ahead
argument-hint: "[version, when the maintainer names one]"
---

Version: $ARGUMENTS — empty means you pick it (where nothing substitutes `$ARGUMENTS`, the version the maintainer named, if any).

It starts only when the maintainer asks for a release in their own message; that request covers Phase 1, and nothing past it. The checklist is the repository's own: the release checklist AGENTS.md names, usually a section of `CONTRIBUTING.md` whose heading starts with "Releasing". Read its phases and numbered steps before starting, and run the steps as written there, commands included. This skill is the order and the gates, not a second copy of the steps. `lifecycle config` → `branches` names the integration and protected branches.

## Phase 1 — Prepare

Reversible; nothing here needs a go-ahead except a paid check.

1. **The version.** Unless the maintainer named one, pick it from semver over the changes since the last tag: breaking → major, additive → minor, fixes only → patch.
2. **Ready to ship.** The milestone has no open issue, every check the checklist puts before the bump reads clean, and the comprehensive reviews that are due (`review_machinery.md` in the guides folder) are named with the trigger that fired each.
3. **The checklist's prepare steps:** bump the version in its one home, date the CHANGELOG section, commit, push the integration branch, open the release PR from it into the protected branch.
4. **A paid check** (a live eval, a paid probe) runs only on its own go-ahead: surface its price and its free twin's result, then wait.

## Phase 2 — Review: stop

Surface the PR URL, a one-paragraph summary, the checks' readings and the reviews that are due, then wait for an explicit "proceed". Corrections are worked here and you stop again:

- A finding that holds the release is fixed or reverted on the integration branch through the task workflow, then the checks run again.
- Any other correction re-reads the checks before stopping again: a reading covers only the commit it ran on.

A prior "do the release" never reaches past this stop.

## Phase 3 — Ship, on "proceed" only

The "proceed" authorizes the whole phase as one batch, with no prompt between steps: the checklist's ship steps — merge the release PR, tag, fast-forward the integration branch, publish the release, close the milestone, verify the deploy. Merge the release PR with a merge commit (`gh pr merge --merge`), never squashed and never with `--delete-branch`: its head is the integration branch, which the fast-forward needs and which outlives every release. The merge and the tag push are irreversible. Report each step with its coordinates, and anything left to the maintainer.
