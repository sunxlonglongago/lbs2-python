"""``blog_Settings`` access.

The table stores one row per setting. ``set_type = 0`` keeps the value in the
numeric ``set_value0`` column, ``set_type = 1`` keeps it in the text
``set_value1`` column. Both the loader and the writer preserve that shape.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping

import db


def row_value(row: sqlite3.Row) -> Any:
    if int(row["set_type"] or 0) == 0:
        return int(row["set_value0"] or 0)
    return row["set_value1"] or ""


def load_all(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = db.query_all(
        conn,
        "SELECT set_name, set_type, set_value0, set_value1 FROM blog_Settings",
    )
    return {row["set_name"]: row_value(row) for row in rows}


def get(conn: sqlite3.Connection, name: str, default: Any = None) -> Any:
    row = db.query_one(
        conn,
        "SELECT set_type, set_value0, set_value1 FROM blog_Settings "
        "WHERE set_name = ?",
        (name,),
    )
    return default if row is None else row_value(row)


def get_int(conn: sqlite3.Connection, name: str, default: int = 0) -> int:
    value = get(conn, name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_flag(conn: sqlite3.Connection, name: str, default: bool = False) -> bool:
    return bool(get_int(conn, name, 1 if default else 0))


def get_text(conn: sqlite3.Connection, name: str, default: str = "") -> str:
    value = get(conn, name, default)
    return default if value is None else str(value)


def put(conn: sqlite3.Connection, name: str, value: Any) -> None:
    """Write one setting, keeping the original column layout."""
    if isinstance(value, bool) or isinstance(value, int):
        values = {"set_type": 0, "set_value0": int(value), "set_value1": ""}
    else:
        values = {"set_type": 1, "set_value0": 0, "set_value1": str(value)}
    # Never rewrite set_name: the ADMIN sources address rows by lower case
    # names ("blogtitle") while the stored names are camel case, and the
    # column is COLLATE NOCASE so the lookup still matches. Including the name
    # in the SET list would silently rename the row.
    existing = db.query_one(
        conn, "SELECT 1 FROM blog_Settings WHERE set_name = ?", (name,)
    )
    if existing:
        db.update(conn, "blog_Settings", values, "set_name = ?", (name,))
    else:
        db.insert(conn, "blog_Settings", {**values, "set_name": name})


def put_many(conn: sqlite3.Connection, values: Mapping[str, Any]) -> None:
    for name, value in values.items():
        put(conn, name, value)
    conn.commit()


def bump(conn: sqlite3.Connection, name: str, delta: int) -> None:
    """Increase a numeric setting, never dropping below zero."""
    conn.execute(
        "UPDATE blog_Settings SET set_value0 = MAX(set_value0 + ?, 0) "
        "WHERE set_name = ?",
        (delta, name),
    )


def counters(conn: sqlite3.Connection) -> dict[str, int]:
    names = (
        "counterArticle",
        "counterComment",
        "counterTrackback",
        "counterUser",
        "counterVisitor",
    )
    return {name: get_int(conn, name) for name in names}
