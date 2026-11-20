import contextlib
import os
import signal
import subprocess
import sys
import time

import pytest
from lifecycle import bounded

# A grandchild that writes its pid, then appends a byte to a file every tenth of a second
# for about twenty seconds.
BEAT = """\
import os, sys, time
open(sys.argv[2], "w").write(str(os.getpid()))
for _ in range(200):
    with open(sys.argv[1], "a") as f:
        f.write("x")
    time.sleep(0.1)
"""
# A child that starts that grandchild holding its own stdout, then hangs.
FAMILY = """\
import subprocess, sys, time
subprocess.Popen(
    [sys.executable, "-c", sys.argv[1], *sys.argv[2:]],
    stdin=subprocess.DEVNULL, stdout=1, stderr=subprocess.DEVNULL,
)
time.sleep(20)
"""


def run_family(tmp_path, timeout):
    """The family run with ``timeout``: the result and the seconds the call took."""
    started = time.monotonic()
    result = bounded.run(
        [sys.executable, "-c", FAMILY, BEAT, str(tmp_path / "beat"), str(tmp_path / "pid")],
        timeout=timeout,
    )
    return result, time.monotonic() - started


def beats(tmp_path):
    beat = tmp_path / "beat"
    return beat.stat().st_size if beat.exists() else 0


def still_beating(tmp_path):
    time.sleep(0.3)
    before = beats(tmp_path)
    time.sleep(1)
    return beats(tmp_path) > before


def test_a_command_that_outlives_its_timeout_is_cut_off_with_all_it_started(tmp_path):
    result, took = run_family(tmp_path, timeout=2)
    assert result is None
    assert took < 8
    assert beats(tmp_path) > 0, "the grandchild never started, so nothing was tested"
    assert not still_beating(tmp_path)


def test_an_interrupted_wait_takes_all_it_started_with_it(tmp_path, monkeypatch):
    real_wait = subprocess.Popen.wait

    def interrupted(self, timeout=None):
        if timeout is None:
            return real_wait(self)
        time.sleep(2)
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess.Popen, "wait", interrupted)
    started = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        run_family(tmp_path, timeout=30)
    assert time.monotonic() - started < 8
    assert beats(tmp_path) > 0, "the grandchild never started, so nothing was tested"
    assert not still_beating(tmp_path)


def test_a_command_that_finishes_gives_its_code_and_output():
    done = bounded.run([sys.executable, "-c", "print('v1'); raise SystemExit(3)"], timeout=10)
    assert (done.returncode, done.stdout.split()) == (3, ["v1"])


def test_with_no_group_the_call_is_still_cut_off_in_time(tmp_path, monkeypatch):
    monkeypatch.setattr(bounded, "_group", lambda child: contextlib.nullcontext())
    try:
        result, took = run_family(tmp_path, timeout=2)
        assert result is None
        assert took < 8
    finally:
        if still_beating(tmp_path):
            os.kill(int((tmp_path / "pid").read_text()), signal.SIGTERM)
