---
name: upgrade
description: Bring a repository up to the installed lifecycle kit as its own small task — guides pinned to the kit's release, template changes ported into the repository's own files
---

Run when `lifecycle doctor` says the repository is behind the installed kit, before the task that found it: a review round waits for it. It is an untracked process task with its own commit, landed apart from any feature — unless it carries a task's guide edits (step 2). `lifecycle` is the kit's command: on PATH with the kit's Claude plugin, otherwise `bin/lifecycle` in a checkout of the kit.

1. `lifecycle doctor`.
2. `lifecycle upgrade`. It copies the kit's method into the guides folder, pins `.lifecycle.lock` to the installed release, and names the templates that changed. A guide edit not yet in the kit belongs to an open task: the upgrade carries it onto the new release by a three-way merge and names it, and a conflict stops the upgrade with nothing written — resolve it with the maintainer. A carried edit still goes to the kit at its task's *Complete*, and its guide cannot be committed apart from it, so the upgrade then rides that task: its review round reads the upgrade with the rest, and its *Complete* commits both.
3. **The templates.** For each template it names, read what the method changed in the repository's skeleton since the last upgrade: `git diff -- <the template>`, or the whole file for a template the upgrade added (`??` in `git status --short`). Port what applies into the repository's own file — `agents_template.md` into `AGENTS.md`, `contributing_template.md` into `CONTRIBUTING.md`, the issue and PR templates into `.github/` — in the repository's words, keeping what it decided for itself. Port nothing that does not apply, and say so.
4. `lifecycle doctor` reads clean, apart from the carried edits it names.
5. **Hand back.** When step 3 ported nothing, only the guides and the lock changed: hand back by the handback skill with the round skipped. When it ported anything, those are decisions in text every agent reads: run the review skill untracked, with the model-facing lens where `AGENTS.md` changed. *Complete* commits it as `docs(guides): upgrade to kit <release>`.
