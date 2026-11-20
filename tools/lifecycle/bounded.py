"""A command cut off at its timeout together with everything it started.

``subprocess.run(timeout=)`` kills only its direct child. A child that starts others
(Git for Windows' ``git.exe`` launcher starts the real git, which starts a remote
helper) leaves them running, and on Windows ``run`` then waits for every holder of the
output pipe, so a hung helper holds the call for as long as it hangs. Here the child
starts in a group that is killed whole: a job object on Windows, a process group of its
own on POSIX, in the caller's session so it keeps the terminal. Its output goes to a
file rather than a pipe, so a process that escapes the group cannot hold the call either.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import tempfile
from collections.abc import Callable, Iterator

_WINDOWS = os.name == "nt"

if _WINDOWS:
    import ctypes
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _kernel32.TerminateJobObject.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _PROCESS_TERMINATE = 0x0001
    _PROCESS_SET_QUOTA = 0x0100


def run(
    args: list[str], *, timeout: float, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str] | None:
    """``args`` run to its end, with its stdout as text, or None once it outlives ``timeout``
    seconds. Stdin and stderr are the null device; raises OSError when ``args`` cannot start.

    However the wait ends but by the child's own exit (the timeout, Ctrl+C, any exception),
    the child and everything it started are killed before the call returns or raises.
    """
    with tempfile.TemporaryFile() as out:
        child = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.DEVNULL,
            env=env,
            **({} if _WINDOWS else {"process_group": 0}),
        )
        with _group(child) as kill_group:
            try:
                code = child.wait(timeout)
            except subprocess.TimeoutExpired:
                return None
            finally:
                if child.returncode is None:
                    if kill_group:
                        kill_group()
                    child.kill()
                    child.wait()
        out.seek(0)
        return subprocess.CompletedProcess(args, code, out.read().decode("utf-8", "replace"))


@contextlib.contextmanager
def _group(child: subprocess.Popen) -> Iterator[Callable[[], object] | None]:
    """How to kill ``child`` and everything it starts, or None where no group could be made
    (Windows refused the job); the caller then kills the child alone."""
    if not _WINDOWS:
        yield lambda: _kill_process_group(child.pid)
        return
    job = _job_holding(child)
    try:
        yield (lambda: _kernel32.TerminateJobObject(job, 1)) if job else None
    finally:
        if job:
            _kernel32.CloseHandle(job)


def _kill_process_group(pgid: int) -> None:
    with contextlib.suppress(OSError):
        os.killpg(pgid, signal.SIGKILL)


def _job_holding(child: subprocess.Popen) -> int | None:
    """A new job object with ``child`` in it, which every process ``child`` starts joins.

    ``child`` runs from its start, so a process it starts before it joins (it has barely
    loaded by then) escapes the job; only the output file then keeps the call bounded.
    """
    job = _kernel32.CreateJobObjectW(None, None)
    if not job:
        return None
    process = _kernel32.OpenProcess(_PROCESS_TERMINATE | _PROCESS_SET_QUOTA, False, child.pid)
    joined = bool(process) and bool(_kernel32.AssignProcessToJobObject(job, process))
    if process:
        _kernel32.CloseHandle(process)
    if joined:
        return job
    _kernel32.CloseHandle(job)
    return None
