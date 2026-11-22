# AGENTS.md template

A copy-and-fill skeleton for the operating contract that AI coding assistants (Claude Code, OpenAI Codex CLI, Cursor, Gemini, Copilot, Aider) read on every change. Drop this into the root of a new repo as `AGENTS.md`, replace the `{{placeholder}}` tokens, and delete sections that don't apply to your project type.

Companion to `project_kickstart.md`: the kickstart explains *why* each rule exists; this file is the *rule itself*, compressed to the form the assistant actually reads.

---

## How to use this template

1. **Copy** the section under "Template" (everything inside the fenced block) into a new `AGENTS.md` at your repo root.
2. **Fill placeholders.** Every named `{{TOKEN}}` has a row in the *Placeholder reference* below, with example values. A choice token, `{{a | b}}`, keeps one option; an example token, `{{e.g., …}}`, takes the repository's own value.
3. **Prune by project type.** Some sections include alternative paragraphs marked `[web-service]`, `[desktop]`, `[mobile]`, `[cli]`, `[library]` — keep the one that matches and delete the others. Sections with no marker apply to all project types.
4. **No vendor shims.** `AGENTS.md` is read natively by most tools (Claude Code from v2.1.277, Codex, Cursor, Windsurf, Gemini CLI, Copilot). Don't add a `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md`: any one of them makes Claude Code read `CLAUDE.md` only. Put Claude-only additions in `.claude/rules/`; a one-line `CLAUDE.md` containing `@AGENTS.md` is only for sessions that can't read `AGENTS.md` directly (an older Claude Code). Tool support shifts quarterly, so check the current docs of each assistant you adopt.
5. **Keep it under ~200 lines.** Longer files get skimmed instead of read. Rationale lives in the kickstart and ADRs, setup and release steps in `CONTRIBUTING.md`; keep `AGENTS.md` as the compressed contract.

### What belongs in AGENTS.md (and what doesn't)

| Belongs                                                         | Belongs elsewhere                              |
| --------------------------------------------------------------- | ---------------------------------------------- |
| Rules an assistant must apply on every change                   | Rationale → the kickstart; decisions → ADRs    |
| The smallest viable list of "don'ts"                            | Setup and release steps → `CONTRIBUTING.md`    |
| The repository's labels, changelog cap and documentation map    | Tutorials and walkthroughs → `docs/guides/`    |
| Pointers to the source-of-truth docs                            | Architecture deep-dives → `docs/architecture/` |
| Loop-safe defaults (no `--no-verify`, no destructive shortcuts) |                                                |

If a rule is in `AGENTS.md` only to explain *why*, move it. The contract should be terse enough that violations are obvious.

---

## Template

Everything inside the fenced block below is the template body. Copy it as-is, then fill placeholders.

````
# Agent instructions — {{PROJECT_NAME}}

You are working in the `{{OWNER}}/{{REPO}}` repository: a {{LANGUAGE}} {{PROJECT_TYPE}} ({{ONE_LINE_DESCRIPTION}}). Follow every rule below on every code change. When a rule conflicts with a direct user instruction in the current session, ask the user to clarify before proceeding.

These rules are the compressed operating contract. Why each exists is the lifecycle kit's [project_kickstart.md](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md); setting up and releasing is [CONTRIBUTING.md](CONTRIBUTING.md). Every link to the lifecycle kit, here or in any other file, opens its `main` on GitHub: read the file at the same path in the folder `lifecycle where` prints instead (`method/…`, `docs/guide.md`), the release this machine runs.

**Hard gates, before anything else** (everything below is detail around them):
- Never ship a release without that release's own "proceed".
- Never commit, push, merge or close work without explicit approval (*Task workflow*), except WIP commits on a feature branch.
- Never bypass a hook with `--no-verify`: fix what it caught, or, if the hook is wrong, say so and propose a fix.
- Never commit or print secrets.

---

## Commands

- Setup: `{{SETUP_CMD}}`
- Test: `{{TEST_CMD}}`; given tests alone: `{{TARGETED_TEST_CMD}}`
- Lint + format: `{{LINT_CMD}}`
- Run locally: `{{RUN_CMD}}`
- Lifecycle: `lifecycle doctor --json` before a task. A finding whose fix is `upgrade` runs the lifecycle kit's upgrade skill first, alone, unless a task's edits are in the tree: that task lands first. Any other `block`, or a failure of the command, goes to the user. `.lifecycle.toml` holds this repository's settings for the kit's skills and command.

These are the canonical invocations — the same ones the hooks and CI run. Don't improvise variants.

## Branching and commits

- **Default flow:** {{commit directly to the integration branch | open a feature branch}}, {{since one maintainer's pre-push hooks mirror CI | since contributors review by PR}}.
- **A feature branch** (`feat/…`, `fix/…`, `chore/…`, `docs/…`, `refactor/…`, `perf/…`), whatever the default, for work that is multi-commit and should land atomically, risky or invasive (schema migrations, auth, payments, cross-cutting refactors), spans sessions, or wants a diff review before merging. When in doubt, branch. It lands by the lifecycle kit's `complete` skill: a PR from `.github/pull_request_template.md` for a reader who never saw the review rounds, merged once every check passed, the branch deleted on both ends. A branch listed by `git branch` is either active work or it shouldn't exist.
- **A push ships nothing.** `{{INTEGRATION_BRANCH}}` is the one long-lived branch. A release {{deploys | publishes artifacts}} only as *Versioning and release* says: where `[release]` in `.lifecycle.toml` names a workflow, dispatched on the commit the release review read, which creates the `v*` tag (never one by hand); otherwise by the steps in CONTRIBUTING.md § Releasing. A production fix that cannot wait for what `{{INTEGRATION_BRANCH}}` holds goes on a `hotfix/…` branch cut from the last release's tag ([CONTRIBUTING.md § Hotfixes](CONTRIBUTING.md)).
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/): a prefix of `feat`, `fix`, `refactor`, `docs`, `test`, `chore` or `perf`, an optional scope (`fix(parser): …`, `chore(deps): …`), a subject in the imperative with no trailing period and under 72 characters, and a body, when used, that says **why**: the diff shows what.

## Task workflow — three phases

Every tracked task moves through three phases. **Do not collapse them**: each gate is the user's, not yours to assume. The issue carries the task between sessions: a session that picks it up cold continues from the issue body, its ticked boxes and the tree, so nothing a later session needs may live only in the conversation.

The rounds, their packets and the briefs are the lifecycle kit's [task_review.md](https://github.com/orwir/lifecycle-kit/blob/main/method/task_review.md); its `clarify`, `review` and `handback` skills run them, and its `complete` skill the close-out. Where `.lifecycle.toml` names a board, the card moves by `lifecycle board`: to `In Progress` at *Clarify*, to `Done` at *Complete*.

1. **Clarify.** Read the ticket and the code it touches, ask for any missing detail, and surface scope or constraint conflicts *before* writing code. Write the issue's *Plan* and run the plan round where it applies. Implementation begins only once the plan is accepted: by the maintainer's "go", or by you where [task_review.md](https://github.com/orwir/lifecycle-kit/blob/main/method/task_review.md) § The plan round awaits none. Accepting a plan opens implementation and nothing more.
2. **Implement & stop.** Do the work in full to the *Definition of Done*, ticking each Technical-details box as its path lands and recording a departure under the plan's *Departures* when you make it. Run the local gate in this session, say what could not run, and run the work round. Then **stop and hand back** with the hand-back brief, the changes **uncommitted** outside a feature branch. Corrections, and answers to the brief given without the go-ahead, are worked here, then you stop again. A gap found in one of the kit's guides is filed on the kit (task_review.md § Developer rules).
3. **Complete — on explicit approval only.** An explicit go-ahead ("complete the task", "lgtm", or equivalent) is the *only* trigger to commit the task work, push, close the ticket and delete a merged feature branch. Answers to the brief given with it are made first, within the size the brief stated; a veto, or a bigger change, renders the brief again and waits for a new go-ahead. The same gate holds `git push`, `gh pr create` and `gh pr merge`: auto mode is permission to write code without re-asking, not permission to land it.

What the kit's skills read here:
- **Parts a decision can touch:** {{PARTS}}.
- **Evidence a root cause is confirmed from:** {{EVIDENCE_SOURCES}}.
- **Drawn surfaces:** {{DRAWN}}; when a change to one is drawn and closed is [design_workflow.md](https://github.com/orwir/lifecycle-kit/blob/main/method/design_workflow.md)'s.

### Definition of Done

A task is done when all five hold; a brief that cannot claim one says which, instead of calling the task done.

1. **It serves the ticket's goal at real scale, not only its named mechanism.** If what the ticket names serves the goal badly with real data — the whole list, the longest locale, the smallest screen — raise it at *Clarify* or take it through the design loop ([design_workflow.md](https://github.com/orwir/lifecycle-kit/blob/main/method/design_workflow.md)); never ship it because it was named.
2. **It was used the way its user uses it.** A UI change is looked at running, with real data: at the smallest and the largest supported width, in every shipped locale, by keyboard alone, and without scripts where the surface promises to work without them. A CLI, API or library change is called the way its caller calls it. Not having looked is a task not done, not a *Not run* line.
3. **Every scenario in the plan, and every other new behaviour, has a test that fails without it** (*Tests and quality gates*).
4. **The gate is green and the work round ran**, or the brief says why it was skipped, as an untracked micro-task's does.
5. **The docs are in sync** (*Keep documentation in sync with code*): every doc the change touches, a `CHANGELOG.md` entry for any user-visible change, new env vars, commands, config options, labels or workflows documented where an operator looks, an ADR for a non-obvious decision (a box in the plan) referenced where it surfaces, and a pattern reusable across projects filed on the lifecycle kit.

The bar is the maintainer's. A shortfall in 1 or 2 found after landing is unfinished work, and its fix is never declined on cost or on the demand not being there yet.

## Code layout

- `{{ENTRY_DIR}}` ({{e.g., `apps/`, `cmd/`, `bin/`}}) holds the thin transport / entry points, which know about {{e.g., HTTP, chat-platform APIs, CLI args, OS event loops, native UI frameworks}}.
- `{{LOGIC_DIR}}` ({{e.g., `packages/`, `lib/`, `internal/`, `core/`}}) holds pure logic. **Never import transport libraries ({{e.g., `fastapi`, `express`, `tauri`, `react-native`, `pyqt`, `cobra`}}) from `{{LOGIC_DIR}}`.** Logic must be testable without spinning up the transport.
- `tests/` mirrors the source tree 1:1, with no clever grouping: `{{LOGIC_DIR}}/foo/bar.{{EXT}}` is tested in `tests/{{LOGIC_DIR}}/foo/test_bar.{{EXT}}`.
- `migrations/` (if any) holds numbered schema files: add one, never rewrite an applied one.
- `scripts/` is for one-off tooling. Don't move runtime code here.
- Do not create new top-level directories without a clear reason and user sign-off.

## Versioning and release

- The version string lives in exactly one place: `{{VERSION_FILE}}` ({{e.g., `packages/core/__init__.py` → `__version__`, `package.json` → `"version"`, `Cargo.toml` → `version`, `pubspec.yaml` → `version`}}). Every other consumer ({{e.g., deploy workflow, `/health` endpoint, About dialog, `--version` flag, image tags, installer name}}) reads from it. **Do not duplicate the version string anywhere else.**
- Update `CHANGELOG.md` for any user-visible change: **one claim per entry, at most {{CHANGELOG_CAP}} characters before the `(#N)`**. The rest of the style is [project_kickstart.md § CHANGELOG style](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md).
- **Releases run by the lifecycle kit's `release` skill: prepare, review, ship.** The ship phase starts only on the maintainer's own "proceed" for that release; a prior "do the release" stops at the review. The steps are [CONTRIBUTING.md § Releasing](CONTRIBUTING.md) and § Hotfixes, run as written.

## Tests and quality gates

- Tests run with `{{TEST_RUNNER}}` ({{e.g., `pytest`, `vitest`, `jest`, `go test`, `cargo test`, `xctest`}}). See `{{PKG_MANIFEST}}` for config.
- The coverage floor, `{{COVERAGE_FLOOR}}%`, is enforced at the pre-push stage and in CI: a change that drops below it adds tests, never lowers the floor.
- Integration tests hit real I/O ({{e.g., a real SQLite database, a real filesystem, a real local HTTP listener}}). **Do not mock the {{primary-side-effect target}} in integration tests.** Unit tests of pure functions are fine without it.
- Lint + format: `{{LINT_TOOL}}` only ({{e.g., `ruff`, `eslint` + `prettier`, `gofmt` + `golangci-lint`, `rustfmt` + `clippy`, `swiftlint` + `swift-format`}}). One tool per role, never a competing one.
- Pre-commit hooks run the same commands as CI, so what passes locally passes CI, and coverage and lint fail the *push*, not just CI. **If this project lacks a local hook config covering lint, format, the full test suite, the coverage floor and a secret scan**, set one up before the first commit: [project_kickstart.md § Day-zero guardrails](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md).

## Documentation

- Respect the documentation layers:
  * `README.md` — end-user front page (what, install); `docs/guide.md` — the user guide, once split off; translated twins (`*.<lang>.md`) beside each, changed in the same commit
  * `CONTRIBUTING.md` — setting the repository up, releasing and hotfixing
  * `CHANGELOG.md` — release history
  * `docs/product/` — vision incl. CUJs, the "what" and "why"; competitors and feasibility, the research behind them; `idea.md` is the frozen origins record — never edit it
  * `docs/architecture/` — the "how": components, data flow, config reference
  * `docs/guides/` — the project's own task-oriented howtos (deploy / publish / package, extend). The lifecycle kit's guides (kickstart, task review, the comprehensive reviews) are not copied here
  * `docs/adr/` — architecture decision records, one per significant choice
- **A new documentation file is written only where the accepted plan has a box for it, or, outside a tracked task, where the user asks for it.** An ADR for a non-obvious decision is proposed as a box; a file a mapping row names that the project lacks is surfaced (*Change → required doc mapping*). A file a kit flow writes (a review's report, an upgrade's port) is that flow's.
- **Do not recreate `roadmap.md`** or any equivalent tracking file. Tracked work lives on GitHub: issues, milestones, the project board.
- Cite code as `file.{{EXT}}:123`. Markdown links in docs use **file-relative paths**, which resolve in every renderer: from a doc under `docs/adr/`, `[{{LOGIC_DIR}}/foo.{{EXT}}](../../{{LOGIC_DIR}}/foo.{{EXT}})`, never a workspace-root path, which 404s outside workspace-aware IDE tooling.
- Avoid `#L123` line anchors in long-lived docs (ADRs especially): keep the file ref, drop the line.
- An ADR has four sections, Status / Context / Decision / Consequences, and the next number.

### How a doc is written

The reader is looking for something, and every line before it is a line charged to them.

- **Open with orientation:** what the doc covers, who it is for, and what it leaves out, in two or three sentences before the first `##`.
- **Conclusion first,** the evidence under it.
- **One claim per paragraph,** each under ~700 characters; a how-to step's caveats are sub-bullets under it.
- **Tables scan, prose explains:** a cell that needs a paragraph holds one sentence, and the paragraph goes below the table.
- **One name for one thing:** `{{PROJECT_NAME}}` everywhere, one form for a cross-reference (`ADR-0007`), one word for a concept in every doc.
- **A list lives in one place;** other docs link to it, and quote a few items only with the reason for the pick.

## Keep documentation in sync with code

**Before you commit any change, check whether any existing doc becomes wrong, incomplete or misleading because of it, and update it in the same commit.** A doc that lies is worse than a missing one.

### Change → required doc mapping

| Change                                                             | Must update                                                                                                                          |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| New user command, argument, response format, or UI surface         | the user guide (`README.md`, or `docs/guide.md` once split) and its twins; the front page when its bullets or install steps change  |
| New env var, config option, or changed default                     | `.env.example` (or equivalent config schema) + the user guide and its twins; also `docs/guides/{{deploy_or_publish_guide}}.md` if it affects shipping |
| New component, changed data flow, new integration                  | `docs/architecture/architecture.md`                                                                                                  |
| Non-obvious design decision                                        | new ADR in `docs/adr/`                                                                                                               |
| Any user-visible change                                            | `CHANGELOG.md` entry under Added / Changed / Fixed / Removed                                                                         |
| New capability or extension point                                  | `docs/guides/extension_guide.md`                                                                                                     |
| New/changed UI component or pattern (if the project has a surface) | the design-language reference (e.g. `docs/guides/design_language.md`)                                                                |
| Visible change to what the front page's demo shows                 | the demo, captured again                                                                                                             |
| New or removed user journey, or a major flow change                | `docs/product/vision.md` § CUJs                                                                                                      |
| Process / workflow change                                          | this file, or `CONTRIBUTING.md` for setup and releasing; a pattern reusable across projects is filed on the lifecycle kit        |

If a row points at a doc the project doesn't have yet (extension guide, design reference), surface the gap — creating the file is a maintainer decision, not an automatic step.

## Issues and pull requests

- New issues use the templates in `.github/ISSUE_TEMPLATE/`: `bug.md` for defects and regressions, `task.md` for features, refactors, docs, infra.
- An issue is captured with no plan; its *Plan* is written at *Clarify*, and changes after acceptance only through its *Departures*. Tick a Technical-details box when its path lands; never edit prose to track progress.
- **Labels:** {{LABELS}}. Add the issue to the milestone if scoped.
- **The board,** where `.lifecycle.toml` names one: every write is `lifecycle board <N> <column>`, which puts the card at the top of its column: **Backlog** when you file an issue; the other moves are *Task workflow*'s, and `Backlog → Ready` is the maintainer's triage. The columns, milestones, two-stage issues and the label taxonomy: [project_kickstart.md § GitHub tracking setup](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md).
- PRs use `.github/pull_request_template.md`: a Summary, a linked issue (`Closes #N`), and a concrete Verification section.
- Reference issues in commit bodies and PR descriptions, each confirmed with `gh issue view <N>` first; never invent a number.
- **Dependabot PRs** are normal PRs: read the bump's changelog or release notes before merging. Patch and minor bumps may merge once CI is green; major bumps always get a manual review.

## Secrets and security

- Never commit `.env`, credentials, API keys, signing certificates, provisioning profiles, or any file matching common secret patterns. A `gitleaks` (or equivalent) pre-commit hook should catch most of this — do not disable it.
- Never log or print a secret's value (a decrypted secret, an auth token, payment data), in the conversation, command output or a debug dump, not even to diagnose: log identifiers (`provider`, `user_id`, `key_fingerprint`) and name keys (`API_TOKEN is set/empty`).
- Document the rotation of every long-lived credential in `docs/guides/{{deploy_or_publish_guide}}.md`.
- Every new CI/CD workflow declares a least-privilege `permissions:` block, not the repo's defaults.

[web-service] Run the production container as a non-root user. Reverse-proxy and TLS termination live outside the application image.
[desktop] Code-sign release artifacts; document the signing certificate location and rotation procedure.
[mobile] Provisioning profiles and signing certificates live in {{e.g., Fastlane Match, EAS, App Store Connect}}, never in the repo.
[cli] Tarballs / archives published to package registries are signed or checksummed; document how to verify.
[library] Published packages use the registry's trusted-publisher / OIDC flow when available, not long-lived tokens.

## Executing actions

- Weigh the blast radius. Freely: edit files, run tests locally, create feature branches. Confirm first: `git reset --hard`, force-pushing, deleting a branch with unmerged work, dropping {{database/state-store}} tables, amending published commits, pushing to shared remotes, publishing to a registry, uploading a release artifact. Deleting a just-merged feature branch is routine close-out.
- Approval in one scope does not extend to another (*Task workflow*, *Versioning and release*).
- Investigate unfamiliar files, branches or config before deleting them: they may be the user's in-progress work.
- Diagnose a failing check at its root cause; never bypass it with `--no-verify`, test-skip markers, lint-suppress comments or the like. Ask the user if you're stuck.

## When editing code

- **Simplicity First.** Touching a load-bearing abstraction (decorator, cache, ContextVar / thread-local, registry, factory, protocol, DI container), ask whether the assumption that forced its shape still holds; if not, surface the simplification *before* another patch, and land coupled residue (a cache and the decorator that only makes sense with it) as one change: [codebase_review.md § Stance: Simplicity First](https://github.com/orwir/lifecycle-kit/blob/main/method/codebase_review.md).
- **Stay in scope.** A task's diff holds only what it needs: no drive-by refactors, renames, dependency bumps or reformatting of untouched code; surface those as suggestions.
- **Conform to the design language** where the project ships a user-facing surface: every UI edit (web, desktop, TUI, a CLI's flags and output) reuses the design-language reference's components, data rendering and patterns (e.g. `docs/guides/design_language.md`), never a parallel variant, and a change to a screen with a design file lands inside that file. (A headless service or library drops this rule; see [project_kickstart.md § User-facing surface foundation](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md).)
- **A comment says why, never what,** and only where the why is non-obvious: a hidden constraint, a subtle invariant, a workaround for an external bug.
- **Comments have a length budget: {{COMMENT_BLOCK_BUDGET}} lines for a comment block, {{DOC_COMMENT_BUDGET}} for a doc comment, {{FILE_HEADER_BUDGET}} for a file/module header.** It counts prose, not a parameter or return block (`Args:`, `@param`); past it, cut or move the prose to an ADR, never append. The numbers are derived from this codebase by [codebase_review.md](https://github.com/orwir/lifecycle-kit/blob/main/method/codebase_review.md) § Phase 2, which says why, and re-derived when it changes shape.
- **Write for the next editor:** a comment answers *what breaks if I change this?* Present tense is the test: a sentence in the past ("used to", "was tried", "regressed") is history. Measurements, variants tried, dates and issue narrative go in the PR description or the tracker, never in source.
- **Displaced rationale moves, cited in one line (`See ADR-0012.`):** a design decision to an ADR, domain rationale to the doc the mapping names, measurements to their issue.
- **Prefer making the code say it:** a named constant, an extracted function, a test named in a sentence; unlike prose, it fails when it stops being true.
- **A tracker reference in a comment** (`#123`, `PROJ-456`) only anchors load-bearing rationale (an ADR, an external bug, a non-obvious constraint). Delete it to test: if the comment still answers "why", the reference may stay; if it falls back to a WHAT-comment, inline the rationale. `added in #123` / `fixes #123` tombstones are banned, in test doc comments too, and three or more references are a changelog, which moves out.
- No backwards-compatibility shims, dead-code tombstones or `# removed X` comments: delete cleanly. No feature flags for work that can simply ship. No half-finished implementations: split the PR and say so; don't leave stubs.
- Validate at system boundaries (user input, external APIs, deserialization) and trust internal invariants: no error handling for impossible scenarios.
- Match the existing patterns of the file you edit; a wrong pattern is fixed in a commit of its own, with a clear message.

## What NOT to do

- Do not use emojis in code or docs unless the user explicitly asks.
- Do not add `print()` / `console.log` / `println!` for debugging — use the project's structured logger.
- Do not add dependencies casually. New dependencies need a reason that justifies the supply-chain surface.
- Do not improvise a review process: a comprehensive review follows the kit's guide for it, on [review_machinery.md](https://github.com/orwir/lifecycle-kit/blob/main/method/review_machinery.md), which names them.

## When in doubt

1. Check if an existing file already solves the problem. Reuse before creating.
2. Mid-task fork: internal and easily reversible → decide, record it under the plan's *Departures*, continue. User-visible, hard to undo, or scope-changing → stop and ask.
3. Otherwise ask the user. A 30-second clarification beats a 30-minute undo.
````

---

## Placeholder reference

Quick reference for each `{{token}}` used above.

| Token | Example values | Notes |
|---|---|---|
| `{{PROJECT_NAME}}` | "Acme Reader", "Widget CLI" | Human-readable name |
| `{{OWNER}}/{{REPO}}` | `acme/reader` | GitHub slug |
| `{{SETUP_CMD}}` / `{{TEST_CMD}}` / `{{LINT_CMD}}` / `{{RUN_CMD}}` | `uv sync` / `pytest --cov` / `ruff check . && ruff format .` / `docker compose up` | The canonical invocations CI and hooks run |
| `{{TARGETED_TEST_CMD}}` | `pytest <tests>`, `npx vitest run <tests>`, `go test <packages>` | The new or changed tests alone, as the review skill runs them on a worktree to prove each fails without the change. `.lifecycle.toml`'s `gate.targeted`, read first where it is set, holds the same run with `{root}` and `{tests}`. None: the review skill reports `not covered: no targeted run` |
| `{{LANGUAGE}}` | "Python 3.13", "Rust 2024", "TypeScript / Node 22", "Swift 5.10" | Primary language and version |
| `{{PROJECT_TYPE}}` | "chat bot", "macOS menu-bar app", "iOS app", "CLI tool", "library" | One-noun shape |
| `{{ONE_LINE_DESCRIPTION}}` | "REST API with SQLite storage, Docker deployment" | Sub-30 words |
| `{{INTEGRATION_BRANCH}}` | `main` | The one long-lived branch, where work lands and releases are cut |
| `{{ENTRY_DIR}}` / `{{LOGIC_DIR}}` | `apps/` + `packages/`; `cmd/` + `internal/`; `src/bin/` + `src/lib/` | Transport-vs-logic split |
| `{{EXT}}` | `py`, `ts`, `tsx`, `go`, `rs`, `swift`, `kt` | Primary source extension |
| `{{VERSION_FILE}}` | `packages/core/__init__.py`, `package.json`, `Cargo.toml`, `pubspec.yaml` | Single source of truth |
| `{{TEST_RUNNER}}` | `pytest`, `vitest`, `jest`, `go test`, `cargo test`, `xctest`, `flutter test` | One command, one runner |
| `{{COVERAGE_FLOOR}}` | `55`, `70`, `80` | Pick something you can defend |
| `{{CHANGELOG_CAP}}` | `120` | **Derive, don't copy** — `project_kickstart.md` § CHANGELOG style |
| `{{PARTS}}` | "the runtime, a prompt, an eval"; "the API, the schema, the client" | The parts of the system a decision can touch, as the plan's D-rows name them. A repository with one part writes "the code" |
| `{{EVIDENCE_SOURCES}}` | "the service logs, the database, a live probe"; "a failing test and the user's report" | What confirms a bug's root cause. A repository with no logs or data names what it does have |
| `{{DRAWN}}` | "the web app's screens"; "the CLI's output"; "nothing: a headless service" | The surfaces a person sees; when to draw is `design_workflow.md`'s |
| `{{LABELS}}` | "one `type/…`, one `priority/…`, one `area/…` when one fits" | The repository's own set; the kickstart's taxonomy is the default |
| `{{COMMENT_BLOCK_BUDGET}}` / `{{DOC_COMMENT_BUDGET}}` / `{{FILE_HEADER_BUDGET}}` | `8` / `20` / `25` | **Derive, don't copy** — `codebase_review.md` § Phase 2 has the procedure. The doc-comment number is the larger of the first two: a doc comment is also an API contract |
| `{{LINT_TOOL}}` | `ruff`, `eslint` + `prettier`, `golangci-lint`, `clippy` + `rustfmt`, `swiftlint` | One per role |
| `{{PKG_MANIFEST}}` | `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml` | Where tool config lives |
| `{{deploy_or_publish_guide}}` | `deployment`, `publishing`, `release`, `distribution` | Filename of the shipping guide |
| `{{primary-side-effect target}}` | "database", "filesystem", "device camera", "network calls to the API" | What integration tests must hit for real |
| `{{database/state-store}}` | "database", "keychain", "user defaults", "Core Data store" | Used in the "blast radius" warning |

---

## Project-type adaptation notes

Where the template's defaults assume a long-running service, here's how each project type usually diverges. Keep these as a checklist when filling the template. Any type that ships a user-facing surface (web, desktop, mobile, TUI, or a CLI's flag/output conventions) should also stand up a design-language reference early — see [project_kickstart.md](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md) § User-facing surface foundation.

### Web service / bot / API

- The default template fits: the release workflow deploys to a runtime host.
- A `/health` endpoint reports the version, and the checklist's version probe calls it after a deploy.

### Desktop app (Electron / Tauri / Qt / native)

- The release publishes a signed installer to GitHub Releases; an About dialog shows the version.
- Keep the `[desktop]` line under *Secrets and security*.
- Integration tests hit a real filesystem; UI tests are their own category.

### Mobile app (iOS / Android / React Native / Flutter)

- The release uploads to TestFlight / the Play Console internal track, by Fastlane lanes (or equivalent) the publish guide documents.
- Keep the `[mobile]` line under *Secrets and security*; the version probe is the app's settings screen.

### CLI tool

- The release publishes to PyPI / npm / crates.io / a Homebrew tap; keep the `[cli]` line under *Secrets and security*.
- A `--version` flag reads the single source of truth, and the smoke check installs the published artifact in a clean environment and runs it.

### Library

- No transport layer: drop the `{{ENTRY_DIR}}` line from *Code layout*.
- The release publishes to a registry; keep the `[library]` line under *Secrets and security*, and publishing under *Executing actions*' confirm list.
- The coverage floor is usually higher: a library's bugs reach more callers.

### Monorepo with multiple project types

- Either split AGENTS.md per workspace (each workspace gets its own root) or write a single AGENTS.md with explicit per-workspace sections. Do not mix the rules into one undifferentiated list.

---

## When to update the template itself

If you've kickstarted two or more projects with this template and noticed the same paragraph getting hand-edited the same way each time, that paragraph is wrong and the template should be updated. File it as an issue on the kit from the task that found it; the kit's own task changes it, and every project meets the new template at its next `lifecycle upgrade` — improvements compound across every future project. Conversely, if a section keeps getting deleted on copy, consider whether it belongs in `project_kickstart.md` instead, since the template should be terser than the playbook.
