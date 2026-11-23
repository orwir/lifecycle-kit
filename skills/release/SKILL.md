---
name: release
description: Run a release in its three phases — Prepare, Review (stop for "proceed"), Ship — by the repository's own release checklist, with any paid check on its own go-ahead
argument-hint: "[version, when the maintainer names one]"
---

Version: $ARGUMENTS — empty means you pick it (where nothing substitutes `$ARGUMENTS`, the version the maintainer named, if any).

It starts only when the maintainer asks for a release in their own message; that request covers Phase 1, and nothing past it. "ship it" alone is no such request: ask. The checklist is the repository's own: the release checklist AGENTS.md names, usually a section of `CONTRIBUTING.md` whose heading starts with "Releasing". Read its steps before starting and run them as written, commands included: this skill is the order and the gates, not a second copy of the steps. `lifecycle config` names the integration branch (`branches.integration`) and the release workflow (`release.workflow`).

A release runs on the integration branch, or, for a fix that cannot wait for what the integration branch holds, on a `hotfix/<name>` branch cut from the last release's tag, the fix already landed there by the task workflow: that branch is *the release branch* below. Where `release.workflow` names a workflow, nothing pushed from a checkout ships: the workflow, dispatched on the commit the review read, builds, ships and creates the tag.

## Phase 1 — Prepare

Reversible; nothing here needs a go-ahead except a paid check.

1. **The version.** `git fetch --tags origin` first: the release workflow creates the tags on GitHub, so a clone holds the last release's tag only after a fetch. Unless the maintainer named one, pick it by semver over the changes since the last tag (`git describe --tags --abbrev=0`): breaking → major, additive → minor, fixes only → patch. A hotfix branch takes the patch after the tag it was cut from.
2. **Ready to ship.**
   - The checklist's milestone steps, where it keeps them, a hotfix skipping them as it says: a milestone with an open issue stops the phase for the maintainer.
   - Every check the checklist puts before the bump reads clean; one that does not stops the phase for the maintainer.
   - The comprehensive reviews that are due (`review_machinery.md` in the kit's `method/`, in the folder `lifecycle where` prints) are named, each with the trigger that fired it.
3. **The checklist's prepare steps:** bump the version in its one home, date the CHANGELOG section, commit those files by name, push the release branch.
4. **CI on the pushed head:** `lifecycle ci <head> --ref <release branch>` waits on the CI that push started, for as long as it runs: run it where a long command may run, in the background where you can. Its last line says how it ended, and its exit code matches:
   - 0, `passed`, or `no CI` where no workflow runs on a push to the branch: on;
   - 1 with `failed`: stop the phase for the maintainer with the line. The release ships no red commit, on "proceed" or otherwise: the failure is fixed on the release branch through the task workflow, or its run re-run where the failure was not the commit's (`gh run rerun <id> --failed`), and read again;
   - 3, `missing`: CI is expected, but no run appeared, a `paths` filter skipping the release commit most often. Stop the phase for the maintainer with the line; on their word Phase 2 follows, its stop naming the missing reading and why, and only their explicit "proceed" ships it;
   - 5, `superseded`: the branch moved past the head: Phase 2's *The branch moved*;
   - 1 with a `lifecycle:` line (a read that failed), 4, `running`, or a last line of `ci: waiting on …` or none at all (the shell cut the wait off): CI is unread, never red or green: read it again by the same command before any stop.
5. **A paid check** (a live eval, a paid probe) runs only on its own go-ahead: surface its price and its free twin's result, then wait.

## Phase 2 — Review: stop

Surface the compare link from the last tag to the release branch's head (`https://github.com/<owner>/<repo>/compare/v<last>...<head>`, the head as a full SHA), a one-paragraph summary, the checks' readings, `lifecycle ci`'s last line on that head among them, each line a hook printed at the release commit or its push saying a check did not run, and the reviews that are due, then wait for an explicit "proceed"; "ship it" is not one: ask. The head this stop shows is the one Phase 3 ships, and it carries its own CI reading by Phase 1's step 4: 0, or a missing one this stop names. Corrections are worked here, and you stop again:

- a finding that holds the release, a red CI reading among them, is fixed or reverted on the release branch through the task workflow, and the checks run again;
- any other correction re-reads the checks: a reading covers only the commit it ran on, and the next stop shows the new head, its CI read again;
- *The branch moved* past the head the release read (Phase 1's `superseded`, or Phase 3's refusal as moved): `git pull`, then check Phase 1's version and changelog, and its milestone where the checklist keeps one, against the new head again, and fix any by one more commit on top, the version included where the new commits change it, never a second release commit; then Phase 1's CI reading and this stop on the new head.

A prior "do the release" never reaches past this stop.

## Phase 3 — Ship, on "proceed" only

The "proceed" authorizes the whole phase as one batch, with no prompt between steps, for the head the last stop showed with its CI reading: never a red, running or unread one. The dispatch is irreversible: the workflow ships as soon as its checks pass. Report each step with its coordinates, and anything left to the maintainer.

1. **Probe a new release workflow.** A workflow with no successful dispatched run (`gh run list --workflow <workflow> --event workflow_dispatch --status success --limit 1` lists none), or one whose file changed since that run (`git log -1 --format=%cI -- .github/workflows/<workflow>` later than the run's `createdAt`, from the same `gh run list` with `--json createdAt`), is probed before the real dispatch. Each probe ships nothing that was not reviewed, even if its check is broken:
   - `lifecycle release <the commit before the head> --ref <release branch>`: expect exit 3, refused as moved;
   - `git push origin <head>:refs/heads/probe/<version>`, then `lifecycle release <head> --ref probe/<version>`: expect exit 1, refused as a wrong ref; delete the probe branch on GitHub afterwards.

   Any other outcome stops the phase: report it.
2. **Ship.**
   - Where `release.workflow` is null: run the checklist's own ship steps.
   - Otherwise `lifecycle release <head> --ref <release branch>`, with the head the last stop showed. It dispatches the workflow and watches the run to its end, as long as the build and the deploy take: run it where a long command may run, in the background where you can.
   - On a workflow step 1 probed, once it has printed `release: dispatched … run <id>` and while that run goes: `gh workflow run <workflow> --ref <release branch> -f commit=<the commit before the head>`. This run cannot ship: expect it to wait while the real one goes, then to be refused as moved. Read it (`gh run list --workflow <workflow> --limit 2`, then `gh run view <id>`) and report it. One that did not wait, the workflow's `concurrency` being wrong, or that was not refused as moved, holds steps 3 and 4 for the maintainer.
   - `lifecycle release`'s last line says how it ended, and its exit code matches:
     - 0, `shipped`: shipped and tagged;
     - 3, `refused: <branch> moved since the review`: Phase 2's *The branch moved*;
     - 1: refused or failed at the step the line names, or nothing was dispatched (a line starting `lifecycle:`, GitHub's refusal among them): report it with the run's link; a run that failed after its deploy started may have shipped in part, and the rollback is the maintainer's call;
     - 4, `in flight`, or no last line at all (the shell cut the command off): the run may still ship and tag; report the run, and dispatch nothing again until it has ended;
     - 2: a usage error from the command line, not a release outcome; fix the command.

   Anything but `shipped` ends the phase here: steps 3 and 4 run only after it.
3. **A hotfix branch lands.** Merge it into the integration branch with a merge commit (`git merge --no-ff`), never squashed, so the tag stays in the integration branch's history:
   - a conflict only in `CHANGELOG.md`: keep both sections, the integration branch's unreleased one above;
   - any other conflict: stop for the maintainer.

   Push it, then `lifecycle ci <the merge commit> --ref <integration branch>`, its last line in the report: nothing stops on it, as the release has shipped, and a red one is the maintainer's next task. Then delete the hotfix branch, remote and local. The merge carries the fix's `Closes #N` to the default branch; where the settings name a board, `lifecycle board <N> Done`.
4. **The checklist's other ship steps:** its milestone steps on the integration branch only, the deploy's verification, and whatever else it lists.
