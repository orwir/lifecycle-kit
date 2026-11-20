import json
import os
import subprocess
import time

from lifecycle import latest


def boom():
    raise AssertionError("asked the remote")


def write_cache(checked, value):
    latest.cache_file().parent.mkdir(parents=True, exist_ok=True)
    latest.cache_file().write_text(json.dumps({"checked": checked, "latest": value}))


def test_a_fresh_cache_answers_without_asking(monkeypatch):
    write_cache(time.time(), "0.3.0")
    monkeypatch.setattr(latest, "_ask", boom)
    assert latest.latest_release() == "0.3.0"


def test_a_stale_cache_asks_the_remote_for_its_newest_tag(tmp_path, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    kit = tmp_path / "kit"
    kit.mkdir()
    subprocess.run(["git", "-C", str(kit), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    for tag in ("v0.1.0", "v0.10.0", "v0.9.0", "not-a-release"):
        subprocess.run(["git", "-C", str(kit), "tag", tag], check=True)
    monkeypatch.setenv("LIFECYCLE_KIT_REMOTE", str(kit))
    write_cache(time.time() - 2 * latest.DAY_SECONDS, "0.1.0")
    assert latest.latest_release() == "0.10.0"
    assert json.loads(latest.cache_file().read_text())["latest"] == "0.10.0"


def test_a_failed_check_keeps_the_last_answer_and_waits_a_day(monkeypatch):
    now = time.time()
    write_cache(now - 2 * latest.DAY_SECONDS, "0.2.0")
    assert latest.latest_release(now) == "0.2.0"
    monkeypatch.setattr(latest, "_ask", boom)
    assert latest.latest_release(now + 60) == "0.2.0"


def test_no_cache_and_no_remote_is_silence():
    assert latest.latest_release() is None


def test_a_hung_remote_is_cut_off_and_waits_a_day(tmp_path, monkeypatch):
    helpers = tmp_path / "helpers"
    helpers.mkdir()
    hang = helpers / "git-remote-hang"
    hang.write_text("#!/bin/sh\nsleep 20\n", encoding="utf-8", newline="\n")
    hang.chmod(0o755)
    monkeypatch.setenv("PATH", f"{helpers}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LIFECYCLE_KIT_REMOTE", "hang::nowhere")
    monkeypatch.setattr(latest, "TIMEOUT_SECONDS", 1)
    started = time.monotonic()
    assert latest.latest_release() is None
    assert time.monotonic() - started < 8
    monkeypatch.setattr(latest, "_ask", boom)
    assert latest.latest_release() is None


def test_the_day_is_recorded_before_the_remote_is_asked(monkeypatch):
    now = time.time()
    seen = {}

    def ask():
        seen["checked"] = json.loads(latest.cache_file().read_text())["checked"]
        return None

    monkeypatch.setattr(latest, "_ask", ask)
    latest.latest_release(now)
    assert seen["checked"] == now
