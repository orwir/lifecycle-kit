---
name: upgrade
description: Bring a repository up to the installed lifecycle kit — guides pinned to the kit's release, templates installed or ported into the repository's own files; a task's first step when the kit moved, or run alone after a pause
---

The clarify skill runs these steps as a tracked task's first step when `lifecycle doctor` names `upgrade`, and the review skill when a minor release blocks a work round. Run them alone after a pause, or before an untracked task's first edit. `lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit.

1. `lifecycle doctor`. It lists what the kit changed since this repository's release.
2. `lifecycle upgrade`. It copies the kit's method into the guides folder and pins `.lifecycle.lock` to the installed release. It replaces each template the repository had installed word for word (the issue and PR templates) with the new text, and names the templates left to port. A guide edit not yet in the kit is carried onto the new release by a three-way merge, and a conflict stops the upgrade with nothing written: resolve it with the maintainer. A carried edit still goes to the kit at its task's *Complete*.
3. **The templates left to port.** For each one, read what the method changed: `git diff -- <the template>`, or the whole file for a template the upgrade added (`??` in `git status --short`). Port what applies into the repository's own file — `agents_template.md` into `AGENTS.md`, `contributing_template.md` into `CONTRIBUTING.md`, an adapted issue or PR template into its copy under `.github/` — in the repository's words, keeping what it decided for itself. Port nothing that does not apply, and say what was left and why.
4. **What the release requires.** `lifecycle upgraded` lists the kit's `Repositories:` lines between the two releases: changes every repository makes beyond its guides and templates (a setting, a hook, a CI step, a settings key). Make each one in this repository, in its words, and name the files it touched; one that does not apply here, say so and why. Each line names the file it changes, so a later session finds those files from the line itself.
5. `lifecycle doctor` reads clean, apart from the carried edits it names and a note that a newer kit is out, which stops nothing: name it in the *Upgrade* line.
6. **Hand back.**
   - Inside a task, the briefs' *Upgrade* line carries it (`lifecycle upgraded` reads it from the tree in any later session), and the complete skill's commit rule lands it.
   - Run alone, render the hand-back brief by the handback skill. With nothing ported and no required change made, the round is skipped. Otherwise run the review skill untracked: the base reviewer reads each port against its template's diff, and each required change against its `Repositories:` line. *Complete* commits it as `docs(guides): upgrade to kit <release>`.
