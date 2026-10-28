"""Reentrant file locks shared by processes and Windows sessions."""
from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
import threading
import time

_registry_guard = threading.Lock()
_locks: dict[str, tuple[threading.RLock, threading.local]] = {}


@contextmanager
def file_lock(path: Path, *, timeout: float = 30):
    path = path.resolve()
    identity = os.path.normcase(str(path))
    with _registry_guard:
        lock, ownership = _locks.setdefault(identity, (threading.RLock(), threading.local()))
    deadline = time.monotonic() + timeout
    if not lock.acquire(timeout=max(0, timeout)):
        raise TimeoutError('Another planner operation is still using the saved data. Try again.')
    try:
        if getattr(ownership, 'active', False):
            yield
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the file: unlinking lets another process lock a different inode.
        with path.open('a+b', buffering=0) as handle:
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b'\0')
            while True:
                handle.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('Another planner operation is still using the saved data. Try again.') from None
                    time.sleep(min(0.05, remaining))
            ownership.active = True
            try:
                yield
            finally:
                ownership.active = False
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        lock.release()
