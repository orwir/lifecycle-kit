# AGENTS.md template

A copy-and-fill skeleton for the operating contract that AI coding assistants (Claude Code, OpenAI Codex CLI, Cursor, Gemini, Copilot, Aider) read on every change. Drop this into the root of a new repo as `AGENTS.md`, replace the `{{placeholder}}` tokens, and delete sections that don't apply to your project type.

Companion to [project_kickstart.md](project_kickstart.md): the kickstart explains *why* each rule exists; this file is the *rule itself*, compressed to the form the assistant actually reads.

---

## How to use this template

1. **Copy** the section under "Template" (everything below `---`) into a new `AGENTS.md` at your repo root.
2. **Fill placeholders.** Every `{{token}}` is a fill-in. The comments after each one tell you what kind of value goes there.
3. **Prune by project type.** Some sections include alternative paragraphs marked `[web-service]`, `[desktop]`, `[mobile]`, `[cli]`, `[library]` — keep the one that matches and delete the others. Sections with no marker apply to all project types.
4. **Add vendor shims if needed.** Symlinks don't work reliably on Windows, so add real files: `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` — each one line of "Read [AGENTS.md](AGENTS.md) before making any change" plus any vendor-specific addendum.
5. **Keep it under ~150 lines.** Longer files get skimmed instead of read. Push rationale into `CONTRIBUTING.md` and the kickstart; keep `AGENTS.md` as the compressed contract.

### What belongs in AGENTS.md (and what doesn't)

| Belongs | Belongs elsewhere |
|---|---|
| Rules an assistant must apply on every change | Rationale and history → `CONTRIBUTING.md` |
| The smallest viable list of "don'ts" | Tutorials and walkthroughs → `docs/guides/` |
| Pointers to the source-of-truth docs | Architecture deep-dives → `docs/architecture/` |
| Loop-safe defaults (no `--no-verify`, no destructive shortcuts) | Decision rationale → ADRs |

If a rule is in `AGENTS.md` only to explain *why*, move it. The contract should be terse enough that violations are obvious.

---

## Template

Everything below this line is the template body. Copy it as-is, then fill placeholders.

```markdown
# Agent instructions — {{PROJECT_NAME}}

You are working in the `{{OWNER}}/{{REPO}}` repository: a {{LANGUAGE}} {{PROJECT_TYPE}} ({{ONE_LINE_DESCRIPTION}}). Follow every rule below on every code change. When a rule conflicts with a direct user instruction in the current session, ask the user to clarify before proceeding.

For the full rationale behind any rule, read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/guides/project_kickstart.md](docs/guides/project_kickstart.md). These rules are the compressed operating contract; those files are the source of truth when details are ambiguous.

---

## Branching and commits

- **Default flow:** {{commit directly to `develop` | open a feature branch}}. {{Reason: solo-maintained with pre-push hooks mirroring CI | reason: multiple contributors review via PR}}. Pick one and stick to it; mixing flows breaks the project board lifecycle.
- **When to use a feature branch:** open one (`feat/…`, `fix/…`, `chore/…`, `docs/…`, `refactor/…`, `perf/…`) when the work is multi-commit and should land atomically, is risky or invasive (schema migrations, auth, payments, cross-cutting refactors), spans multiple sessions, or benefits from a diff-review pass before merging. When in doubt, branch.
- **Never push directly to `{{PRODUCTION_BRANCH}}`** ({{e.g., `master`, `main`, `release`}}). It {{auto-deploys | triggers the release pipeline | publishes artifacts}}; merges only via release PRs from `{{INTEGRATION_BRANCH}}`.
- **Automated feature-branch flow:**
  ```bash
  git checkout -b feat/my-thing
  # ... work, commit, push ...
  git push -u origin feat/my-thing
  gh pr create --fill --base {{INTEGRATION_BRANCH}}
  gh pr merge --squash --auto --delete-branch
  ```
  Auto-merge must be enabled once in the repo's Settings → General → Pull Requests.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  - Allowed prefixes: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.
  - Optional scope in parentheses: `fix(parser): …`, `chore(deps): …`, `chore(ci): …`.
  - Subject in imperative mood, no trailing period, under 72 characters.
  - Body (when used) explains **why**, not what. The diff shows what.
- Never use `--no-verify` to bypass hooks. If a hook fails, fix the underlying issue. If the hook is wrong, say so and propose a fix — do not skip.

## Task workflow — three phases

Every tracked task moves through three explicit phases. **Do not collapse them** — each gate is the user's, not yours to assume.

1. **Clarify.** Read the ticket and/or description, ask for any missing detail, and surface scope or constraint conflicts *before* writing code. Move the board item to `In Progress` when you pick it up. Implementation does not begin until the details are clear — whether from the ticket, added clarification, or the discussion.
2. **Implement & stop.** Do the work in full: code, tests, docs, fixtures. Run the local gate (lint + tests). Then **stop and hand back for review** — leave the changes **uncommitted** in the working tree. If review turns up corrections, work them out here and stop again. Do **not** commit, push, or close anything in this phase.
3. **Complete — on explicit approval only.** An explicit go-ahead ("complete the task", "lgtm", or equivalent) is the *only* trigger to commit the task work, push, close the ticket, and move the board item to `Done`. No approval → no commit, no push, no close. The same gate applies to `git push`, `gh pr create`, and `gh pr merge` — auto mode is permission to write code without re-asking, not permission to land it.

## Code layout

- `{{ENTRY_DIR}}` ({{e.g., `apps/`, `cmd/`, `bin/`}}) contains transport / entry points. These are thin — they know about {{e.g., HTTP, Discord, CLI args, OS event loops, native UI frameworks}}.
- `{{LOGIC_DIR}}` ({{e.g., `packages/`, `lib/`, `internal/`, `core/`}}) contains pure logic. **Never import transport libraries ({{e.g., `discord`, `fastapi`, `tauri`, `react-native`, `pyqt`, `cobra`}}) from `{{LOGIC_DIR}}`.** Logic must be testable without spinning up the transport.
- `tests/` mirrors the source tree 1:1. A new file `{{LOGIC_DIR}}/foo/bar.{{EXT}}` gets a new file `tests/{{LOGIC_DIR}}/foo/test_bar.{{EXT}}`. No clever grouping.
- `migrations/` (if applicable) contains numbered schema files. Don't rewrite applied migrations — add a new one.
- `scripts/` is for one-off tooling. Don't move runtime code here.
- Do not create new top-level directories without a clear reason and user sign-off.

## Versioning and release

- The version string lives in exactly one place: `{{VERSION_FILE}}` ({{e.g., `packages/core/__init__.py` → `__version__`, `package.json` → `"version"`, `Cargo.toml` → `version`, `pubspec.yaml` → `version`}}). Every other consumer ({{e.g., deploy workflow, `/health` endpoint, About dialog, `--version` flag, image tags, installer name}}) reads from it. **Do not duplicate the version string anywhere else.**
- Update `CHANGELOG.md` for any user-visible change. Style rules:
  - **One line per entry.** If it needs a paragraph, it belongs in the linked issue/PR.
  - **User/operator-visible only.** New command, new env var, changed default, observable behaviour, user-visible fix — yes. Internal refactors, renames, new log fields nobody consumes — no.
  - **Reference the issue/PR** (`- Fix X (#42)`). Details and migration prose live there.
  - **Group under Added / Changed / Fixed / Removed once per version.** Collapse duplicate section headers within a release.
  - **No rationale prose.** "In production this lands at…", "we did this because…", "which means…" belong in the commit message or PR description. Drop the effect clause when it just restates the mechanism.
- The release process is documented as a numbered checklist in [CONTRIBUTING.md § Releasing](CONTRIBUTING.md). Do not invent shortcuts.

## Release workflow — three phases

Releases run in three explicit phases too, mirroring the task workflow. Full mechanics (commands, file targets, post-merge steps) live in [CONTRIBUTING.md § Releasing](CONTRIBUTING.md); this section is the contract.

1. **Prepare.** Decide the next version yourself from [semver](https://semver.org/) based on the changes since the last release (breaking → major, additive → minor, fixes only → patch) — unless the user names a specific version. Bump the version string in `{{VERSION_FILE}}`, date the CHANGELOG entry, complete any doc-sync, commit, and open the `{{INTEGRATION_BRANCH}} → {{PRODUCTION_BRANCH}}` release PR. All reversible inside this phase; no extra approval needed.
2. **Review.** **Stop** and surface the PR URL plus a one-paragraph summary. Wait for explicit "proceed". Work out any corrections here, then stop again.
3. **Ship — on explicit approval only.** The "proceed" authorizes the entire ship phase in one batch: merge the release PR, push the `vX.Y.Z` tag, fast-forward the integration branch, publish the GitHub release, close the milestone, and verify post-deploy. A prior "do the release" instruction does **not** extend past the review checkpoint — only the phase-3 approval does. The publish steps (PR merge + tag push) are irreversible.

## Tests and quality gates

- Every new feature or bug fix gets tests. New code without tests is incomplete.
- Tests run with `{{TEST_RUNNER}}` ({{e.g., `pytest`, `vitest`, `jest`, `go test`, `cargo test`, `xctest`}}). See `{{PKG_MANIFEST}}` for config.
- Coverage floor is `{{COVERAGE_FLOOR}}%` and enforced by both pre-commit (pre-push stage) and CI. If your change drops coverage below the floor, add tests, don't lower the floor.
- Integration tests hit real I/O ({{e.g., a real SQLite database, a real filesystem, a real local HTTP listener}}). **Do not mock the {{primary-side-effect target}} in integration tests.** Unit tests of pure functions are fine without it.
- Lint + format: `{{LINT_TOOL}}` only ({{e.g., `ruff`, `eslint` + `prettier`, `gofmt` + `golangci-lint`, `rustfmt` + `clippy`, `swiftlint` + `swift-format`}}). Never introduce competing tools that do the same job — pick one per role and stick with it.
- Pre-commit is wired to run the same commands as CI. If something passes locally, it should pass CI.

## Documentation

- Respect the documentation layers:
  - `README.md` — end-user entry point (install, use)
  - `CONTRIBUTING.md` — how to work in the repo (branching, release, commit style)
  - `CHANGELOG.md` — release history
  - `docs/product/` — vision, requirements, the "what" and "why"
  - `docs/architecture/` — the "how": components, data flow, config reference
  - `docs/guides/` — task-oriented howtos (deploy / publish / package, extend, kickstart, comprehensive review)
  - `docs/adr/` — architecture decision records, one per significant choice
- **Do not create new documentation files unprompted.** Work from conversation context; if you need to capture a decision, suggest an ADR and wait for approval.
- **Do not recreate `roadmap.md`** or any equivalent tracking file. Tracked work lives on GitHub: issues, milestones, the project board.
- When referencing code, cite `file.{{EXT}}:123` style. Markdown links in docs use **file-relative paths** so they resolve in every renderer (GitHub web, IDE preview, static site generators). From a doc under `docs/adr/`, that means `[{{LOGIC_DIR}}/foo.{{EXT}}](../../{{LOGIC_DIR}}/foo.{{EXT}})` — workspace-root-relative paths like `[foo.{{EXT}}]({{LOGIC_DIR}}/foo.{{EXT}})` only resolve in workspace-aware IDE tooling and 404 everywhere else.
- Avoid `#L123` line anchors in long-lived docs (ADRs especially). Line numbers rot on every refactor — keep the file ref, drop the line.
- When writing an ADR, use the four-section format: Status / Context / Decision / Consequences. Number it sequentially.

## Keep documentation in sync with code

Documentation is a first-class deliverable. **Before you commit any change, check whether any existing doc becomes wrong, incomplete, or misleading because of it. If yes, update the doc in the same commit.** Do not defer doc updates to "later" — drift compounds, and a doc that lies is worse than a doc that's missing.

### Change → required doc mapping

| Change | Must update |
|---|---|
| New user command, argument, response format, or UI surface | `README.md` |
| New env var, config option, or changed default | `.env.example` (or equivalent config schema) + `README.md`; also `docs/guides/{{deploy_or_publish_guide}}.md` if it affects shipping |
| New component, changed data flow, new integration | `docs/architecture/architecture.md` |
| Non-obvious design decision | new ADR in `docs/adr/` (Status / Context / Decision / Consequences) |
| Any user-visible change | `CHANGELOG.md` entry under Added / Changed / Fixed / Removed |
| New capability or extension point | `docs/guides/extension_guide.md` |
| New/changed UI component or pattern (if the project has a surface) | the design-language reference (e.g. `docs/guides/design_language.md`) |
| Process / workflow change | `CONTRIBUTING.md`; also `docs/guides/project_kickstart.md` if the pattern is reusable across projects |

### Task-closing checklist

Before marking an issue, PR, or user-requested task as complete, verify:

1. Every doc touched by the change is up to date.
2. `CHANGELOG.md` has an entry for any user-visible change.
3. New env vars, commands, config options, labels, or workflows are documented where an operator would look for them.
4. Non-obvious decisions have an ADR, and the ADR is referenced from the code or doc where the decision surfaces.
5. If the change introduces a reusable pattern (not just local code), the reusable pattern is reflected in the relevant guide (`project_kickstart.md`, `extension_guide.md`, deploy/publish guide).

Only after this checklist passes should you report the task as done.

## Issues and pull requests

- New issues use the templates in `.github/ISSUE_TEMPLATE/`:
  - `bug.md` for defects and regressions
  - `task.md` for features, refactors, docs, infra
- Technical-details sections use `[NEW]` / `[MODIFY]` / `[DONE]` markers on concrete file paths so scope is scannable.
- After creating an issue, apply labels from all three axes: `type/…`, `area/…`, `priority/…`. Add it to the milestone if scoped, and add it to the project board with Status = **Backlog** (do not leave it in "No Status" — that hides it from the board views).
- **Reflect work state on the project board.** Backlog → In Progress → Done is the full lifecycle. When you start working on an issue, move it to **In Progress** as the first step — before reading code, before planning, before writing anything. When the work lands, move it to **Done** as part of the same close-out flow that closes the issue.
- **Position to top on every board write.** Projects v2 has no Created-date sort, so column order is raw position. After every `gh project item-add` and after every status change, call `updateProjectV2ItemPosition` with `afterId: null` so the just-touched item lands at the top of its new column.
- PRs use `.github/pull_request_template.md`. Every PR has a Summary, a linked issue (`Closes #N`), and a concrete Verification section.
- Reference issues in commit bodies and PR descriptions. Do not invent issue numbers — confirm they exist with `gh issue view <N>` first.

## Secrets and security

- Never commit `.env`, credentials, API keys, signing certificates, provisioning profiles, or any file matching common secret patterns. A `gitleaks` (or equivalent) pre-commit hook should catch most of this — do not disable it.
- Never log decrypted secrets, auth tokens, or payment data. Log identifiers (`provider`, `user_id`, `key_fingerprint`), not values.
- Document secret rotation in `docs/guides/{{deploy_or_publish_guide}}.md` for every long-lived credential. When you're being paged at 2am you do not want to improvise.
- All new CI/CD workflows declare least-privilege `permissions:` blocks, not inherit repo defaults.

[web-service] Run the production container as a non-root user. Reverse-proxy and TLS termination live outside the application image.
[desktop] Code-sign release artifacts; document the signing certificate location and rotation procedure.
[mobile] Provisioning profiles and signing certificates live in {{e.g., Fastlane Match, EAS, App Store Connect}}, never in the repo.
[cli] Tarballs / archives published to package registries are signed or checksummed; document how to verify.
[library] Published packages use the registry's trusted-publisher / OIDC flow when available, not long-lived tokens.

## Executing actions

- Carefully consider blast radius before destructive actions. Freely: edit files, run tests locally, create feature branches. Confirm first: `git reset --hard`, `git push --force`, force-pushing, deleting branches, dropping {{database/state-store}} tables, amending published commits, pushing to shared remotes, publishing to a registry, uploading a release artifact.
- Tool approval in one scope does not extend to other scopes (see the *Task workflow* and *Release workflow* sections for the per-workflow gates).
- If you hit unfamiliar files, branches, or config, investigate before deleting — it may be the user's in-progress work.
- When running into a failing check, diagnose the root cause. Do not bypass with `--no-verify`, test-skip markers, lint-suppress comments, or similar. Ask the user if you're stuck.

## When editing code

- **Simplicity First — does the surviving justification still demand this shape?** When you touch a load-bearing abstraction (decorator, cache, ContextVar / thread-local / async-local, registry, factory, protocol, dependency-injection container), ask: what assumption forces this to be shaped the way it is, and does that assumption still hold? Long-lived projects accumulate residue because each individual scope cut (an ADR revision, a follow-up PR) was too small to justify restructuring on its own. Examples of residue: a request-scoped cache that exists only because a per-call decorator re-runs an underlying check that now fires once; an async-local that propagates data across layers when the data can be passed explicitly; a generic abstraction with exactly one caller and one implementation. When you spot residue, surface the simplification *before* layering on another patch — don't extend a pattern whose justification has eroded. Coupled residue (cache + decorator that only make sense together) lands as one change, not two. This applies to *all* work, not just review passes.
- Prefer editing existing files over creating new ones.
- **If the project ships a user-facing surface, conform to its design language.** Any UI edit — web, desktop, or TUI, and a CLI's flag/output conventions — reuses the documented components, data rendering, and UX patterns in the design-language reference (e.g. `docs/guides/design_language.md`); don't introduce a parallel variant. Applies to every UI edit, not just new screens. (Drop this rule for a headless service or library. See the *User-facing surface foundation* section in `docs/guides/project_kickstart.md`.)
- Don't add comments that explain **what** — the code shows that. Only add comments when the **why** is non-obvious (a hidden constraint, a subtle invariant, a workaround for an external bug).
- **Issue references in comments / docstrings.** A `(#N)` or `(issue #N)` parenthetical is only allowed when it anchors a *design pointer* — an ADR number, a specific external bug, or a non-obvious subsystem constraint — that the surrounding comment still reads as load-bearing rationale without. The bare `# added in #N` / `# fixes #N` / `(issue #N)` tombstone is banned: it tells a future reader nothing once the linked thread is buried. Test the comment by deleting the parenthetical — if the remaining prose still answers "why", keep the ref; if it collapses to a WHAT-comment, the ref was carrying the rationale and the rationale needs to be inlined instead. Same rule for test docstrings.
- No backwards-compatibility shims, dead-code tombstones, or `# removed X` comments. Delete cleanly.
- No feature flags for work that can simply ship.
- No half-finished implementations. If scope is too big, split the PR and say so; don't leave stubs.
- Do not add error handling for impossible scenarios. Validate at system boundaries (user input, external APIs, deserialization), trust internal invariants.
- Match existing patterns in the file you're editing. If the existing pattern is wrong, fix it in a separate commit with a clear message.

## What NOT to do

- Do not push to `{{PRODUCTION_BRANCH}}`.
- Do not duplicate the version string.
- Do not `--no-verify`.
- Do not commit `.env`, secrets, signing material, or generated credentials.
- Do not recreate `roadmap.md` or any other ad-hoc tracking file.
- Do not create documentation files unprompted.
- Do not introduce competing lint/format/type tools when one already covers the role.
- Do not use emojis in code or docs unless the user explicitly asks.
- Do not mock the {{primary-side-effect target}} in integration tests.
- Do not add `print()` / `console.log` / `println!` for debugging — use the project's structured logger.
- Do not add dependencies casually. New dependencies need a reason that justifies the supply-chain surface.
- Do not improvise a comprehensive-review process — when asked for one, follow `docs/guides/codebase_review.md`.

## When in doubt

1. Read the relevant section of `CONTRIBUTING.md` or `docs/guides/project_kickstart.md`.
2. Check if an existing file already solves the problem. Reuse before creating.
3. Ask the user. A 30-second clarification beats a 30-minute undo.
```

---

## Placeholder reference

Quick reference for each `{{token}}` used above.

| Token | Example values | Notes |
|---|---|---|
| `{{PROJECT_NAME}}` | "Murmur", "Acme Reader" | Human-readable name |
| `{{OWNER}}/{{REPO}}` | `orwir/murmur` | GitHub slug |
| `{{LANGUAGE}}` | "Python 3.13", "Rust 2024", "TypeScript / Node 22", "Swift 5.10" | Primary language and version |
| `{{PROJECT_TYPE}}` | "async Discord bot", "macOS menu-bar app", "iOS app", "CLI tool", "library" | One-noun shape |
| `{{ONE_LINE_DESCRIPTION}}` | "multi-provider LLM support, SQLite storage, Docker deployment" | Sub-30 words |
| `{{PRODUCTION_BRANCH}}` | `master`, `main`, `release` | Auto-deploy or publish target |
| `{{INTEGRATION_BRANCH}}` | `develop`, `main`, `next` | Default branch, where work lands |
| `{{ENTRY_DIR}}` / `{{LOGIC_DIR}}` | `apps/` + `packages/`; `cmd/` + `internal/`; `src/bin/` + `src/lib/` | Transport-vs-logic split |
| `{{EXT}}` | `py`, `ts`, `tsx`, `go`, `rs`, `swift`, `kt` | Primary source extension |
| `{{VERSION_FILE}}` | `packages/core/__init__.py`, `package.json`, `Cargo.toml`, `pubspec.yaml` | Single source of truth |
| `{{TEST_RUNNER}}` | `pytest`, `vitest`, `jest`, `go test`, `cargo test`, `xctest`, `flutter test` | One command, one runner |
| `{{COVERAGE_FLOOR}}` | `55`, `70`, `80` | Pick something you can defend |
| `{{LINT_TOOL}}` | `ruff`, `eslint` + `prettier`, `golangci-lint`, `clippy` + `rustfmt`, `swiftlint` | One per role |
| `{{PKG_MANIFEST}}` | `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml` | Where tool config lives |
| `{{deploy_or_publish_guide}}` | `deployment`, `publishing`, `release`, `distribution` | Filename of the shipping guide |
| `{{primary-side-effect target}}` | "database", "filesystem", "device camera", "network calls to the API" | What integration tests must hit for real |
| `{{database/state-store}}` | "database", "keychain", "user defaults", "Core Data store" | Used in the "blast radius" warning |

---

## Project-type adaptation notes

Where the template's defaults assume a long-running service, here's how each project type usually diverges. Keep these as a checklist when filling the template. Any type that ships a user-facing surface (web, desktop, mobile, TUI, or a CLI's flag/output conventions) should also stand up a design-language reference early — see `docs/guides/project_kickstart.md` § User-facing surface foundation.

### Web service / bot / API
- Default template fits.
- `/health` version probe is mandatory; smoke-check it post-deploy.
- Production branch auto-deploys to a runtime host.

### Desktop app (Electron / Tauri / Qt / native)
- Replace "deploy to VPS" with "publish signed installer to GitHub Releases".
- Drop `/health` for an About dialog showing the version.
- Add a `signing` section under Secrets covering certificate storage and rotation.
- Integration tests hit a real filesystem; UI tests are their own category.

### Mobile app (iOS / Android / React Native / Flutter)
- Replace "deploy" with "upload to TestFlight / Play Console internal track".
- Use Fastlane lanes (or equivalent) for the release pipeline; document the lanes in the publish guide.
- Signing certificates and provisioning profiles never enter the repo — use Match / EAS / App Store Connect.
- The "version probe" is the app's settings screen.

### CLI tool
- Replace "deploy" with "publish to PyPI / npm / crates.io / Homebrew tap".
- `--version` flag is mandatory and reads from the single source of truth.
- Smoke check: install the published artifact in a clean environment and run `--version`.

### Library
- No transport layer — drop the `{{ENTRY_DIR}}` row from Code layout and keep only `{{LOGIC_DIR}}`.
- Replace "release" with "publish to registry".
- Cut the "Executing actions" line about deploys; keep the publish gate.
- Coverage floor is usually higher (libraries get reused; bugs hurt more callers).

### Monorepo with multiple project types
- Either split AGENTS.md per workspace (each workspace gets its own root) or write a single AGENTS.md with explicit per-workspace sections. Do not mix the rules into one undifferentiated list.

---

## When to update the template itself

If you've kickstarted two or more projects with this template and noticed the same paragraph getting hand-edited the same way each time, that paragraph is wrong and the template should be updated. Edit the canonical gist (then re-sync each project's mirror) — improvements compound across every future project. Conversely, if a section keeps getting deleted on copy, consider whether it belongs in `project_kickstart.md` instead, since the template should be terser than the playbook.
