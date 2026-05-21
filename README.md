# orwir project templates — canonical source

This gist is the **single source of truth** for the reusable project-setup docs.
Each project keeps a *mirror* copy in `docs/guides/`; edit here, then re-sync the
mirrors.

## Files

- **`project_kickstart.md`** — language-agnostic playbook for standing up and
  growing a project (branching, releases, CI, docs layers, tracking, the
  user-facing-surface foundation, what to grow / what to skip).
- **`agents_template.md`** — copy-and-fill skeleton for a new repo's `AGENTS.md`
  (the operating contract AI assistants read).

## Use in a project

Mirror both files into the repo and point `AGENTS.md` at the kickstart as the
"why":

```bash
base=https://gist.githubusercontent.com/orwir/d288ef4ec7dcb37a4cd3e9ae2019c037/raw
curl -sL "$base/project_kickstart.md" -o docs/guides/project_kickstart.md
curl -sL "$base/agents_template.md"   -o docs/guides/agents_template.md
```

Re-run the same two lines to pull the latest after editing the canonical here.

## Edit the canonical

- Web: edit this gist in the browser.
- CLI: `gh gist edit d288ef4ec7dcb37a4cd3e9ae2019c037`
- Clone: `git clone https://gist.github.com/d288ef4ec7dcb37a4cd3e9ae2019c037.git`

When a project discovers a reusable pattern (not project-specific), fold it back
into the relevant file *here* so every project inherits it on the next sync.
