<!-- Installs to CONTRIBUTING.md at the repo root. Fill every {{token}}, delete
     sections that don't apply. It holds the steps run as written, by a person or
     by the lifecycle kit's release skill: setting up, releasing, hotfixing.
     Everything an assistant applies on every change lives in AGENTS.md. -->

# Contributing — {{PROJECT_NAME}}

How to set this repository up and how to release it. Branching, commits, the
quality gates, the task's review rounds and the board are this repository's
operating contract, [AGENTS.md](AGENTS.md); why each rule exists is the lifecycle
kit's
[project_kickstart.md](https://github.com/orwir/lifecycle-kit/blob/main/method/project_kickstart.md).

## Local setup

1. Clone and install dependencies: `{{SETUP_CMD}}` ({{e.g., `uv sync`, `npm install`}}).
2. Install the git hooks: `{{HOOK_INSTALL_COMMAND}}` ({{e.g., `pre-commit install
   --hook-type pre-commit --hook-type pre-push`}}). Non-negotiable — the pre-push
   stage is the local CI gate. Install each tool the hooks call that the hook
   manager does not install itself: {{TOOLS_THE_HOOKS_CALL}} ({{e.g., `gitleaks`}}).
   A hook that finds one missing says its check did not run.
3. Copy `.env.example` → `.env` and fill the values (the comments in
   `.env.example` say where each one comes from).

## Releasing

[SemVer](https://semver.org), picked by what landed since the last tag: a
release ships what has landed. The checklist is literal — execute it in order,
no shortcuts:

1. **Read what the dispatch's CI will read** (drop this step where no job of
   `ci.yml` reads more under the release's dispatch than on a push): run
   {{WIDENED_CHECK}} ({{e.g., the secret scan, which gitleaks-action runs over
   the whole history under a dispatch: `gitleaks git -v --redact` on a fresh
   clone, which holds what the dispatch's checkout holds, at the job's gitleaks
   version and config}}) and land what it finds before the bump. A
   secret it finds is rotated and its finding allowlisted ({{e.g., its
   fingerprint in `.gitleaksignore`}}), never only deleted: the history keeps it.
2. **Bump the version** in `{{VERSION_FILE}}` — the single source of truth.
3. **Update `CHANGELOG.md`**: date the new section, group entries under
   Added / Changed / Fixed / Removed, reference issues (`#N`).
4. **Commit and push** the release commit to `{{INTEGRATION_BRANCH}}`.
5. **Review the release** on the compare link from the last tag (`git fetch
   --tags origin` first: the workflow makes the tags on GitHub) to that commit
   (`https://github.com/<owner>/<repo>/compare/v<last>...<sha>`), with the
   readings of every check that runs only before a release. A correction lands
   on `{{INTEGRATION_BRANCH}}`, and the review reads the new head.
6. **— Checkpoint —** If an AI assistant is driving, it stops here and waits
   for explicit approval. Step 7 is irreversible and ships to production; a
   prior "do the release" does not extend past this line.
7. **Dispatch the release workflow** (`{{RELEASE_WORKFLOW}}`, named under
   `[release]` in `.lifecycle.toml`) on the reviewed commit, and watch the run
   to its end: `lifecycle release <sha>`. It refuses when
   `{{INTEGRATION_BRANCH}}` moved since the review (check the version and the
   changelog against the new head, review it, then dispatch that) or when the
   version is tagged already; otherwise it builds, ships, and creates the tag
   and the GitHub Release last.
8. **Verify the deployment**: `{{VERSION_PROBE}}` ({{e.g., `curl
   https://…/health`, `--version` of the published artifact}}) reports the new
   version. A release isn't done until this passes.

## Hotfixes

For an urgent production fix while `{{INTEGRATION_BRANCH}}` holds unreleased
work:

1. Cut `hotfix/…` from the last release's tag: `git fetch --tags origin`, then
   `git switch -c hotfix/<name> v<last>`. Where that tag is older than the release workflow, bring the
   workflow file over from `{{INTEGRATION_BRANCH}}` first: a dispatch runs the
   workflow file of the branch it names.
2. Fix, with a test that fails before and passes after, and push the branch.
   Nothing merges it yet.
3. Release from the branch by the Releasing steps, with `hotfix/<name>`
   wherever they name `{{INTEGRATION_BRANCH}}`: the patch version, the release
   commit pushed to the branch, corrections landed on it, and the dispatch
   `lifecycle release <sha> --ref hotfix/<name>`.
4. Merge the branch into `{{INTEGRATION_BRANCH}}` with a merge commit (`git
   merge --no-ff`), never squashed, so the tag stays in its history, and push.
5. Delete the hotfix branch — remote and local.

With nothing unreleased on `{{INTEGRATION_BRANCH}}`, a fix is an ordinary task
and an ordinary patch release.
