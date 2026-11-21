---
name: release
description: Run a release in its three phases — Prepare, Review (stop for "proceed"), Ship — by the repository's own release checklist, with any paid check on its own go-ahead
argument-hint: "[version, when the maintainer names one]"
---

Version: $ARGUMENTS — empty means you pick it (where nothing substitutes `$ARGUMENTS`, the version the maintainer named, if any).

It starts only when the maintainer asks for a release in their own message; that request covers Phase 1, and nothing past it. The checklist is the repository's own: the release checklist AGENTS.md names, usually a section of `CONTRIBUTING.md` whose heading starts with "Releasing". Read its phases and numbered steps before starting, and run the steps as written there, commands included. This skill is the order and the gates, not a second copy of the steps. `lifecycle config` names the integration branch (`branches.integration`) and the release workflow (`release.workflow`).

A release runs on the integration branch, or, for a fix that cannot wait for what the integration branch holds, on a `hotfix/<name>` branch cut from the last release's tag: that branch is *the release branch* below. Nothing pushed from a checkout ships. The release workflow, dispatched on the commit the review read, builds, ships and creates the tag.

## Phase 1 — Prepare

Reversible; nothing here needs a go-ahead except a paid check.

1. **The version.** Fetch the tags first (`git fetch --tags origin`): the release workflow creates them on GitHub, so a clone holds the last release's tag only after a fetch. Unless the maintainer named one, pick it from semver over the changes since the last tag (`git describe --tags --abbrev=0`): breaking → major, additive → minor, fixes only → patch. A hotfix branch takes the patch after the tag it was cut from.
2. **Ready to ship.** On the integration branch, the milestone has no open issue. Every check the checklist puts before the bump reads clean, and the comprehensive reviews that are due (`review_machinery.md` in the kit's `method/`, in the folder `lifecycle where` prints) are named with the trigger that fired each.
3. **The checklist's prepare steps:** bump the version in its one home, date the CHANGELOG section, commit those files by name, push the release branch.
4. **A paid check** (a live eval, a paid probe) runs only on its own go-ahead: surface its price and its free twin's result, then wait.

## Phase 2 — Review: stop

Surface the compare link from the last tag to the release branch's head (`https://github.com/<owner>/<repo>/compare/v<last>...<head>`, the head as a full SHA), a one-paragraph summary, the checks' readings and the reviews that are due, then wait for an explicit "proceed". The head this stop shows is the one Phase 3 ships. Corrections are worked here and you stop again:

- A finding that holds the release is fixed or reverted on the release branch through the task workflow, then the checks run again.
- Any other correction re-reads the checks before stopping again: a reading covers only the commit it ran on, and the next stop shows the new head.

A prior "do the release" never reaches past this stop.

## Phase 3 — Ship, on "proceed" only

The "proceed" authorizes the whole phase as one batch, with no prompt between steps:

1. **Probe a new release workflow.** The first release through a release workflow probes it first, before the real dispatch, each probe shipping nothing that was not reviewed even if its check is broken:
   - `lifecycle release <the commit before the head> --ref <release branch>`: expect exit 3, refused as moved.
   - `git push origin <head>:refs/heads/probe/<version>`, then `lifecycle release <head> --ref probe/<version>`: expect exit 1, refused as a wrong ref. Delete the probe branch on GitHub afterwards.
   - Once step 2's `lifecycle release` has printed `release: dispatched … run <id>`, and while that run is still going: `gh workflow run <workflow> --ref <release branch> -f commit=<the commit before the head>`. Whatever the real run's end, this one cannot ship: expect it to wait while the real run goes, then to be refused as moved. Read its run (`gh run list --workflow <workflow> --limit 2`, then `gh run view <id>`) and report it; one that did not wait shows the workflow's `concurrency` is wrong.

   Any other outcome stops the phase: report it.
2. **Ship.** Where `release.workflow` is null, the repository ships by the checklist's own ship steps: run those. Otherwise `lifecycle release <head> --ref <release branch>`, with the head the last stop showed. It dispatches the release workflow and watches the run to its end, which takes as long as the build and the deploy: run it where a long command may run, in the background where you can. Its last line says how it ended, and its exit code matches:
   - 0, `shipped`: shipped and tagged.
   - 3, `refused: <branch> moved since the review`: go back to Phase 2 on the new head.
   - 1: refused or failed at the step the line names, or nothing was dispatched (a line starting `lifecycle:`, GitHub's refusal among them). Report it with the run's link; a run that failed after its deploy started may have shipped in part, and the rollback is the maintainer's call.
   - 4, `in flight`, or no last line at all (the shell cut the command off): the run may still ship and tag. Report the run, and dispatch nothing again until it has ended.
   - 2 is a usage error from the command line, not a release outcome: fix the command.

   Anything but `shipped` ends the phase here: steps 3 and 4 run only after it.
3. **A hotfix branch lands.** Once it shipped, merge it into the integration branch with a merge commit (`git merge --no-ff`), never squashed, so the tag stays in the integration branch's history. Push it, then delete the hotfix branch, remote and local. A conflict stops for the maintainer. The merge carries the fix's `Closes #N` to the default branch; when the settings name a board, `lifecycle board <N> Done`.
4. **The checklist's other ship steps:** close the milestone, verify the deploy, and whatever else it lists.

The dispatch is irreversible: the workflow ships as soon as its checks pass. Report each step with its coordinates, and anything left to the maintainer.
