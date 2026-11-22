# Ideas home

Every idea still being weighed lives here, run through the lifecycle kit's idea
gauntlet, `idea_gauntlet.md` in the kit's `method/` (in the folder `lifecycle where`
prints), and `graduated.md` follows every project that left. The kit's guides are not
copied here: a gap found in one is filed with `lifecycle gap`.

## Layout

- `active/<idea>/`: every idea still in the gauntlet, parked ones included.
  `IDEA.md` is its state; its evidence sits beside it.
- `archive/<YYYY-MM-DD>-<idea>/`: killed ideas, moved here whole.
- `archived.md`: one line per killed idea. `graduated.md`: one per graduated idea,
  with its status and next check.

## Rules

- The answers in an idea's `IDEA.md`, its bar, every verdict and every check are
  the user's: never fill them or make the call. Do the legwork on request, inside
  that idea's folder.
- Facts about an idea go into its own files, not agent memory: memory is usually
  kept per repo, so here it's shared by every idea and stays behind at graduation.
- Commit the ideas' files at the end of each working session and push, so every
  idea stays backed up. An upgrade's changes are not among them: they land by the
  upgrade's own hand-back and the user's go-ahead.

## Checks

At the start of a session, run `lifecycle doctor --json` (the lifecycle kit's
command: on the agent's PATH where the kit's plugin is on, otherwise `bin/lifecycle`
in a checkout of the kit). A finding whose fix is `upgrade`: run the kit's upgrade
skill first, as its own commit. A `block` whose fix is `adopt` or `update-kit`, or a
failure of the command: tell the user what it printed.

Then list the `graduated.md` rows whose next check has passed. For each, show the
bet from its project's `docs/product/vision.md` where that can be read, and its
sessions: the days with commits in its repo since the last check and since
graduation, for the user to correct. Then ask the user to call each one: continue,
re-scope, park, done or dead. Write the call into the row as the guide's *The logs*
says.

## Capture

Check `archived.md` first: if this idea or a close variant was killed, show the
line; re-opening needs new facts against the logged reason. Then create
`active/<idea>/IDEA.md` from the template in `idea_gauntlet.md`, with the name, the Captured
date and `Status: captured`. The folder takes the idea's working name.

## Kill

`git mv active/<idea> archive/<YYYY-MM-DD>-<idea>`, set `Status: KILLED (see
archived.md)`, add the line to `archived.md` in the user's words, commit.

## Graduate

1. Create the project's repo under its real name and give it the folder with its
   history: `git subtree split --prefix=active/<idea> -b graduate-<idea>`, then
   `git push <new repo> graduate-<idea>:main` and `git branch -D graduate-<idea>`.
2. Here: `git rm -r active/<idea>`, add a line to `graduated.md` with a next check
   four weeks out, commit.
3. In the new repo: put it on the kit (the kit's `docs/guide.md`, *Put a repository
   on the kit*) and run the kickstart (gauntlet Phase 4). Last, set `IDEA.md`'s
   `Status: GRADUATED` with the repo link and move it to `docs/product/idea.md`,
   frozen from there.

## Re-open

Copy the archived folder back into `active/` (the archive stays as it was) and
cite its `archived.md` line in `IDEA.md`, with the new facts.
