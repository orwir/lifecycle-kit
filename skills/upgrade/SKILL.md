---
name: upgrade
description: Bring a repository up to what the installed lifecycle kit asks of it — templates installed or ported into its own files, upgrade steps made, the lock written; run alone, with its own round and commit
---

`lifecycle doctor` names `upgrade` when the installed kit asks something of this repository: a template it follows changed, a release since its own carries an upgrade step, or it still holds a copy of the method from before 0.8.0. The method itself is served from the installed kit, so nothing else asks for one. The upgrade runs alone, before a tracked task's plan or an untracked task's first edit, with its own round and commit; one that comes due while a task's edits are in the tree waits until that task lands. `lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit.

1. **`lifecycle doctor`**, its output saved to a file in a scratch folder outside the tree for the round's packet: once the lock is written, doctor reads clean and no longer prints the steps.
   - Its `upgrade` finding lists each step owed (each opened `Upgrade <release>:`, from the kit's `UPGRADING.md`, oldest release first), each changed template with the file it ports into, then what the kit changed, each line opened by its group in the kit's CHANGELOG (`Removed: <entry>` names what is gone).
   - On a first move onto the kit, its `adopt` finding lists every step up to the installed release; a later step can undo an earlier one, so make their net effect.
   - A step that changes something outside the tree (a branch on GitHub, a repository setting) comes first, only on the maintainer's go-ahead and in the order it gives. A declined one stops the upgrade with nothing written; a failed one stops it and names what the step already changed outside the tree.
   - A step that changes `.lifecycle.toml` comes next, since the upgrade reads those settings: `[templates]` decides which templates the repository follows.
2. **A first move** has no `.lifecycle.lock`. `lifecycle upgrade --adopt --dry-run` names each file in the guides folder named like one in the kit's `method/` (in the folder `lifecycle where` prints): it would delete each whose text is the kit's, and keep the rest.
   - Compare each kept one with the kit's, and show the maintainer every difference.
   - An older copy of the kit's goes after step 3 and before step 5, by `git rm`, once what only it holds is filed with `lifecycle gap` or in a guide of the repository's own, as the maintainer says: 0.8.0's link step counts it among the kit's files.
   - A guide of the repository's own, such as its own `README.md` index, stays.
3. **`lifecycle upgrade`**, with `--adopt` on a first move, runs once; what it prints is saved beside step 1's output, since a second run finds nothing to change.
   - It deletes a copy of the method from before 0.8.0, or, on a first move, each file the dry run named to delete.
   - A copied file holding an edit the kit never took stops it with nothing written: the edit is filed with `lifecycle gap` or goes into a guide of the repository's own, as the maintainer says; the kit's text goes back into the copy, or the copy is deleted; then it runs again.
   - It replaces each file a template ports into that still holds the template's old text word for word, and names each other changed template with its diff, or read whole for a template new to the repository.
   - It writes `.lifecycle.lock`: the release, and each followed template's text at it.
   - A session that picks up an upgrade cut off after this step finds the old templates in the `templates` of `git show HEAD:.lifecycle.lock`, or, for a lock from before 0.8.0, in the copies under HEAD's guides folder (`git show HEAD:docs/guides/<template>`); a first move reads every template whole. The steps are in the kit's `UPGRADING.md`, for the releases after the old lock's.
4. **The templates left to port.** For each one, its diff says what the template changed. Port what applies into the file it names, in the repository's words, keeping what the repository decided for itself; a template read whole is ported whole, adapted the same way. Port nothing that does not apply, and say what was left and why.
5. **The steps owed.** Make each step from step 1 not yet made, in this repository's words, and name the files it touched; for one that does not apply here, say so and why.
   - **Records stay as written,** whatever files a step lists, a step's own exception holding beside them: an ADR once accepted, a released section of `CHANGELOG.md`, and every frozen record — each review document in `docs/reviews/`, `docs/product/idea.md`, and any other record the repository's `AGENTS.md` calls frozen. Their old paths and names are history, true of the day each was written, so a link the upgrade left dead stays as it is. Name each such record a step would otherwise have rewritten, and what in it: a review still running is its lead's to fix.
6. **The accounting.** Every step and template in step 1's saved output is made, ported or said not to apply; one that is none of these goes back to step 4 or 5.
7. **Hand back.**
   - Nothing ported and no step made: render the hand-back brief by the handback skill, the round skipped.
   - Otherwise run the review skill untracked, its packet's *Read first* naming both saved outputs and step 5 of this skill, in the folder `lifecycle where` prints: the base reviewer reads each port against its template's diff, each step against its text, and checks that the diff changes none of the records step 5 keeps as written.
   - *Complete* commits it as `chore: upgrade to kit <release>`. Then the task that waited goes on in this session: a tracked task's plan round (the clarify skill's § 0), or an untracked task's first edit.
