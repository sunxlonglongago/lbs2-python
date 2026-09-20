"""Process wide site state.

``_common.asp`` keeps the "site closed" switch in ASP ``Application`` scope;
this is the same idea for a single process deployment.
"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_closed = False


def site_closed() -> bool:
    with _lock:
        return _closed


def set_site_closed(value: bool) -> None:
    global _closed
    with _lock:
        _closed = bool(value)
