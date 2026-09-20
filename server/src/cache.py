"""Process level cache.

``class/cache.asp`` kept the settings, categories, user groups, smilies, word
filters and sidebar lists in ASP ``Application`` scope. The Flask port keeps the
same data in memory with a short TTL; writes invalidate the affected entries.

Loaders open their own short lived connection: the cached value outlives the
request that filled it, so it must never hold on to a caller's connection.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any, Callable

import db

# Settings and categories change rarely; a short TTL keeps the sidebar fresh
# without hitting SQLite on every request.
DEFAULT_TTL = 30.0

_lock = threading.RLock()
_store: dict[str, tuple[float, Any]] = {}


def _cached(key: str, loader: Callable[[], Any], ttl: float = DEFAULT_TTL) -> Any:
    now = time.monotonic()
    with _lock:
        entry = _store.get(key)
        if entry and now - entry[0] < ttl:
            return entry[1]
    value = loader()
    with _lock:
        _store[key] = (now, value)
    return value


def _fetch(sql: str, params: "tuple | list" = ()) -> list[sqlite3.Row]:
    """Run a query on a private connection, independent of any request."""
    with db.connection() as conn:
        return db.query_all(conn, sql, params)


def invalidate(key: "str | None" = None) -> None:
    with _lock:
        if key is None:
            _store.clear()
        else:
            _store.pop(key, None)


def settings(conn: sqlite3.Connection) -> dict[str, Any]:
    import settings as settings_module

    def load() -> dict[str, Any]:
        with db.connection() as private:
            return settings_module.load_all(private)

    return _cached("settings", load)


def setting(conn: sqlite3.Connection, name: str, default: Any = None) -> Any:
    return settings(conn).get(name, default)


def categories(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    def load() -> list[dict[str, Any]]:
        rows = _fetch(
            "SELECT cat_id, cat_name, cat_order, cat_articleCount, "
            "cat_hidden, cat_locked FROM blog_Category ORDER BY cat_order",
        )
        return [
            {
                "id": int(row["cat_id"]),
                "name": row["cat_name"] or "",
                "order": int(row["cat_order"] or 0),
                "article_count": int(row["cat_articleCount"] or 0),
                "hidden": bool(row["cat_hidden"]),
                "locked": bool(row["cat_locked"]),
            }
            for row in rows
        ]

    return _cached("categories", load)


def groups(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    def load() -> dict[int, dict[str, Any]]:
        rows = _fetch("SELECT group_id, group_name, group_rights FROM blog_UserGroup")
        return {
            int(row["group_id"]): {
                "id": int(row["group_id"]),
                "name": row["group_name"] or "",
                "rights": row["group_rights"] or "",
            }
            for row in rows
        }

    return _cached("groups", load)


def smilies(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    def load() -> list[dict[str, Any]]:
        rows = _fetch("SELECT sm_id, sm_code, sm_image FROM blog_Smilies ORDER BY sm_id")
        return [
            {
                "id": int(row["sm_id"]),
                "code": row["sm_code"] or "",
                "image": row["sm_image"] or "",
            }
            for row in rows
        ]

    return _cached("smilies", load)


def word_filters(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    def load() -> list[dict[str, Any]]:
        rows = _fetch(
            "SELECT wf_id, wf_mode, wf_text, wf_replace, wf_regExp "
            "FROM blog_WordFilter ORDER BY wf_id",
        )
        return [
            {
                "id": int(row["wf_id"]),
                "mode": int(row["wf_mode"] or 0),
                "text": row["wf_text"] or "",
                "replace": row["wf_replace"] or "",
                "regexp": bool(row["wf_regExp"]),
            }
            for row in rows
        ]

    return _cached("wordfilter", load)


def get_category(categories: list[dict[str, Any]], category_id: int) -> dict[str, Any]:
    """``lbsCache.getCategoryByID``: unknown ids fall back to a hidden category."""
    for category in categories:
        if category["id"] == category_id:
            return category
    return {
        "id": 0,
        "name": "",
        "order": 0,
        "article_count": 0,
        "hidden": True,
        "locked": True,
    }
