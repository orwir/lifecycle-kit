# Codebase review template

When the user asks for a comprehensive codebase review (multi-phase walk through every layer to catch drift, dead code, over-engineering, and quiet bugs after a heavy build phase), follow this template. Optimised for: solo-maintained Python repos, work-as-you-go execution, plan kept in `docs/reviews/` as historical record with selective GitHub issues for cross-cutting follow-ups.

## When to use this template

Run this template when accumulated drift is felt but hard to name — typically after a major release, quarterly, or at the close of a heavy build phase. Don't run it for:

- Hot-path bug fixes — too slow; do the fix first, file follow-ups for adjacent drift.
- Sub-week projects — the payback isn't there.
- Active feature work on the same surface — the codebase is moving; reviews need a stable target.
- Pre-launch hardening — that's a security review (Phase 5 alone), not a 12-phase walk.

**Minimum viable review.** When a full pass is too heavy right now, run Phase 0 → Phase 1 → Phase 3 → close-out and skip the rest deliberately: baseline, doc truth-up, the architecture/simplification audit, delta + ledger. That loop catches the highest-value drift; an abandoned full template catches nothing.

If an early phase produces severe findings (architectural rot, security exposure), surface them and pause — escalating those is itself a valid output of the review.

## Stance: Simplicity First

The review's bias is toward removal, not addition. Most of the value comes from finding code, abstractions, and machinery that pulled their weight under an earlier assumption that no longer holds — patterns chosen for the right reason at the time but kept past the moment that reason eroded. Long-lived projects accumulate this residue because each individual erosion (an ADR revision, a follow-up PR, a scope cut) was too small to justify restructuring on its own.

Concrete stance the reviewer holds throughout:

- **For every load-bearing abstraction, the question is "does the surviving justification still demand this shape?"** Not "is the code clean?" Not "is the test coverage high?" If the shape outlives the rationale, the shape is residue regardless of how clean it reads. The [3.W Load-bearing assumption audit](#3w-load-bearing-assumption-audit) is the dedicated check.
- **Default to the smaller code that solves the surviving problem.** A cache that exists because a decorator fired N times per request stops being justified when the underlying check fires once. A ContextVar that propagates data across layers stops being justified when the data can be passed explicitly. Surface the simplification with a decision-shape item; the maintainer chooses the new boundary.
- **Coupled residue lands together.** If removing the cache forces removing the decorator, treat them as one action item, not two — the split is the wrong axis. A half-removal often re-introduces the original perf or correctness problem the residue was masking.
- **Watch for "no abstractions for single-use code."** Generic decorators, protocols, factories that have exactly one caller and one implementation are residue from a planned-but-cancelled second user. Either ship the second user or collapse the abstraction.

**Simplification proposals are a first-class deliverable, not a by-product.** Accumulation is the default direction of drift — every feature adds, almost nothing removes — and the bill lands on performance, maintainability, and everything built on top. The review is the scheduled counterweight: every phase is expected to surface removal and collapse candidates alongside its findings, the close-out aggregates them into a ranked ledger (12.4), and a review whose output is purely additive (more tests, more docs, more checks) almost certainly didn't look hard enough.

This stance is operationalised in the phase sub-checks and the cross-phase habits below; the reviewer doesn't need to remember to apply it ad hoc.

## How this template runs

A 12-phase review is not a single sitting. Run it in passes — each phase is its own context-bounded unit, picked up cold from the plan file when you start it.

1. **Pass 1 — Skeleton.** One session. Fill in the phase table (skip irrelevant phases; customise the domain phases for the project), capture Phase 0 baseline metrics, write the file header. Don't try to write sub-check detail for phases beyond 0 yet — the template's sub-checks and starter lists are enough; project-specific domain-phase detail gets written when those phases are picked up, not now.
2. **Pass 2 — Per-phase analysis.** One session per phase (or per tight cluster). Pick up the plan, re-read it end-to-end, run the phase's sub-checks, produce findings and proposed action items, and surface them to the user. Once the user authorizes, execute the cheap action items in the same session and defer the rest to a follow-up session.
3. **Pass 3 — Execution and revisits.** Action items often span sessions; the lifecycle markers (`Open` / `Done` / `Deferred → #issue`) keep the plan honest across resumptions.
4. **Pass 4 — Close-out.** The final phase (12 in the default layout). Re-run the baseline, populate the delta table, compile the simplification ledger, file issues for the issue-worthy deferred items and leave the rest `[DEFERRED]` for the next review. The plan file stays in `docs/reviews/` permanently — don't delete it (see [Phase 12.5](#closing-out-phase-12)).

**Per-phase context discipline.** When you pick up a phase you should be able to start from: the plan file + the Phase 0 baseline + the project's contract docs. Don't depend on prior-session conversation memory — write findings and decisions into the plan, not into the chat.

**Recovering from a noisy phase.** Subagents sometimes return reports too speculative or too broad to act on. When that happens, restart the phase with tighter scope (specific files, specific question) rather than salvaging a noisy report. The plan stays; only the in-progress findings get redone.

## Working document

Create `docs/reviews/YYYY-MM-codebase-review.md` (or `YYYY-Q#`; e.g. `docs/reviews/2026-06-codebase-review.md`). **Tracked** — the plan is a permanent historical record, not a throwaway. Past review docs are how [Phase 0.2](#02-ground-rules-read) of the *next* review picks up unresolved items.

The plan is a *living* document — the user will return between phases to surface findings, pick options, and authorise commits. Update findings and action items inline as work lands; the [Phase 12.2](#closing-out-phase-12) baseline-vs-final delta table lives inside the plan, not as a separate artifact.

## File header

```
# {project} — Comprehensive Review Plan

Goal: {one line — usually "catch problems early after a heavy build phase, no overengineering"}

**How to use this file**

- Work top-down. Tasks are intentionally small and ordered so later phases assume earlier ones landed.
- Each task starts with a 1–2 line **Why** and a **Scope** bullet list.
- Each task is a *prompt*, not a finished design. When you pick a task up, the first deliverable is a short analysis (findings + suggested changes); only then implement.
- Broken state between tasks is fine. Failing tests are fine. Fix at meaningful checkpoints (end of phase or end of session).
- This file lives in `docs/reviews/` permanently — historical record of what was found and what shipped. Don't delete on close-out.
```

## Default phase structure

The 12 phases below cover most full-stack Python services. Skip irrelevant phases and add domain-specific ones (e.g. ML pipeline review, frontend audit) as needed. Number contiguously.

| Phase | Topic                                               | Why                                                                                                              |
| ----- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 0     | Baseline & ground rules                             | Establish what "done" looks like before changing anything                                                        |
| 1     | Documentation truth-up                              | Fix doc drift first so claims are anchors during code work                                                       |
| 2     | Repository hygiene                                  | Cheap mechanical cleanups (artifacts, tombstones, **comment & docstring drift**) so later phases see real signal |
| 3     | Architecture & layering                             | Validate boundaries hold; produce a concept landscape map; audit pattern duplication and ADR supersession        |
| 4     | Configuration                                       | Env vars / settings / defaults                                                                                   |
| 5     | Security                                            | SQL surface, web endpoints, auth, secrets, deps                                                                  |
| 6     | Database & persistence                              | Schema, repo invariants, retention, migrations                                                                   |
| 7..N  | Domain-specific phases (one per critical subsystem) | One key module at a time — see "Domain phase count" note below                                                   |
| N+1   | Errors & observability                              | Exception hygiene, structured logs, health                                                                       |
| N+2   | Tests & coverage                                    | Coverage gaps, mirror discipline, slow tests                                                                     |
| N+3   | Operations & deployment                             | Docker, CI, backups, release                                                                                     |
| N+4   | Final passes                                        | Self-enforcing rules, doc sweep, close out                                                                       |

**Domain phase count.** The 7..N row expands to as many phases as the project has critical subsystems — typically 2–4. Two slots is fine for a small service. A richer service often needs 3–4 layers along the lines of: a *foundation* layer (external integrations, providers), an *orchestration* layer (pipelines, dispatchers), a *cross-cutting gate* (validation, safety, authz), and a *settlement* layer (anything with strict bookkeeping — billing, accounting, state machines). Translate these labels to your domain: a service with billing might hit all four; a screen-capture utility might have only *capture* and *render*; a CLI tool might collapse to a single *commands* phase. What matters is that each layer with its own correctness logic gets a focused phase. When in doubt, give an orchestration layer or a strict-liability surface its own phase rather than folding it into a neighbour — both have subtle correctness logic that benefits from focused review. Order domain phases by execution flow (foundation → orchestration → gate → settlement) so each phase's findings are concrete by the time the dependent phase is picked up.

**Phase numbers in this template.** The sub-check sections below carry the numbers of the default layout — exactly two domain phases, so security = 5, tests = 10, close-out = 12. If your table has more or fewer domain phases, renumber on use; the topics are canonical, not the numbers.

### Cross-phase working habits

Rules that apply throughout, not in any one phase.

**Subagents.**

- **Spot-check agent claims before relaying.** Subagents over-summarise — they'll confidently say "X is only used in tests" when X is also imported by `composition.py`. One verifying `grep` per load-bearing claim before it goes into the findings table.
- **Delegate large reads, not synthesis.** Send subagents to read a long architecture doc or scan a directory; come back to your own context to write findings.

**Findings discipline.**

- **Don't recommend refactors *because* two files share a prefix or a word.** Architecture-driven layering produces false positives; verify before recommending.
- **Findings get numbered per phase; action items get slugs.** A finding is `P3 #5` (phase + number — number resets each phase). An action item is a kebab-case slug like `` `handler-coverage` `` that is unique across the whole plan, memorable in conversation, greppable, and survives into commit messages and (when relevant) issue titles. Action items cite which findings they address (`Addresses P10 #3, #4`).
- **Severity is a commitment.** Each label changes the default action — pick deliberately, don't default to `Drift` for everything.

**Simplification.**

- **Every phase closes with "what can go?"** Before marking a phase done, write a one-line answer: what did this phase reveal that can be deleted, collapsed, or made cheaper (dead config, single-caller abstractions, per-call work that could be per-process, N+1 queries, redundant test layers)? "Nothing" is a valid answer — but it must be written. Skipping the question is how bloat survives reviews.
- **Prefer the diff that removes.** When a finding admits both an additive fix (wrap, guard, extend) and a subtractive one (delete, inline, collapse), recommend the subtractive shape by default; an additive recommendation needs a stated reason.

**Pace.**

- **First deliverable per task is analysis, not code.** Surface findings + suggested changes; commit only after the user authorises.
- **Broken state between phases is fine.** Failing tests are acceptable mid-phase; fix at phase or session boundaries.

**Project layout.**

- **Substitute `packages apps` with your project's source roots** throughout the grep / find / coverage recipes below. The template uses `packages apps` as a stand-in (a common Python monorepo layout); your project may use `src/`, `lib/`, `internal/`, `cmd/`, or a single nested package. Decide the substitution once at the start of Phase 0 and apply it consistently — the commands won't run as-written on a layout that doesn't have a top-level `packages/`.

### Phase 0 sub-checks — baseline & ground rules

Capture the starting state mechanically and read the project's contract documents end-to-end. Phase 12.2 compares against the metrics captured here, so this is load-bearing — don't skip.

#### 0.1 Baseline scan

Run and record results in the plan. These become the "Baseline" column of the Phase 12.2 delta table.

```
# Lint
ruff check . | tail -5
ruff format --check . | tail -5

# Tests
pytest --collect-only -q | tail -3        # test count
pytest --durations=10                     # wall time + slowest
pytest --cov --cov-report=term | tail -5  # coverage

# Repo size
git ls-files | wc -l
find packages apps -name "*.py" | xargs wc -l | tail -1

# Top-10 largest source files — bloat radar, feeds Phase 3
find packages apps -name "*.py" -printf "%s %p\n" | sort -rn | head -10
```

Capture the numbers, not the full output. Standard table:

| Metric                               | Baseline ({date}) |
| ------------------------------------ | ----------------- |
| Ruff issues                          | 0                 |
| Pytest passed                        | 1369              |
| Coverage                             | 86%               |
| Wall time                            | 40s               |
| Source lines (`packages/` + `apps/`) | 21,514            |
| Direct dependencies (manifest)       | 14                |

Add repo-specific rows (open issues, project-board state, deploy version) when they're useful evidence later.

#### 0.2 Ground-rules read

Read these end-to-end before changing anything:

- `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` — the operating contract.
- `README.md` — what the project claims to do.
- `docs/architecture/` (or equivalent) — load-bearing diagrams and decision records.
- `docs/reviews/` (or equivalent) — past review docs. Skim the most recent one for any unresolved `[ ]` action items and carry them into this review's plan as starting findings.

The output of 0.2 is *internal alignment*, not a written artifact. If a rule surprises you, that's a finding for Phase 1 (docs truth-up).

### Phase 1 sub-checks — documentation truth-up

Fix doc drift first so claims are anchors during the rest of the review. Code can lie quietly; docs lie loudly. Walk the documentation surface and compare each claim against the code.

- **README claims vs `--help`.** Every command, flag, and example in the README should match the actual CLI / API. Run the examples.
- **Env vars: `.env.example` vs source.** Grep the codebase for env reads; every key that influences behavior should be in `.env.example` with a one-line comment.

```
grep -rEn "os\.environ|getenv|os\.getenv" packages apps --include="*.py"
```

- **Version string single-source.** Grep for the version string; it should appear in exactly one place. Every reader (deploy workflow, health endpoint, Docker tags) should read from there, not duplicate.
- **CHANGELOG vs git tags.** Every released tag should have a CHANGELOG section; every CHANGELOG section above the unreleased line should have a tag.
- **ADR status accuracy.** Each ADR's Status (Proposed / Accepted / Superseded / Deprecated) should match reality. A "Proposed" ADR for a decision shipped six months ago is drift.
- **Link rot.** Resolve every cross-link in `docs/`. Broken anchors are silent failures.
- **Module / class docstrings claiming "this calls X" or "used by Y."** Drift candidates — spot-check the high-traffic modules.
- **Frozen records are exempt.** `docs/reviews/*` and `docs/product/idea.md` are point-in-time; don't flag them for drift against current code.

Severity is usually `Drift`. A wrong env-var name in the README, a `--help` example that crashes, or a CHANGELOG that omits a breaking change escalates to `Real bug`.

### Phase 2 sub-checks — comment & docstring hygiene

Most projects have rules like "comments explain *why*, not *what*" and "no PR-history references in code." These rules rot quickly because nobody runs a linter for them. Bundle the audit into Phase 2 alongside artifact and tombstone cleanups:

- **WHAT-comments** — comments that restate what the next line does. Delete; the well-named identifier carries the information.
- **Historical references** — "added for the X flow", "removed in #Y", "used by Z", "fixes issue #123". Belong in PR descriptions and commit messages; in code they rot as the codebase evolves.
- **Stale claims** — comment says one thing, code does another. Either the comment lies and gets deleted, or the code is wrong and needs fixing. Flag both directions.
- **Multi-paragraph docstrings on small functions** — usually copy-pasted boilerplate. One line is almost always enough.
- **Workaround comments without a "Why:"** — `# hack to avoid X` is not enough. Add the bug / constraint that forces the workaround so a future reader can decide whether it still applies.
- **Module docstrings carrying rationale that belongs in an ADR** — long "we chose X because Y" prose at the top of a module should live in a numbered ADR; the module docstring points at it.
- **Oversized comments — the one that hides from every other check.** A "why, not what" rule bounds the *kind* of comment and never its *volume*, so a file accretes one legitimate rationale paragraph per issue that touches it and no individual line ever looks wrong. Measure it: **prose share per file** (comment + docstring lines ÷ non-blank lines) and **the longest run of consecutive comment lines**. Anything past 8 lines in a block, 20 in a file header, or ~35% prose in a non-test source file is a finding. The content is rarely wrong — it is discovery narrative (runs, variants tried, regressions, dates, issue-by-issue history) that should move to the ADR or the issue and be cited in one line.

Grep starting points (Python, adjust for the language):

```
# WHAT-comments — short single-line comments preceding obvious code
grep -rEn "^\s*# [a-z]" packages/ apps/ --include="*.py"

# Historical / authorial references
grep -rEn "added (for|in)|removed in|used by|see issue|fix(es|ed) (#|issue)|introduced (by|in)" packages/ apps/ --include="*.py"

# TODO / FIXME / XXX accumulation — should be near zero, otherwise they belong in issues
grep -rEn "(TODO|FIXME|XXX)\b" packages/ apps/ --include="*.py"

# Oversized blocks — runs of 8+ consecutive comment lines, longest first
awk '/^[[:space:]]*#/ {if(!n)s=FNR; n++; next}
     {if(n>=8) print n"\t"FILENAME":"s; n=0}' $(git ls-files "*.py") | sort -rn
```

**Do not try to detect oversized comments by wording.** Measured on a repo with the problem, keyword greps for history markers ("used to", "was tried", "regressed") matched 7% of the bloated lines and missed 84% entirely — hard-wrapped prose scatters its own tells across fragments, so no per-line pattern sees the paragraph. Length is the only signal that survives wrapping, which is also why the prevention rule is stated as a line budget rather than a style guideline.

Surface findings in the standard table; severity is usually `Cleanup` (delete) or `Drift` (stale claim). Bulk fixes land as one commit per file or per concern, not one per comment. Report prose share as a before/after number — it is the one comment metric that moves visibly.

### Phase 3 sub-checks — concept landscape, assumption residue, pattern duplication, ADR supersession

After a heavy build phase the riskier questions aren't just "do the boundaries hold" but "did newer patterns supersede older ones, leaving the older ones as dead weight?" and "is each load-bearing abstraction still shaped by an assumption that still holds?" Bundle four sub-checks into Phase 3, in this order: the landscape map produced by 3.X is the input for 3.W (load-bearing assumption audit), 3.Y (pattern duplication), and 3.Z (ADR supersession).

#### 3.X Concept landscape map (do this first)

Produce a one-page concept map *before* probing for issues. It makes the rest of Phase 3 — and the later domain-phase audits — much faster, because you know what's load-bearing and what's incidental.

Delegate the architecture doc to a read-only subagent (it's usually large; reading it in main context is wasteful). Ask for:

- Subsystems with a one-line purpose
- Cross-cutting patterns: handlers, registries, factories, decorators, value objects, services
- Layering/boundaries (apps/ vs packages/, transport vs logic) and how they wire together
- Configuration surface (env vars, tier config, feature gating)
- Data flow for the canonical commands end-to-end
- Storage model (tables, UoW, encryption boundaries)
- **Load-bearing abstractions** — the 8–12 names touched by many files (handler protocol, error hierarchy, request context, single-chokepoint dispatcher, etc.)

Output: a short markdown block at the top of Phase 3 with file:line refs throughout. Keep it for the rest of the review.

#### 3.W Load-bearing assumption audit

Most architecture decay isn't a literal duplicate file or a forgotten ADR — it's an implementation pattern that *made sense under assumption A*, the team incrementally changed assumption A through PRs and ADR revisions, and the original implementation shape stayed put because each individual revision was too small to justify restructuring on its own. The residue accumulates as cache machinery, ContextVar plumbing, decorator hooks, or per-call hot paths that no longer pull their weight. It passes tests, it doesn't show up as pattern duplication, and the ADR's Status line still says *Accepted* — only the revisions tell you the original justification eroded.

This is the canonical "Simplicity First" check: for every load-bearing abstraction in the 3.X concept map, ask *what assumption forces this to be shaped the way it is?* Then check whether that assumption still holds.

For each load-bearing name in 3.X:

- **State the original justification in one sentence.** Read the ADR(s), the docstring, and the commit that introduced the pattern. If you cannot state the justification in one sentence, the abstraction itself is unclear — flag and skip the rest of the check on it.
- **Walk the ADR revisions and notable follow-up PRs.** A long Revisions trailer is a strong signal: every revision narrowed, removed, or substituted some part of the original. The justification is the *intersection* of what survived.
- **Compare current shape against current justification.** If the shape is *strictly larger* than what the surviving justification demands — a per-call decorator when the check fires once per request, a request-scoped cache when only one verdict can occur per request, a ContextVar when the data can be passed directly — that excess is residue.
- **Categorize each excess.** Adapt the pattern-duplication verdicts to this lens:
  * *Load-bearing* — the shape really is justified by something the surviving rationale needs. Note it and move on; don't refactor for taste.
  * *Defense-in-depth* — broader than strictly needed but cheap and guarding a real failure mode. Acceptable; document the failure mode in a comment if the docstring doesn't.
  * *Residue from superseded assumption* — the shape outlived its reason. Severity: `Drift` (architectural). Action: surface the simplification with a decision-shape item so the maintainer picks the new boundary; don't unilaterally rewrite a load-bearing abstraction.
  * *Coupled residue* — the residue can't be peeled off without restructuring (e.g. the cache and the decorator are bound together — removing the cache re-introduces the perf problem the cache was fixing). Treat as one action item, not two; the split is the wrong axis.

A standing example (hypothetical — translate the shape to your domain): an authorization decorator was wired around every storage call because the original design wanted to authorize each access independently. Later revisions narrowed the requirement to validating the caller once per request and added a per-request cache to keep the decorator from re-checking across calls. The surviving justification was "authorize the caller once per request", but the implementation was still "decorator at every call + cache". The audit said: decorator + cache are coupled residue; the new shape is "single gate called once at request entry."

Do NOT pattern-match on superficial cues (long file, many imports, deeply nested logic). The signal is the *delta* between what the rationale needs now and what the implementation does. A short, simple file can still be residue; a long, complex one can still be load-bearing.

Findings shape: name the abstraction, quote the original justification, quote the surviving justification, name the excess. One row per abstraction; most rows resolve to *Load-bearing*.

#### 3.Y Pattern duplication audit

Enumerate file-naming smells from the project tree, then probe each in parallel — one read-only subagent per smell. This catches superseded patterns that still linger.

Smell candidates worth probing:

- `<name>.py` next to `multi_<name>.py` or `<name>_v2.py`
- `core/<topic>.py` next to a `<topic>/` package
- Multiple files sharing a prefix (`i18n_*`, `report_*`, `auth_*`) — old+new of one concept, or N distinct surfaces?
- Empty `__init__.py` next to siblings that export real symbols
- Local artifacts (`.mypy_cache/`, `build/`, `dist/`) for tools the project removed but the artifact survived
- Modules mentioned only in older docs / older ADRs

For each smell, the agent's job is: read top-of-file docstrings, count external imports per candidate (`grep` the module path), check tests, look at git log when creation order matters. Ask for a one-line verdict per file from this set:

| Verdict                    | Maps to severity | Action                                                                        |
| -------------------------- | ---------------- | ----------------------------------------------------------------------------- |
| **Live, distinct concern** | Acceptable       | Don't touch; cite the ADR or layering rule that justifies the split           |
| **Stale leftover**         | Cleanup          | Delete; confirm no live importers                                             |
| **Thin shim**              | Cleanup or Minor | Fold if the win is real (small file, single internal user); not urgent        |
| **Transitional**           | Drift            | Old + new both live — decide which way to finish                              |
| **False alarm**            | Acceptable       | Same name, different concern. Note it so the next reviewer doesn't re-flag it |

Most smells in a mature codebase resolve to *Live, distinct concern* — say so explicitly in the findings table so the user knows the pattern is intentionally not refactored.

#### 3.Z ADR supersession spot-check

Any ADR whose Status line says "Supersedes X in `file.py`" is a testable claim. Grep for X. Two silent failure modes that both pass tests:

- **Replacement landed, old path forgotten** — the new code works, the old code is still there, both run. Severity: `Drift`. Action: delete the old path.
- **Old path renamed, logic survived** — the symbol is gone but the equivalent code lives under a new name. Severity: `Drift` or `Real bug` if the survival contradicts the ADR's intent.

Walk every ADR with a Supersedes claim and grep the named symbols. This is the single highest-value sub-check in Phase 3 — drift here is invisible to tests and CI.

#### Phase 3 working habits

In addition to the [cross-phase working habits](#cross-phase-working-habits) above:

- **Don't merge classes whose split encapsulates per-instance state** (counter, lock, cache) just because one is only used by the other. The **file split** may be redundant; the **class split** usually isn't. A "primitive + router" pair where the primitive owns mutable per-instance state is almost always two classes pulling their weight — collapse the file, keep the classes.

### Phase 4 sub-checks — configuration

Config is a bloat magnet: keys outlive the features that read them, and "flexibility" settings spend years pinned to one value. The lens here is shrink-first.

- **Dead keys.** Grep every key in `.env.example` and the settings module against actual reads. Defined-but-unread → delete the key, the doc line, and the plumbing (`Cleanup`).
- **One-position switches.** Feature gates and mode flags that have held a single value since introduction: hardcode the value, delete the branch (`Drift` — the flexibility assumption eroded; cite git log as evidence).
- **Default truth.** The default in code vs `.env.example` vs README — one value stated in three places is two bugs waiting (single-source check).
- **Config-driven indirection with one configuration.** A setting that parameterizes behavior for exactly one caller with exactly one value ever used is the config flavor of a single-use abstraction — collapse it.
- **Validation at the boundary.** Required config should fail fast at startup with the missing key's name; a service that boots half-configured and dies on first use is `Drift-prone`.

### Phase 5 sub-checks — security

The smell here isn't subtle bugs; it's *quiet* exposure — secrets that leak in logs, endpoints that skip auth, deps with known CVEs. Walk the surface in this order; most repos have all five.

#### 5.1 Secrets

- **Pre-commit secret scan over current state, not just diffs.**

```
gitleaks detect --source . --no-banner
```

- **Logging hygiene.** Grep for log calls that include known sensitive fields:

```
grep -rEn "log\.(info|debug|warning|error).*\b(token|secret|key|password|api_key)\b" packages apps
```

Log identifiers (key fingerprint, provider name), not values.

- **`.env.example` cleanliness.** No real values, no copy-pasted production keys.

#### 5.2 Dependencies

- **Known advisories.** Run the project's dep-audit tool (`pip-audit`, `npm audit`, `cargo audit`).
- **Pinning policy.** Are majors pinned on security-sensitive deps (auth, crypto, web frameworks)?
- **Transitive surface.** Spot-check the deepest deps; supply-chain risk lives there.
- **Dependency diet.** Advisories aside: one line per direct dependency — what it does, and whether the stdlib or a smaller library now covers it. A dep with one call site (or none) is supply-chain surface and upgrade churn paid for nothing; collapse or drop. Feeds the 12.4 ledger.

#### 5.3 Auth and authz

- **Every endpoint enumerated.** List all routes / commands / handlers; for each, what's the auth requirement? Per-endpoint `if user.is_admin` is a smell — centralized check is healthier.
- **Privilege boundary tests.** Are there tests that assert a non-admin *cannot* reach an admin path? If not, file a follow-up.

#### 5.4 Data surface

- **SQL injection.** Grep for string-formatted SQL.

```
grep -rEn 'f".*(SELECT|UPDATE|INSERT|DELETE)|format.*(SELECT|UPDATE|INSERT|DELETE)' packages apps
```

Should be zero outside parameterized queries.

- **Web endpoints.** Validate every input at the boundary; trust internal invariants. Spot-check for missing validation on user-controlled fields.
- **Encryption boundaries.** Where does data become plaintext? Where does it stop being plaintext? Every transition is a checkpoint.

#### 5.5 Workflows and CI

- **Least-privilege `permissions:` blocks** on every workflow file. No inheriting repo defaults.
- **Secret usage in CI.** Secrets used only in trusted contexts, never on PRs from forks.

Severity vocabulary: `Real bug` for an actively exploitable issue; `Drift-prone` for "this will become exploitable when X happens"; `Cleanup` for stale config.

### Phase 10 sub-checks — test suite health

A passing suite with adequate coverage is necessary but not sufficient. Tests accumulate redundancy invisibly: framework-behavior tests, layered duplication, mock-heavy fixtures that brittle on every refactor. Phase 10 audits the suite as a system, not as a coverage number. Run sub-checks A→E in order; A frames the rest.

#### 10.A Scale & runtime snapshot

Mechanical counts that frame every later finding.

```
# Test count (collection only — fast)
pytest --collect-only -q | tail -5

# Test functions defined; gap to collected count = parametrize fan-out
grep -rEn "^\s*(async )?def test_" tests/ --include="*.py" | wc -l

# Test:source line ratio
find tests -name "*.py" | xargs wc -l | tail -1
find packages apps -name "*.py" | xargs wc -l | tail -1

# Top-10 largest test files
find tests -name "*.py" -printf "%s %p\n" | sort -rn | head -10

# Wall time + slowest tests
pytest --durations=20
```

Healthy ranges: test:source 0.8–1.5x for logic-heavy code; parametrize fan-out under ~20% of total count; no single test file over ~800 lines without a clear reason.

#### 10.B Coverage reality check (low *and* high)

```
pytest --cov=packages --cov=apps --cov-report=term-missing
```

Both tails matter:

- **Low coverage** is the known smell — usually clusters around transport (HTTP handlers, bot command handlers, CLI entry points). Severity is usually `Drift-prone` or `Real bug`.
- **Suspiciously high coverage** is the inverse smell. A small module at 100% often has tests of framework behavior or trivial getters. Spot-check the last few covered lines for assertion value.
- **Recently refactored modules at low coverage** are regression windows. Cross-reference `git log --since="30 days ago" --name-only` with the coverage report.

#### 10.C Redundancy & bloat signals

The highest line-count payoff of the phase. Each is a separate probe.

- **Layered duplication.** Same code path tested in handler + pipeline + rendering + transport adapter + e2e? The e2e is usually load-bearing; middle layers often re-assert the same thing with different mocks. Per layer, ask: *what does this assert that the layer above/below doesn't?* Verdicts: *Unique responsibility* (keep), *Overlapping with layer X* (trim to the unique cases), *Redundant* (delete).
- **Mock-heavy fixtures.** A `MagicMock`-spawning helper driving N tests becomes brittle on every schema change.

```
grep -rEn "MagicMock\(" tests/ --include="*.py" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

Candidates to replace with typed builders or `SimpleNamespace`.

- **Trivial-assertion tests.** Tests that round-trip a getter, peek at private attributes (`obj._registry`), or assert framework validation. They lock implementation, not behavior.
- **Excessive parametrize fan-out.** A single test with 50 cases on trivial variations. Healthy fan-outs sit under ~20 cases.

```
grep -rEn "@pytest.mark.parametrize" tests/ --include="*.py" -A1
```

- **Snapshot / golden tests with no semantic value.** Tests that lock current output without claiming it's correct. Rename or replace with property-based assertions.

#### 10.D Quality & rule signals

- **Skip / xfail debt.** Each `pytest.mark.skip`, `xfail`, `skipif` is a TODO that pytest hides. Healthy projects have near-zero.

```
grep -rEn "pytest\.mark\.(skip|xfail|skipif)" tests/ --include="*.py"
```

- **Smoke-only tests.** Test functions whose body has no `assert`. Either add a real assertion or delete.
- **Project-rule violations.** Most projects have written or unwritten test rules — audit each one explicitly. Examples:
  * "Don't mock the database in integration tests" → grep `MagicMock` / `mock.patch` inside integration test paths.
  * "No `print()` in tests" → `grep -rEn "print\(" tests/`.
  * "No external network in unit tests" → grep `requests.`, `httpx.`, `aiohttp.` outside fixtures.
- **Slowest tests.** From `pytest --durations=20`. A subprocess-heavy test at 1.5s is fine; a logic test at 0.5s usually has a heavy fixture or a real `sleep`.

#### 10.E Mirror discipline

If the project rule is `tests/` mirrors source 1:1:

```
# Sketch — adapt for the actual layout
comm -23 <(find packages apps -name "*.py" | sed 's|^|tests/|' | sort) \
         <(find tests -name "*.py" | sed 's|test_||' | sort)
```

A naive mirror script over-flags because nested packages can collapse into a single test file (e.g. `packages/db/sqlite/messages.py` covered by `tests/packages/db/test_messages.py`). Pass the script output through a manual false-positive sweep, then surface only the real failure modes:

- **Source file with no test, and no test inheritance from a higher-level file.** Real gap.
- **Test file with no source file.** Stale test (source moved/renamed without updating the test path) or coverage of removed code.

#### Phase 10 working habits

- Don't blanket-prune. Each test removal needs a one-line "what does this assert that another test already covers" justification.
- Trim *layered redundancy* before *trivial assertions* — the line-count payoff is bigger.
- Coverage drops on prune are expected; coverage drops on *new code* are the real signal. Track separately in the Phase 12.2 delta table.
- A passing suite with high coverage doesn't disprove bloat; that's exactly when bloat is hardest to spot.

### Starter sub-checks — phases 6, N+1, N+3

These phases don't get full sections; write their detail at pickup, seeded from the lists below and the 3.X landscape map.

**Phase 6 — database & persistence:**

- Schema vs models drift; unused tables and columns (grep for *writes*, not just reads).
- Migrations replay cleanly on an empty database — the only test of migration health that counts.
- Retention / cleanup jobs actually firing — check row timestamps, not the code.
- Query count per canonical command: N+1s and per-call queries that could be batched or cached are simultaneously a perf finding and a simplification finding.

**Phase N+1 — errors & observability:**

- Bare and over-broad `except` sweeps; swallowed exceptions.
- Exception hierarchy still single-rooted, and every subclass actually raised somewhere — unraised subclasses are dead code.
- Log levels honest (errors that are warnings, info that is debug noise); re-run the 5.1 secrets grep over code added since.
- `/health` truthful: it should fail when the service is unhealthy, not merely report that the process exists.

**Phase N+3 — operations & deployment:**

- Dockerfile against the kickstart essentials: pinned base, deps layer-cached from the lockfile, non-root, `HEALTHCHECK`.
- CI workflows vs local hooks still running identical commands — the local==CI promise rots quietly.
- Backup cron firing *and the restore tested* — a job that runs is not evidence the backup works.
- Compose resource limits still sane against current memory reality.

## Per-phase format

```
## Phase N — Topic

[Optional 1-2 line "Why" if not obvious from the title]

### N.1 Subsection name
- Bullet describing the check / scan / read-end-to-end
- Specific enough that an assistant can pick it up cold
- Cite expected files / commands when known

### N.2 Subsection name
- ...

#### Snapshot (Phase N)
[Optional — current-state inventory: line counts, decision tables, env-var inventories.
Only include when the snapshot is itself useful evidence for findings.]

#### Findings (Phase N)

| # | Finding | Location | Severity |
|---|---|---|---|
| 1 | One-sentence summary. Follow-up sentence with detail if the row needs it. | `path/to/file.py:123` (markdown link) | **Severity** |
| 2 | ... | ... | ... |

#### Action items (Phase N)

- [ ] **`slug-name`** — Short title. Addresses #1. Concrete edits with file paths. Acceptance criteria when non-obvious.
- [ ] **`other-slug`** — Short title. Addresses #2 + #3 (one action collapses multiple findings).
- [ ] **`stale-comment-pass` [DEFERRED]** — Out of scope this review; carry to next.
```

### Severity vocabulary

Use exactly these labels — each carries an expectation:

| Severity             | Meaning                                                                                      | Default action                                                              |
| -------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Real bug**         | Observable defect for users or operators                                                     | Fix this phase                                                              |
| **Drift**            | Code / docs out of sync with reality; not user-visible                                       | Fix this phase if cheap; otherwise file follow-up                           |
| **Drift-prone**      | Pattern that will silently break in a known-future scenario (e.g. when multi-platform lands) | Document the trigger + plan; fix when activated                             |
| **Cleanup**          | Dead code, stale comments, unused exports                                                    | Fix this phase, mechanical                                                  |
| **Minor**            | Inconsistency, style, doc gap, log-level mismatch                                            | Fix only if it's in the immediate diff                                      |
| **Acceptable**       | Confirmed correct or appropriate trade-off                                                   | Leave; note for the record                                                  |
| **Decision pending** | Needs maintainer's call (option A vs B vs C)                                                 | Surface to user with recommended option + rationale; don't act unilaterally |

### Action-item lifecycle

Each action item is a checkbox line keyed by a unique kebab-case slug. The slug is the action item's *name* — it stays the same as the item moves through Open / Done / Deferred and is the way you refer to it in conversation, commit messages, and (when issued) issue titles.

```
# Open
- [ ] **`handler-coverage`** — Improve transport-handler test coverage. Addresses P10 #3, #4.
      Files / changes / tests.

# Done — append a one-liner about what shipped + commit ref
- [x] **`handler-coverage` [DONE]** — Improve transport-handler test coverage. (commit `abc1234`)

# Deferred — issue-worthy (see threshold below). Filed as a tracking issue.
- [x] **`handler-coverage` [DEFERRED → #166]** — Filed with `type/refactor`, `area/api`, `priority/tier-2`.

# Deferred — stays in this doc, picked up at next review
- [ ] **`docstring-spotcheck` [DEFERRED]** — Skim high-traffic module docstrings for "used by X" / "calls Y" claims; not urgent. Carry to next review.
```

**When does an action item become a GitHub issue?** Only when at least one is true:

1. **Real bug** that affects users or operators — needs visibility outside the review.
2. **Deferred work that needs scheduling** — milestone, external blocker, or dependency on another team / release.
3. **Cross-cutting work** that won't fit in one review-driven PR and has its own multi-session lifecycle.

Otherwise the action stays in the doc. Trivial cleanups, single-PR refactors, and small follow-ups are *not* issue-worthy — issuing them inflates the tracker without adding signal. The next review's [Phase 0.2](#02-ground-rules-read) opens by skimming this doc for open `[ ]` items.

**Commit references.** Use the slug in commit message bodies: `closes plan: handler-coverage`. The plan, the git log, and (when it exists) the issue all line up.

### Cross-phase blocks

When one finding blocks another, note it inline rather than relying on the reader to spot it:

> "Until `session-store-fix` lands, finding #2 (retry on stale session) cannot land cleanly — adding retries while the store returns stale rows just moves the bug, doesn't fix it."

The blocker note belongs in the *Action items* section of the blocking phase, not buried in Findings.

### Decision shapes

When an action item has more than one reasonable execution path, present them as letters with a recommendation:

```
- [ ] **`dep-pinning-policy`** — Decide on dependency pinning policy. Addresses #4. Three reasonable shapes:
  - **(A) Pin majors** — `httpx>=0.27,<1.0`. One-time edit, no new tooling.
  - **(B) Lockfile via `pip-compile`** — reproducible, but ongoing bump churn.
  - **(C) Accept current looseness with rationale** — cheapest, footgun.
  - **Recommended: (A).** Catches the actual risk (surprise major bump at next build) without the lockfile maintenance burden.
```

The user picks; you implement. Don't act unilaterally on letter-shaped items.

## Closing out (Phase 12)

```
### 12.1 Self-enforcing rules
- Lock invariants noticed during the review as tests so they don't rot.
  Standard set: layer isolation, cross-transport import bans, single
  version-string source, naming conventions, etc.
- Keep each check tiny — one assertion. If a check would be flaky,
  prefer a doc note.

### 12.2 Final scan re-run
- Re-run Phase 0.1 commands. Compare against baseline in a delta table:

| Metric | Baseline ({date}) | Final ({date}) | Δ |
|---|---|---|---|
| Ruff issues | 0 | 0 | — |
| Pytest passed | 1369 | 1421 | +52 |
| Coverage | 86% | 84% | −2pt |
| Wall time | 40s | 36s | −4s |
| Source lines | 21,514 | 20,818 | −696 |
| Direct dependencies | 14 | 12 | −2 |

Explain the deltas — coverage drops on real new code at <100% are
expected and worth noting, not hiding. For a maturing codebase, negative
source-line and dependency deltas are a success signal, not an anomaly:
the removal bias should be visible right here.

### 12.3 Doc + CHANGELOG sweep
- For every commit landed during the review, confirm the relevant doc
  was updated in the same commit.
- One CHANGELOG line per user-visible change. Pure refactors don't
  touch CHANGELOG.
- Skim every file the review touched for stale comments and
  docstrings — especially comments that referenced "the new X" or
  "as of #Y" before the review and now describe a state that has
  moved on.

### 12.4 Simplification ledger
- Collect every removal / collapse action item from all phases into one
  ranked table: slug, what it removes (lines / dep / abstraction / config
  keys / test layers), status (Done / Deferred).
- Surface the top deferred simplifications as decision shapes — the
  maintainer should leave the review knowing the three biggest
  simplification opportunities, even if none ship now.
- An empty ledger means the review didn't look. If that's truly the state
  of the codebase, write the sentence saying so — don't omit the section.

### 12.5 Close out
- For every `[DEFERRED]` item, decide: does it meet the issue-worthiness
  threshold (see Action-item lifecycle)? If yes, file as a GitHub issue
  with labels + project board, and update the line to `[DEFERRED → #N]`.
  If no, leave it as `[DEFERRED]` for the next review to pick up.
- The plan file stays in the repo as historical record. Don't delete it.
```

## Conventions checklist

When updating the plan during a session, double-check:

- [ ] Findings live in a table; one row per finding; columns are # / Finding / Location / Severity. Numbering resets per phase.
- [ ] Severity uses the seven-label vocabulary, no ad-hoc labels.
- [ ] Action items are markdown checkboxes (`- [ ]` / `- [x]`) keyed by a unique kebab-case slug, not prose paragraphs. Slugs are unique across the whole plan.
- [ ] Done action items have a one-line note about what shipped + commit ref.
- [ ] Deferred items either have a GitHub issue number (`[DEFERRED → #N]`) — only for issue-worthy work — or are flagged `[DEFERRED]` to be picked up at the next review.
- [ ] Cross-phase blocks are noted in the *blocking* phase, not the blocked one.
- [ ] File / line references are markdown links: `[path:line](path#L123)`. Line anchors are fine here, unlike in ADRs — the plan is a point-in-time record; rot doesn't matter.
- [ ] Every phase closed with a written one-line "what can go?" answer — even when the answer is "nothing".
- [ ] Phase 12 includes the simplification ledger, with the top deferred simplifications surfaced as decision shapes.
- [ ] Decision-shape items present options as `(A) / (B) / (C)` with a recommendation; don't act unilaterally on them.
- [ ] Phase 2 covers comment & docstring hygiene against the project's "WHY not WHAT" rule, not just artifacts and tombstones.
- [ ] Phase 3 produces a concept landscape map first (cite it in later phases), then runs the load-bearing assumption audit, pattern duplication, and ADR supersession against it.
- [ ] Phase 3.W (load-bearing assumption audit) ran for every name in the concept map, with the surviving justification and any excess called out per row.
- [ ] Phase 0 baseline metrics captured before any code change; Phase 12.2 compares against them.
- [ ] Subagent claims spot-checked with at least one verifying `grep` before relaying into the findings table.
- [ ] Sub-section numbering is consistent within each artifact (the template uses 3.W/3.X/3.Y/3.Z, 5.1/5.2, 10.A/10.B; pick one per phase, don't mix).
