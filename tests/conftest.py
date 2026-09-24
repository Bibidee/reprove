"""Test-runner compatibility for the GenLayer direct harness on Windows.

genlayer-test 0.29.2 replaces fd 0 with a temporary file and immediately
unlinks that file. Windows keeps the descriptor open, so unlink raises
PermissionError even though the harness is otherwise ready to run. Leaving
the temporary file until process cleanup preserves the harness semantics.
"""

import os
import tempfile


if os.name == "nt":
    _unlink = os.unlink

    def _unlink_windows_safe(path, *args, **kwargs):
        try:
            return _unlink(path, *args, **kwargs)
        except PermissionError:
            temp_root = os.path.abspath(tempfile.gettempdir()).lower()
            candidate = os.path.abspath(os.fspath(path)).lower()
            if candidate.startswith(temp_root + os.sep):
                return None
            raise

    os.unlink = _unlink_windows_safe
