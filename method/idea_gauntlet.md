# Idea Gauntlet

From "I have an idea" to a committed project, a parked one, or an archived one with
a one-line reason. The gauntlet makes that call on evidence, as early as the
evidence allows: an evening on whether the idea is worth its cost, an evening
shaping it, then the verdict. A project that graduates carries kill criteria into
its repo, because projects die after they start, often of lost time or interest,
rather than at the idea. Research is cheap now (an agent does most of the
legwork), but paper buys little confidence: keep the gauntlet short and let a
small v0.1 in use settle the rest.

Companion to `project_kickstart.md`: the gauntlet ends exactly where the kickstart
begins. Every idea lives in your ideas home (see *The ideas home*), one folder per
idea, versioned from its first line and backed up once you say yes; *The ideas home* says how an agent
sets one up, and its `AGENTS.md` how to capture an idea into it. Each phase
leaves its evidence where the kickstart will read it (see *Artifacts*), so
graduation moves the folder out into its own repo as it is: `IDEA.md` freezes as
the origins artifact and the rest become the project's first docs. A killed idea
moves to the archive, whole.

Works for software, hardware, and mixed builds — a bot, a smart-home sensor, an
automatic plant waterer, a pinball machine. Items tagged `[sw]` / `[hw]` apply only
to that kind; untagged items always apply. Mixed projects take both.

A game, from a single-screen arcade game to a story-rich adventure, is built from
one of those kinds and takes its items, and its `[game]` lines too. An idea is a
game when what it offers is play, not a fix to a problem: a pinball machine is a
game, a habit tracker with points is software. A game sells an experience, so a
`[game]` line adds what a game is judged on to the item above it; one that says
*instead* replaces that item's untagged and `[sw]` words, or only those it names,
and leaves its `[hw]` words to a game built of hardware.

## The rules

1. **One folder per idea, in your ideas home; `IDEA.md` is the state.** The `Status`
   line says where you are, the checkboxes say what is done, the gates say what was
   decided. `IDEA.md` holds answers, verdicts and links; the research and the
   definitions live in the artifacts beside it.
2. **Decide as early as the evidence allows.** Any gate can be the verdict. Before a
   phase's research or shaping starts, name the question it must answer that could
   still flip the verdict; if there is none, skip that work and decide. Inside a
   phase, run the likeliest killer first. An idea still unclear after two evenings
   is the finding: cut it down or kill it. A kill before the build is a success: it
   cost evenings, not months.
3. **Kill on numbers, never on mood.** From Phase 1 on, every kill names its reason
   with its numbers; before that, a captured idea you stopped caring about can
   simply go. Four reasons end an idea before the build:
   - **solved by X:** an existing option already does the job;
   - **adapt X:** making the best option do the job (learning it, configuring it, a
     small script on top) costs less than building, found by using it rather than
     reading about it;
   - **blocked by Y:** research finds a hard blocker;
   - **not worth it:** the cost, up front and per month, outweighs the gain; an idea
     still unclear after two evenings is one.

   A spike adds a fifth: **disproved:** the riskiest assumption failed.

   [game] For a game, a crowded genre is a market, not a kill. **Solved by X** is a
   near-twin: a comparable game that already gives the same fantasy and hook, at
   or under the price; kill, or go back to Phase 0 for a hook the twin lacks.
   **Adapt X:** a mod, a level in an existing game's editor, or a paper or jam
   version scratches the itch. **Blocked by Y:** the rights to someone else's
   world, or no way to be paid where you live. **Not worth it:** the content
   inventory outgrows the appetite, or, for a game sold, comparable games'
   estimated sales don't cover the spend. **Disproved:** it isn't fun, or its
   story doesn't hold a player.
4. **Size the bet at capture, in sessions.** The appetite is the effort you're
   willing to spend on v0.1, counted in sessions: one sitting of focused work,
   about an evening. Free time comes in bursts, so budgets count sessions, never
   calendar time; the calendar only says when to check (rule 7). The appetite sets
   how deep the gauntlet goes
   ([Shape Up](https://basecamp.com/shapeup/1.2-chapter-03): an appetite starts
   with a number and ends with a design):

   | Appetite | What it is                                          | The gauntlet                                                        |
   | -------- | --------------------------------------------------- | ------------------------------------------------------------------- |
   | Toy      | Up to 3 sessions; nobody depends on it              | Phase 1, then the definitions and the verdict; no shaping, no spike |
   | Project  | Up to 15 sessions to v0.1                           | Every phase                                                         |
   | Product  | A project's, plus upkeep a month; others rely on it | Every phase, plus a real user's reaction before the verdict         |

   [game] A game's v0.1 is a playable vertical slice: one level, run or chapter at
   the quality of the finished game, far short of a release. A toy game is
   jam-sized. A game released to strangers, sold or free, is a product whatever
   its size: players expect patches, and a store page and its marketing cost a
   small game what they cost a big one. Its appetite line says whether it is sold.

5. **Set the bar before shaping, then structure before surface.** Before anything is
   shaped, write the bar in two halves: the value the shape must show against the
   best existing option, and the cost ceiling it must stay under. Then shape from
   the journeys Phase 1 wrote: the IA first, and a picture only where a walk of the
   journeys through the IA can't settle the bar. The verdict judges the result
   against the bar, not the feeling, and waits at least one night. [game] Only
   play settles fun: a game's value half is a playtest result, judged at the
   spike, and Phase 2's verdict judges the cost half and the hook. A toy game runs
   no spike: its play is judged by its v0.1, played by people other than you.
6. **A killed idea gets a log line, not a funeral.** Its folder moves to `archive/`,
   whole, with one line in `archived.md`. Re-opening requires new facts that beat
   the logged reason — renewed enthusiasm doesn't count.
7. **Graduation is a bet with terms.** The project carries its kill criteria into
   its repo: if-then lines, each a state and a budget of sessions. Annie Duke's
   *Quit* (2022) pairs each state with a date; free time comes in bursts, so here
   the pair is a budget, with a date only where the world sets one. The first is
   v0.1's budget, the circuit breaker: v0.1 not in use when it runs out re-runs the
   verdict instead of extending by default. A check comes every four weeks, and
   sooner when a budget runs out: it counts the sessions spent and ends in a call
   (continue, re-scope, park, done or dead; *The logs* says what each one writes),
   so no project drifts into dormancy unnoticed. A done project, its bet met and in
   use, is checked every twelve weeks for its use and its upkeep.
8. **WIP limit.** One idea in exploration at a time, carried to a verdict before the
   next is picked up. At most two running projects (`active` in `graduated.md`; a
   done project isn't one), counting an idea past its make verdict, toys included.
   A make verdict, or a parked or done project picked back up, over the limit
   names the project it parks. Raise either limit deliberately, never by accident.
   Captured and parked ideas are unlimited. A new project's real price is the time
   it steals from the projects you already run.
9. **No product code, no purchases before Phase 3.** Sketches, mock-ups and
   throwaway canvases are fine: they answer the cheap questions instead of skipping
   them. [hw] No parts orders before the Phase 3 spike defines the minimal shopping
   list.
10. **You decide; an agent can do the legwork.** Research, notes, draft CUJs, the
    IA, the walk sheets and the picture can be delegated, and so can the
    pre-mortem: a reader with no stake, who reads `IDEA.md` cold and argues for the
    kill, sees what you won't. The answers in `IDEA.md`, the bar, every verdict and
    every check are yours.

## The ideas home

One private repo holds every idea from capture to verdict, and the record of every
project that graduated from it; the host and the name are yours to pick. Each idea
is versioned from its first line, and backed up from the moment you say yes to a copy
online; its folder never has to carry the final project name.

```
ideas/
├── AGENTS.md        where everything is, and how to capture, kill, graduate and check
├── archived.md      one line per killed idea -> its folder in archive/
├── graduated.md     one line per graduated idea -> its repo, status and next check
├── .lifecycle.toml  the kit's settings: integration branch `main`,
│                    and `ideas_home_template.md` as the template AGENTS.md follows
├── .lifecycle.lock  the kit release the home last upgraded to, with its template's text
├── active/          every idea still in the gauntlet, parked ones included
│   └── <idea>/
└── archive/         killed ideas, moved here whole
    └── <YYYY-MM-DD>-<idea>/
```

Where the home's agent has a plugin system, the home turns the kit's plugin on as a
project does (the kit's `docs/guide.md`). Its `.lifecycle.toml` names its one template under
`[templates]`, `"ideas_home_template.md" = "AGENTS.md"`, and none of a project's. The
method itself, this guide included, is served from the installed kit, so an upgrade
asks the home for nothing but a change to that template.

- **Capture:** a new folder in `active/`, with `IDEA.md` from the template below.
- **Park:** it stays in `active/`; its `IDEA.md` says until when.
- **Kill:** the folder moves to `archive/`, prefixed with the date, and gets a line
  in `archived.md`.
- **Graduate:** the folder moves out into its own repo under the project's real
  name (`git subtree split` brings its history along), and gets a line in
  `graduated.md` with its first check, four weeks out.
- **Check:** when a graduated project's next check comes due, count its sessions,
  read them against the bet in its `docs/product/vision.md`, and call it:
  continue, re-scope, park, done or dead. Its `graduated.md` row records the call
  (see *The logs*).

The root `AGENTS.md` carries these steps for any agent opened in an idea's folder. A new
home starts from `ideas_home_template.md`, beside this guide in the kit, adjusted to taste.

**Setting a home up** (agent instructions). The kit's capture skill finds a home, or sets
one up, before it asks for an idea. Asked to run the gauntlet with no home in reach, find
it the same way: `lifecycle home --check` names the home the folder is in, or `ideas` in
the user folder, and the user's global agent instructions may name another. Where there
is none, offer one where the user chooses, the check naming why a folder cannot be one:
`lifecycle home <folder>` makes it, with the layout, settings and lock above, in one
commit. It stays on the machine until `lifecycle home <folder> --github <name>` backs it
up to a new private GitHub repository, on the user's go-ahead.

## Artifacts

What each phase leaves behind, inside the idea's folder. Every file sits where the
kickstart expects it, so graduation moves the folder as it is and copies nothing.
Every claim carries its source and date: research goes stale, and later work needs
to know how stale.

- **`IDEA.md`** (Phase 0) — the state: status, appetite, the answers, the bar, every
  verdict, links to the rest. It stays short: research and definitions go to the
  files below. Freezes as `docs/product/idea.md` at graduation.
- **`docs/product/competitors.md`** (Phase 1) — each existing option: what it does
  well, the specific reason it doesn't fit, what's worth borrowing; the baseline
  walk of the best one through each CUJ, and its adapt price. Phase 2 adds the side
  by side. Stays living: later UX reviews compare against it.
- **`docs/product/feasibility.md`** (Phase 1) — the assumptions by risk type, the
  riskiest marked; the cost in sessions and money; what research settled (data,
  APIs, platform limits, licences; [hw] parts, power, tolerances); open questions.
  Phase 3 adds the spike's plan, result and stack choice. After graduation it's
  the research record: the stack choice becomes the first ADRs, and the facts the
  code relies on move into `docs/architecture/` as it gets written.
- **`docs/product/vision.md`** (Phase 1) — the problem, who has it, and the CUJs;
  Phase 2 adds the done statement, IN/OUT and the IA; Phase 4 adds the bet. From
  graduation on it's the living intent doc: the IA review rewrites its IA section
  (`ia_review.md` § Phase 8), the UX review builds on its CUJs, and each check reads
  its bet.
- **`design/`** (Phase 2, optional) — only what the IA walk couldn't settle:
  low-fidelity flows on a design canvas, a CLI or bot transcript, [hw] sketches or
  photos of a cardboard mock-up. The first design rounds start from it, or from the
  IA where there is none (`design_workflow.md`).
- **`spike/`** (Phase 3) — throwaway code. Delete it any time: what it proved is in
  `feasibility.md`.

[hw] `docs/hardware/` joins at Phase 4.

[game] A game's evidence goes in the same files: `competitors.md` holds the
comparable games and, for a game sold, their estimated sales, `vision.md` the
fantasy, the players and the player journeys, `feasibility.md` the content
inventory.

## Template

Copy everything below into `active/<idea>/IDEA.md` in your ideas home and fill as
you go (the ideas home's `AGENTS.md` has an agent do this step for you).

```
# Idea: {{name}}

- Status: captured | phase 1 | phase 2 | phase 3 | PARKED until {{trigger}} | KILLED (see archived.md) | GRADUATED -> {{repo}}
- Type: software | hardware | mixed[, game]
- Appetite: toy | project | product — {{the sessions v0.1 may take}}
- Captured: {{YYYY-MM-DD}}

## Phase 0 — Capture (5 minutes)

- [ ] Type and appetite, in the header. The type: what it's built from, and
      whether it's a game (the guide's intro). The appetite: toy, project or
      product; it sets how deep the gauntlet goes (the guide's rule 4).
      [game] A game released to strangers is a product: say whether it's sold.
- [ ] Problem — what hurts, concretely:
      [game] instead: the fantasy and the hook — what the player does and feels,
      and the one thing no comparable game has:
- [ ] Who has it, and how often ("just me" is a valid answer):
      [game] instead: who plays it, not who it's about — the players of 2–3
      named comparable games, on what, and for how long a sitting:
- [ ] Solution shape, one sentence:
      [game] instead: the pitch, "X meets Y, but Z":

No gate: the idea waits, captured, for a free evening — the wait is the cooldown.
Re-read it when you pick it up. No longer care? Leave it, or kill it.

## Phase 1 — Worth it? (an evening)

Research and the walk go to docs/product/competitors.md and
docs/product/feasibility.md, the CUJs to docs/product/vision.md. Likeliest killers
first.

- [ ] Existing options checked — OSS, paid products, [hw] off-the-shelf devices
      and kits. Best 2–3 candidates and the *specific* reason each doesn't fit:
      [game] instead: 5–10 comparable games, searched by theme and fantasy as
      well as by genre, small free ones included, each with its price and its
      hook; for a game sold, its review count as estimated sales where it shows
      one (reviews × about 30, range 20–55: Video Game Insights on 2021
      releases), and with no count, say so. A game far past the appetite, named
      for the feeling it gives, is a reference, not a comparable. The closest by
      fantasy and hook, and what mine adds:
      1.
      2.
- [ ] CUJs: the 2–4 journeys that matter, each with a success criterion and a
      frequency, in vision.md after the problem and who has it (format:
      ux_review.md § CUJs).
      [game] The four player journeys: the first minutes, the core loop, one
      session (a run, a level, a chapter), the whole arc. Success is what a
      watcher sees ("starts a second run unasked"); the frequency, how long and
      how often a sitting.
- [ ] The baseline walk: use the best option yourself through each CUJ — steps,
      decisions, time (method: ux_review.md § Phase 1). Then its adapt price:
      what it would take to make it do the job — learning it, configuring it, a
      small script on top:
      [game] instead of using the best option: play the top 2–3 comparable
      games, an hour each — the core loop, the first ten minutes, the moment I'd
      quit. The adapt price: a mod, a level in its editor, a paper or jam version.
- [ ] Feasibility: what research can settle — data and API access, platform
      limits, licences; [hw] parts availability, power, tolerances. What it can't
      settle goes to feasibility.md as open questions.
      [game] Engine and platform fit, a performance target, and the skills the
      content needs (art, audio, music, writing), each gap with an answer: a
      style that hides it, free-licensed assets, or a paid commission.
- [ ] Cost: does a useful v0.1 fit the appetite's sessions? Upkeep per month, in
      sessions and money — updates, data, support, hosting, paid APIs; [hw]
      power, consumables, the space it takes. Up front — [hw] rough BOM + tools
      I'd have to buy + parts lead time. Hardware iterations cost real money and
      shipping weeks: budget 2–3x the first guess.
      [game] A content inventory, counted — levels, characters, sprites, tracks,
      words — where most of a game's cost goes. A product adds the store's fixed
      overhead, whatever the game's size: its fee, the store page, capsule art, a
      trailer.
- [ ] Portfolio: the running projects (graduated.md), and which one loses these
      sessions. "They can co-exist" is not an answer.
- [ ] Motivation: do I want the *result* or the *process*? Both are valid — but a
      process project gets scoped as a toy; a result project must beat the adapt
      price.
- [ ] Outside view: how did my last graduated projects go (graduated.md), and
      what makes this one different? With no record of my own, what failed
      open-source projects cite: lack of time or interest is a third of the
      stated causes (Coelho & Valente, 2017: https://arxiv.org/abs/1707.02327).
- [ ] Pre-mortem, best run by a reader with no stake: it's three months after
      graduation and the project is dead. Why?
- [ ] Assumptions by risk type, in feasibility.md: value (will it beat the adapt
      price in use?), usability, feasibility, viability (will the upkeep get
      paid?). The riskiest assumption:
      [sw] often value or viability; feasibility when data access, an API or a
      model limit is in play
      [hw] usually sensor accuracy, power budget, waterproofing, mechanical
      tolerances, or a skill I don't have yet
      [game] usually value: that it's fun, which only play settles (Phase 3).
      For a game sold, viability: comparable games' estimated sales against the
      store's base rates (e.g. Steam games released January–October 2025:
      median revenue about $249, 66% under $1,000; Gamalytic, via 80.lv, 2025);
      with no review count among them, on the base rates and the hook

EARLY EXIT (rule 3): solved by X, adapt X, blocked by Y, or not worth it -> KILL,
with the numbers. Otherwise:
[game] A near-twin may go back to Phase 0 for a hook it lacks instead (rule 3).

- [ ] The question Phase 2's shaping must answer that could still flip the
      verdict. None, or a toy -> Phase 2 writes the bar's cost half and the
      definitions, skips the IA, the walk and the picture, and goes to the GATE:
      [game] A toy judges its hook by the pitch, and its play by its v0.1; any
      other game still draws the picture's capsule, which its hook is judged by.

## Phase 2 — Shape it (an evening, no product code)

The definitions and the IA go to docs/product/vision.md, the comparison to
competitors.md.

- [ ] The bar, written before anything is shaped, in two halves —
      value: what the shape must show against the baseline walk (e.g. "clearly
      fewer steps than X on CUJ-1 and CUJ-2, and worse on none"):
      cost: the ceiling it must stay under (v0.1 within the appetite's sessions;
      upkeep under N sessions and M money a month):
      [game] instead of the value half: what a playtest must show, a result a
      watcher sees ("three of five start a second run unasked"), judged at the
      spike. Here the hook stands in for it: the capsule holds up beside
      comparable games' capsules.
- [ ] Done statement: "v0.1 is done when ____" — one sentence, observable.
- [ ] IN — the MVP, max 7 bullets; OUT — explicitly not in v0.1 (be generous).
      [game] With the content counted: levels, endings, characters.
- [ ] Constraints: money cap; deadline (only if real); [hw] where it physically
      lives and who else has to tolerate it — the household veto is real.
- [ ] [hw] Safety check: mains voltage, water near electronics, lithium cells,
      springs/solenoids under load? If yes -> prefer certified modules (relay
      boards, valve kits, charging boards) over raw builds, or explicitly accept
      it as a learning project and plan the precautions.
- [ ] The IA, one page, in the shape ia_review.md reads later: per CUJ, the
      reader and the decision they make (§ Phase 3); the objects, each with its
      attributes, actions, relationships and one home (§ Phase 2); the map of
      screens, commands and messages, [hw] controls, displays and alerts
      (§ Phase 5); the vocabulary (§ Phase 6).
      [game] instead: the entities and systems with their states (the objects),
      the menus, HUD and world map (the map), and the vocabulary; a story game
      adds its outline and a branch map.
- [ ] The IA walk: each CUJ through the IA, in text, with its steps and decisions
      counted. Then re-check the cost half: the objects, their states and the map
      are the honest size of v0.1.
      [game] instead of the walk in text: a paper prototype (cards, dice, a
      spreadsheet) for a systems game, a playable text draft for a story one,
      played through each journey.
- [ ] The picture, in design/, only for what the walk can't settle — often an
      interaction that is itself the edge: [sw] low-fidelity flows, or a CLI or
      bot transcript; [hw] a sketch or a cardboard mock-up, photographed.
      [game] instead, for every game but a toy: a target screenshot and a mock
      store capsule, the art direction set beside comparable games' look, so
      the hook shows at a glance.
- [ ] Side by side: the IA walk against the baseline walk, per CUJ, in
      competitors.md.
      [game] The paper prototype against the baseline play, per journey, and the
      capsule beside comparable games'.
- [ ] Product appetite only: a real user's reaction to the IA walk, or without
      one to the CUJs and the done statement — what they do today, and what they
      would stop doing.
      [game] instead: strangers who play comparable games see the pitch and the
      capsule beside those games' and say which they would try.

No user-facing surface -> no IA, no walk and no picture. Without an IA walk, for
whatever reason, judge the value half on the CUJs and the done statement.

GATE (the verdict, after at least one night's sleep): does it clear both halves of
the bar? Would I use it instead of the best option, adapted? Can I state the done
statement and the riskiest assumption from memory?
[game] Here the bar is its cost half and the hook: the value half is the spike's
gate, or a toy's v0.1's. Instead of using it: would players pick it over the
closest comparable game?
- Make -> Phase 3; a toy goes to Phase 4. Over the WIP limit -> name the project
  it parks:
- Park -> Status: PARKED until {{a date or an event}}. No trigger means it's a kill.
- Kill -> the folder moves to archive/, with a falsifiable reason in archived.md.

## Phase 3 — Spike (one to three sessions)

Budget: {{1–3}} sessions. [hw] Parts spend cap: {{amount}}.

- [ ] Prototype *only* what neither research nor the IA walk could settle —
      usually the riskiest assumption. Throwaway by definition, in spike/.
      [sw] a script or notebook, everything hardcoded; an interactive prototype
      when the risk is the interaction
      [hw] dev board + breadboard, cardboard, hand-operated before automated;
      simulate first where possible (Wokwi, Falstad); order the minimal parts,
      never the full BOM
      [game] the main gate: the riskiest part of the experience made playable —
      usually the core loop as a greybox (placeholder shapes), for a story game
      a playable slice of the story — played by 3–5 people other than me while I
      watch, not ask
- [ ] Stack / platform picked while spiking, reasons noted in feasibility.md —
      these become the project's first ADRs.
- [ ] Result, one line (the numbers and surprises go to feasibility.md):
      [game] how many played, and what they did unasked.

GATE: the assumption survived? Yes -> Phase 4. No -> back to Phase 1 with what was
learned, or KILL with reason "disproved: ____".
[game] Survived: the playtest met the bar's value half, or with none written,
they played on, or read on, unasked. Disproved: not fun, or the story doesn't
hold them. Fewer than three played -> PARKED until three players are lined up:
never passed on fewer, or on my own play.

## Phase 4 — Commit (handoff)

- [ ] The bet, in docs/product/vision.md: the appetite, the cost ceiling, and the
      kill criteria as if-then lines, each a state and a budget of sessions (a
      date only where the world sets one). The first is v0.1's, the circuit
      breaker: "if v0.1 isn't in use after {{N}} sessions, I re-scope or kill",
      never a quiet extension.
      [game] In use: played by people other than me. A product adds a second
      budget, sessions to launch, and kill criteria the world measures: "if a
      level costs over N sessions once the slice measures it, I cut levels";
      "under W wishlists on the store page after N production sessions, I ship
      smaller or elsewhere". The store's lead times (its review, a coming-soon
      period, festival dates) are dates the world sets.
- [ ] Move this folder out of the ideas home into the project's own repo, under
      its real name, and put that repo on the kit; add its line
      to graduated.md, with a next check four weeks out.
- [ ] [sw] Run the kit's project_kickstart.md (an agent can drive it), seeded
      from the artifacts: done statement -> v0.1 milestone; IN list -> first
      issues; the stack choice (the spike's, where there was one) and the
      decisions recorded here -> first ADRs.
      [game] It has no game variant yet: take what fits, and file with
      `lifecycle gap` what the project had to work out for itself (the
      engine's setup, large assets, store builds).
- [ ] [hw] A repo anyway (firmware, code, docs), plus docs/hardware/: BOM with
      sources and prices, wiring diagram or labeled photo, build log,
      calibration notes.
- [ ] Set Status: GRADUATED with the repo link, then move this file to
      docs/product/idea.md. Frozen from here — the origins artifact, never
      edited again.

From here the kickstart playbook owns the process, and graduated.md's checks own
the bet.
```

## The logs

`archived.md` and `graduated.md` record the ideas home's two exits.

| Date       | Idea         | Died at | Reason (one line, falsifiable)                             | Folder                           |
| ---------- | ------------ | ------- | ---------------------------------------------------------- | -------------------------------- |
| 2026-06-01 | auto-waterer | Phase 1 | solved by a $25 drip timer; the gap isn't worth 6 sessions | archive/2026-06-01-auto-waterer/ |

| Graduated  | Idea   | Repo                  | Status | Next check |
| ---------- | ------ | --------------------- | ------ | ---------- |
| 2026-07-15 | plantr | github.com/you/plantr | active | 2026-08-12 |

- The reason must be falsifiable: not "too expensive" but "BOM ~€140 vs €25
  off-the-shelf".
- Re-opening an archived idea requires new facts against the logged reason (price
  dropped, a new library shipped, a skill acquired). Copy its folder back into
  `active/` (the archive stays as it was) and reference the old line in `IDEA.md`.
- A graduated idea's line is all that stays in the home; its repo owns everything
  else, including the frozen `IDEA.md` and the bet in its `vision.md`.

Graduating doesn't mean a project lives. A check comes due every four weeks, and
sooner when a budget in the bet runs out. It counts the project's sessions since
the last check and since graduation (days with commits in its repo, corrected for
work that left none), reads them against the bet, and writes its call into the
row. The line stays whatever the call: the record of what lived and what didn't
is the outside view for the next idea. A running project is one whose Status is
`active`.

| Call     | Status                    | Next check                                   |
| -------- | ------------------------- | -------------------------------------------- |
| continue | active                    | four weeks out                               |
| re-scope | active, the bet rewritten | four weeks out                               |
| park     | parked until {{trigger}}  | the trigger's date, or four weeks out to ask |
| done     | done, in use              | twelve weeks out                             |
| dead     | dead, called {{date}}     | none                                         |

A running project with no sessions since the last check can't continue: the call
is park, with a trigger, or dead. A park needs a trigger, as an idea's does: no
trigger means dead. Done means the bet is met and the project is in use, with
only upkeep left. Its check asks whether it is still in use and whether the
upkeep stayed within the bet's cost ceiling: it stays done, re-opens as a new bet
(re-scope, back to `active`), or is dead once nobody uses it. A next check is
always a date, so every row still in play comes due.

## When to update this file

Same rule as the rest of the set: if two ideas in a row needed the same hand-edit
to the template, the template is wrong — file it with `lifecycle gap`.
