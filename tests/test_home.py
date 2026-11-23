import json
import subprocess

import pytest
from lifecycle import cli, doctor, guides, home
from lifecycle.config import load

NOT_SIGNED_IN = "To get started with GitHub CLI, please run:  gh auth login\n"


class FakeGh:
    """``home.gh`` answering from ``replies``, keyed by a call's first two words: a reply is
    ``(code, stdout, stderr)``, or an exception to raise. Each call is kept."""

    def __init__(self, **replies):
        self.replies = {"api_user": (1, "", NOT_SIGNED_IN), **replies}
        self.calls = []

    def __call__(self, *args, cwd, timeout=None):
        self.calls.append(args)
        reply = self.replies.get("_".join(args[:2]), (1, "", "unexpected call"))
        if isinstance(reply, Exception):
            raise reply
        code, out, err = reply
        return subprocess.CompletedProcess(["gh", *args], code, out, err)

    def made(self, *words):
        return [args for args in self.calls if args[: len(words)] == words]


def install(monkeypatch, **replies):
    fake = FakeGh(**replies)
    monkeypatch.setattr(home, "gh", fake)
    return fake


def configure(path, identity=True):
    """A git global config at ``path``: an identity where asked, and a default branch that is
    not ``main``, so the home's own branch is proven."""
    body = "[init]\n\tdefaultBranch = master\n"
    if identity:
        body += "[user]\n\tname = Ada Example\n\temail = ada@example.com\n"
    path.write_text(body, encoding="utf-8")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """git reads only a config of the test's, gh is never the real one, and the user folder
    is the test's."""
    gitconfig = tmp_path / "gitconfig"
    configure(gitconfig)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    (tmp_path / "user").mkdir()
    monkeypatch.setattr(home, "user_folder", lambda: tmp_path / "user")
    install(monkeypatch)
    return gitconfig


def sh(folder, *args):
    return subprocess.run(
        ["git", *args], cwd=folder, capture_output=True, text=True, check=True
    ).stdout.strip()


def listing(folder):
    return sorted(
        p.relative_to(folder).as_posix() for p in folder.rglob("*") if ".git" not in p.parts
    )


EXPECTED = sorted(
    [
        "AGENTS.md",
        ".lifecycle.toml",
        ".lifecycle.lock",
        "archived.md",
        "graduated.md",
        "active/.gitkeep",
        "archive/.gitkeep",
    ]
)


def test_an_empty_folder_becomes_a_home_doctor_finds_clean(tmp_path):
    folder = tmp_path / "ideas"
    made = home.setup(folder)
    assert made.made and made.committed == EXPECTED
    assert sh(folder, "symbolic-ref", "--short", "HEAD") == "main"
    assert sh(folder, "rev-list", "--count", "HEAD") == "1"
    assert sorted(sh(folder, "ls-files").splitlines()) == EXPECTED
    assert sh(folder, "status", "--porcelain") == ""
    template = guides.text(guides.METHOD / home.TEMPLATE)
    assert (folder / "AGENTS.md").read_text(encoding="utf-8") == template
    assert home.is_home(folder)
    assert doctor.check(load(folder)) == []


def test_claude_settings_are_committed_and_local_settings_and_os_files_are_not(tmp_path):
    folder = tmp_path / "ideas"
    (folder / ".claude").mkdir(parents=True)
    (folder / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (folder / ".claude" / "settings.local.json").write_text("{}\n", encoding="utf-8")
    for name in home.OS_FILES:
        (folder / name).write_text("", encoding="utf-8")
    made = home.setup(folder)
    assert made.committed == sorted([*EXPECTED, ".claude/settings.json"])
    tracked = sh(folder, "ls-files").splitlines()
    assert ".claude/settings.json" in tracked
    assert ".claude/settings.local.json" not in tracked
    assert not home.OS_FILES & set(tracked)


def test_an_empty_git_repository_becomes_a_home_on_main(tmp_path):
    folder = tmp_path / "ideas"
    folder.mkdir()
    sh(folder, "init", "-q")
    assert sh(folder, "symbolic-ref", "--short", "HEAD") == "master"
    assert home.setup(folder).made
    assert sh(folder, "symbolic-ref", "--short", "HEAD") == "main"
    assert sh(folder, "rev-list", "--count", "HEAD") == "1"


def test_a_home_is_left_as_it_is(tmp_path):
    folder = tmp_path / "ideas"
    home.setup(folder)
    head = sh(folder, "rev-parse", "HEAD")
    again = home.setup(folder)
    assert not again.made and again.committed == []
    assert sh(folder, "rev-parse", "HEAD") == head


def _a_file(folder):
    folder.mkdir()
    (folder / "notes.txt").write_text("mine\n", encoding="utf-8")
    return "is not empty: it holds notes.txt"


def _history(folder):
    folder.mkdir()
    sh(folder, "init", "-q")
    sh(folder, "commit", "-q", "--allow-empty", "-m", "first")
    return "a git repository with history"


def _on_the_kit(folder):
    folder.mkdir()
    (folder / ".lifecycle.toml").write_text('[branches]\nintegration = "main"\n', encoding="utf-8")
    return "is not empty: it holds .lifecycle.toml"


def _a_remote(folder):
    folder.mkdir()
    sh(folder, "init", "-q")
    sh(folder, "remote", "add", "origin", "https://example.com/someone/ideas.git")
    return "the remote https://example.com/someone/ideas.git"


def _inside(folder):
    outer = folder.parent
    sh(outer, "init", "-q")
    return f"inside the git repository at {outer}"


def _empty_repository_inside(folder):
    outer = folder.parent
    sh(outer, "init", "-q")
    folder.mkdir()
    sh(folder, "init", "-q")
    return f"inside the git repository at {outer}"


@pytest.mark.parametrize(
    "make", [_a_file, _history, _on_the_kit, _a_remote, _inside, _empty_repository_inside]
)
def test_a_folder_holding_anything_else_is_refused_with_nothing_written(tmp_path, make):
    outer = tmp_path / "outer"
    outer.mkdir()
    folder = outer / "ideas"
    why = make(folder)
    before = listing(outer)
    with pytest.raises(home.HomeError, match="no home set up") as refused:
        home.setup(folder)
    assert why in str(refused.value)
    assert listing(outer) == before
    assert not home.is_home(folder)


def test_only_a_configured_git_identity_counts(tmp_path, isolated):
    configure(isolated, identity=False)
    folder = tmp_path / "ideas"
    why = home.identity(folder)
    assert "user.name or user.email" in why and "git config --global user.email" in why
    with pytest.raises(home.HomeError, match=r"no home set up: git has no user.name"):
        home.setup(folder)
    assert not folder.exists()


def test_the_logs_take_the_gauntlets_table_headers_and_no_row(tmp_path):
    lines = guides.text(guides.METHOD / home.GAUNTLET).splitlines()
    logs = lines[lines.index("## The logs") :]
    first = logs.index(next(line for line in logs if line.startswith("| Date")))
    second = logs.index(next(line for line in logs if line.startswith("| Graduated")))
    folder = tmp_path / "ideas"
    home.setup(folder)
    for name, start in (("archived.md", first), ("graduated.md", second)):
        rows = [
            line
            for line in (folder / name).read_text(encoding="utf-8").splitlines()
            if line.startswith("|")
        ]
        assert rows == logs[start : start + 2], name


def test_the_logs_refuse_a_guide_that_lost_their_tables(tmp_path, monkeypatch):
    method = tmp_path / "method"
    method.mkdir()
    (method / home.GAUNTLET).write_text("## The logs\n\n| a |\n| - |\n", encoding="utf-8")
    monkeypatch.setattr(guides, "METHOD", method)
    with pytest.raises(home.HomeError, match="no longer opens with the two logs' tables"):
        home.log_headers()


def test_check_finds_a_home_from_the_folder_up_then_in_the_user_folder(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert home.check(None)["home"] is None
    default = tmp_path / "user" / "ideas"
    home.setup(default)
    assert home.check(None)["home"] == str(default.resolve())
    near = tmp_path / "near"
    home.setup(near)
    monkeypatch.chdir(near / "active")
    assert home.check(None)["home"] == str(near.resolve())


def test_check_proposes_a_folder_or_says_why_none(tmp_path, monkeypatch):
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    report = home.check(None)
    assert report["proposed"] == str(here.resolve()) and report["refused"] == []
    (here / "notes.txt").write_text("mine\n", encoding="utf-8")
    report = home.check(None)
    assert report["proposed"] == str((tmp_path / "user" / "ideas").resolve())
    assert [r["folder"] for r in report["refused"]] == [str(here.resolve())]
    (tmp_path / "user" / "ideas").mkdir()
    (tmp_path / "user" / "ideas" / "x.txt").write_text("", encoding="utf-8")
    report = home.check(None)
    assert report["proposed"] is None and len(report["refused"]) == 2
    given = home.check(tmp_path / "given")
    assert given["proposed"] == str((tmp_path / "given").resolve())
    assert listing(tmp_path / "user") == ["ideas", "ideas/x.txt"]


def test_check_names_git_and_the_gh_login_or_why_not(tmp_path, monkeypatch, isolated):
    monkeypatch.chdir(tmp_path)
    report = home.check(None)
    assert report["git"] == {"ready": True, "why": None}
    assert report["gh"]["login"] is None and "gh auth login" in report["gh"]["why"]
    install(monkeypatch, api_user=(0, "ada\n", ""))
    assert home.check(None)["gh"] == {"login": "ada", "why": None}
    install(monkeypatch, api_user=home.HomeError("gh is not installed"))
    assert home.check(None)["gh"] == {"login": None, "why": "gh is not installed"}
    configure(isolated, identity=False)
    assert home.check(None)["git"]["ready"] is False


@pytest.fixture
def local_home(tmp_path):
    folder = tmp_path / "ideas"
    home.setup(folder)
    return folder


def bare(path):
    subprocess.run(["git", "init", "-q", "--bare", str(path)], check=True)
    return path


def test_github_creates_a_private_repository_and_pushes_with_git(tmp_path, monkeypatch, local_home):
    remote = bare(tmp_path / "remote.git")
    fake = install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    backup = home.backup(local_home, "ideas")
    assert backup.created and backup.pushed and backup.url == str(remote)
    (create,) = fake.made("repo", "create")
    assert create == ("repo", "create", "ideas", "--private")
    assert sh(local_home, "remote", "get-url", "origin") == str(remote)
    assert sh(remote, "rev-parse", "main") == sh(local_home, "rev-parse", "HEAD")


def test_github_after_a_failed_push_pushes_and_creates_nothing(tmp_path, monkeypatch, local_home):
    remote = tmp_path / "remote.git"
    fake = install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    with pytest.raises(home.HomeError) as failed:
        home.backup(local_home, "ideas")
    assert f"`lifecycle home {local_home} --github ideas` again pushes" in str(failed.value)
    assert sh(local_home, "remote", "get-url", "origin") == str(remote)
    bare(remote)
    backup = home.backup(local_home, "ideas")
    assert backup.pushed and not backup.created
    assert len(fake.made("repo", "create")) == 1
    assert sh(remote, "rev-parse", "main") == sh(local_home, "rev-parse", "HEAD")


def test_a_pushed_home_creates_nothing(tmp_path, monkeypatch, local_home):
    remote = bare(tmp_path / "remote.git")
    install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    home.backup(local_home, "ideas")
    fake = install(monkeypatch)
    again = home.backup(local_home, "ideas")
    assert not again.created and not again.pushed and again.url == str(remote)
    assert fake.calls == []


def test_github_unready_is_refused_before_anything_is_written(tmp_path, monkeypatch, capsys):
    fake = install(monkeypatch)
    folder = tmp_path / "ideas"
    assert cli.main(["home", str(folder), "--github", "ideas"]) == 1
    assert "nothing written or created: gh is not signed in" in capsys.readouterr().err
    assert not folder.exists() and not fake.made("repo")
    home.setup(folder)
    head = sh(folder, "rev-parse", "HEAD")
    with pytest.raises(home.HomeError, match="no repository created: gh is not signed in"):
        home.backup(folder, "ideas")
    assert not fake.made("repo") and sh(folder, "rev-parse", "HEAD") == head
    assert home.origin(folder) is None


def test_a_failed_creation_leaves_the_local_home_and_names_the_retry(monkeypatch, local_home):
    taken = "GraphQL: Name already exists on this account (createRepository)\n"
    install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(1, "", taken))
    head = sh(local_home, "rev-parse", "HEAD")
    with pytest.raises(home.HomeError) as failed:
        home.backup(local_home, "ideas")
    assert "Name already exists" in str(failed.value)
    assert f"`lifecycle home {local_home} --github <name>` again" in str(failed.value)
    assert home.origin(local_home) is None
    assert sh(local_home, "rev-parse", "HEAD") == head
    assert sh(local_home, "status", "--porcelain") == ""


def test_the_command_prints_and_exits_by_outcome(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "ideas"
    assert cli.main(["home", str(folder)]) == 0
    assert capsys.readouterr().out.startswith(f"set up the ideas home in {folder.resolve()}")
    assert cli.main(["home", str(folder)]) == 0
    assert "an ideas home already: nothing written" in capsys.readouterr().out
    assert cli.main(["home", str(folder), "--check"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["home"] == str(folder.resolve()) and set(report) == {
        "home",
        "proposed",
        "refused",
        "here",
        "git",
        "gh",
    }
    remote = bare(tmp_path / "remote.git")
    install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    assert cli.main(["home", str(folder), "--github", "ideas"]) == 0
    assert f"backed up to {remote}, a new private repository" in capsys.readouterr().out
    assert cli.main(["home", str(folder), "--github", "ideas"]) == 0
    assert "backed up already" in capsys.readouterr().out
    busy = tmp_path / "busy"
    busy.mkdir()
    (busy / "notes.txt").write_text("", encoding="utf-8")
    assert cli.main(["home", str(busy)]) == 1
    assert capsys.readouterr().err.startswith("lifecycle: no home set up:")


def test_check_answers_as_json_with_git_missing(tmp_path, monkeypatch):
    nothing = tmp_path / "no-programs"
    nothing.mkdir()
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    monkeypatch.setenv("PATH", str(nothing))
    report = home.check(None)
    assert report["git"]["ready"] is False and "git is not installed" in report["git"]["why"]
    assert report["proposed"] is None
    with pytest.raises(home.HomeError, match="no home set up: git is not installed"):
        home.setup(tmp_path / "ideas")
    assert not (tmp_path / "ideas").exists()


def refuse_commits(tmp_path, gitconfig):
    """Every commit fails, by a pre-commit hook git runs on every OS: executable, since git
    skips a hook without that bit on Linux and macOS. Returns the hook."""
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    with gitconfig.open("a", encoding="utf-8") as config:
        config.write(f"[core]\n\thooksPath = {hooks.as_posix()}\n")
    return hook


def test_a_failed_commit_keeps_nothing_and_says_what_next(tmp_path, isolated):
    hook = refuse_commits(tmp_path, isolated)
    folder = tmp_path / "ideas"
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert "git commit failed" in str(failed.value)
    assert "Nothing was kept" in str(failed.value)
    assert f"`lifecycle home {folder}` again" in str(failed.value)
    assert not folder.exists()
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(home.HomeError, match="Nothing was kept"):
        home.setup(empty)
    assert empty.is_dir() and not any(empty.iterdir())
    hook.unlink()
    assert home.setup(folder).made


def test_a_failed_commit_in_a_repository_keeps_it_and_stages_nothing(tmp_path, isolated):
    refuse_commits(tmp_path, isolated)
    folder = tmp_path / "ideas"
    (folder / ".claude").mkdir(parents=True)
    (folder / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    sh(folder, "init", "-q")
    with pytest.raises(home.HomeError, match="Nothing was kept"):
        home.setup(folder)
    assert (folder / ".git").is_dir()
    assert sh(folder, "status", "--porcelain", "--untracked-files=all") == (
        "?? .claude/settings.json"
    )
    assert listing(folder) == [".claude", ".claude/settings.json"]
    assert sh(folder, "symbolic-ref", "--short", "HEAD") == "main"


def test_a_timed_out_commit_is_taken_back_and_named(tmp_path, monkeypatch):
    real = home.git

    def git(folder, *args, timeout=home.CALL_SECONDS):
        if args[:1] == ("commit",):
            raise home.HomeError(f"git commit -q gave no answer in {timeout} s")
        return real(folder, *args, timeout=timeout)

    monkeypatch.setattr(home, "git", git)
    folder = tmp_path / "ideas"
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert "git commit -q gave no answer" in str(failed.value)
    assert "Nothing was kept" in str(failed.value)
    assert not folder.exists()
    monkeypatch.setattr(home, "git", real)
    assert home.setup(folder).made


def test_what_the_rollback_cannot_take_away_is_named(tmp_path, isolated, monkeypatch):
    refuse_commits(tmp_path, isolated)
    monkeypatch.setattr(home.shutil, "rmtree", lambda path, ignore_errors=False: None)
    folder = tmp_path / "ideas"
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert f"Not taken away: {folder / '.git'}. Remove it and," in str(failed.value)
    assert "Nothing was kept" not in str(failed.value)
    assert f"`lifecycle home {folder}` again" in str(failed.value)
    assert (folder / ".git").is_dir() and listing(folder) == []


def test_a_file_the_rollback_cannot_delete_is_named_not_raised(tmp_path, isolated, monkeypatch):
    refuse_commits(tmp_path, isolated)
    real = home.Path.unlink

    def unlink(path, missing_ok=False):
        if path.name == home.TARGET:
            raise PermissionError(13, "held by another process", str(path))
        real(path, missing_ok=missing_ok)

    monkeypatch.setattr(home.Path, "unlink", unlink)
    folder = tmp_path / "ideas"
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert f"Not taken away: {folder / home.TARGET}. Remove it and," in str(failed.value)
    assert f"`lifecycle home {folder}` again" in str(failed.value)
    assert listing(folder) == [home.TARGET] and not (folder / ".git").exists()


def test_a_failed_add_claims_nothing_staged(tmp_path):
    folder = tmp_path / "ideas"
    (folder / ".claude").mkdir(parents=True)
    (folder / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    sh(folder, "init", "-q")
    (folder / ".git" / "index.lock").write_text("", encoding="utf-8")
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert "git add failed" in str(failed.value)
    assert "Nothing was kept" in str(failed.value)
    assert "staging" not in str(failed.value)
    assert listing(folder) == [".claude", ".claude/settings.json"]


def test_what_a_failed_add_did_stage_is_unstaged(tmp_path):
    folder = tmp_path / "ideas"
    (folder / ".claude").mkdir(parents=True)
    (folder / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    sh(folder, "init", "-q")
    with (folder / ".git" / "info" / "exclude").open("a", encoding="utf-8") as exclude:
        exclude.write(".claude/\n")
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert "git add failed" in str(failed.value)
    assert "Nothing was kept" in str(failed.value)
    assert sh(folder, "ls-files") == ""
    assert listing(folder) == [".claude", ".claude/settings.json"]


def test_a_failed_unstaging_is_named_with_its_reason(tmp_path, isolated, monkeypatch):
    refuse_commits(tmp_path, isolated)
    folder = tmp_path / "ideas"
    folder.mkdir()
    sh(folder, "init", "-q")
    real = home.git
    locked = "fatal: Unable to create '.git/index.lock': File exists."

    def git(folder, *args, timeout=home.CALL_SECONDS):
        if args[:1] == ("rm",):
            return subprocess.CompletedProcess(["git", *args], 128, "", locked + "\n")
        return real(folder, *args, timeout=timeout)

    monkeypatch.setattr(home, "git", git)
    with pytest.raises(home.HomeError) as failed:
        home.setup(folder)
    assert "Not taken away: the staging of .lifecycle.lock, .lifecycle.toml, AGENTS.md" in str(
        failed.value
    )
    assert f"in {folder / '.git'} ({locked}). Remove it and," in str(failed.value)
    assert "Nothing was kept" not in str(failed.value)


def test_github_pushes_a_main_ahead_of_origin(tmp_path, monkeypatch, local_home):
    remote = bare(tmp_path / "remote.git")
    install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    home.backup(local_home, "ideas")
    (local_home / "active" / "x").mkdir()
    (local_home / "active" / "x" / "IDEA.md").write_text("# Idea: x\n", encoding="utf-8")
    sh(local_home, "add", "active/x")
    sh(local_home, "commit", "-q", "-m", "Capture x")
    fake = install(monkeypatch)
    again = home.backup(local_home, "ideas")
    assert again.pushed and not again.created and fake.calls == []
    assert sh(remote, "rev-parse", "main") == sh(local_home, "rev-parse", "HEAD")


def test_github_from_an_idea_folder_backs_up_its_home(tmp_path, monkeypatch, capsys, local_home):
    remote = bare(tmp_path / "remote.git")
    install(monkeypatch, api_user=(0, "ada\n", ""), repo_create=(0, f"{remote}\n", ""))
    assert cli.main(["home", str(local_home / "active"), "--github", "ideas"]) == 0
    assert f"backed up to {remote}" in capsys.readouterr().out
    assert sh(remote, "rev-parse", "main") == sh(local_home, "rev-parse", "HEAD")


def test_check_names_the_repository_here_and_whether_it_holds_a_project(tmp_path, monkeypatch):
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)
    assert home.check(None)["here"] == {"repository": None, "project": False}
    clone = tmp_path / "clone"
    clone.mkdir()
    sh(clone, "init", "-q")
    sh(clone, "remote", "add", "origin", "https://example.com/someone/new.git")
    monkeypatch.chdir(clone)
    assert home.check(None)["here"] == {"repository": str(clone), "project": False}
    (clone / "AGENTS.md").write_text("# Agent instructions\n", encoding="utf-8")
    assert home.check(None)["here"]["project"] is True
    (clone / "AGENTS.md").unlink()
    sh(clone, "commit", "-q", "--allow-empty", "-m", "first")
    assert home.check(None)["here"]["project"] is True


def test_a_push_refused_for_credentials_names_gh_auth_setup_git(monkeypatch, local_home):
    sh(local_home, "remote", "add", "origin", "https://github.com/ada/ideas.git")
    real = home.git
    refused = "fatal: could not read Username for 'https://github.com': terminal prompts disabled"

    def git(folder, *args, timeout=home.CALL_SECONDS):
        if args[:1] == ("push",):
            return subprocess.CompletedProcess(["git", *args], 128, "", refused + "\n")
        return real(folder, *args, timeout=timeout)

    monkeypatch.setattr(home, "git", git)
    with pytest.raises(home.HomeError) as failed:
        home.backup(local_home, "ideas")
    assert "run `gh auth setup-git`" in str(failed.value)
    assert f"`lifecycle home {local_home} --github ideas` again" in str(failed.value)
