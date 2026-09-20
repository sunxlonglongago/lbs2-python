"""SQLite access layer.

Small wrappers around :mod:`sqlite3`; the original ASP code used an ADODB
connection wrapper (``class/dbconn.asp``) with ``query``/``insert``/``update``
helpers, so the same shape is kept here.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable, Mapping, Sequence

import config
import schema

Rows = Sequence[Any]


def connect(data_dir: "str | None" = None) -> sqlite3.Connection:
    """Open the database, creating the data directory when needed."""
    target = config.db_path(data_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    schema.ensure_schema(conn)
    conn.commit()


@contextmanager
def connection(data_dir: "str | None" = None):
    """Open a connection, commit on success and always close it."""
    conn = connect(data_dir)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(conn: sqlite3.Connection, sql: str, params: Rows = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def query_one(conn: sqlite3.Connection, sql: str, params: Rows = ()) -> "sqlite3.Row | None":
    return conn.execute(sql, params).fetchone()


def scalar(conn: sqlite3.Connection, sql: str, params: Rows = ()) -> Any:
    row = query_one(conn, sql, params)
    return row[0] if row is not None else None


def execute(conn: sqlite3.Connection, sql: str, params: Rows = ()) -> int:
    """Run a write statement and return the number of affected rows."""
    return conn.execute(sql, params).rowcount


def insert(conn: sqlite3.Connection, table: str, values: Mapping[str, Any]) -> int:
    """Insert one row, returning the new rowid."""
    columns = list(values)
    placeholders = ", ".join("?" for _ in columns)
    sql = f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders})'
    cursor = conn.execute(sql, [values[column] for column in columns])
    return int(cursor.lastrowid or 0)


def update(
    conn: sqlite3.Connection,
    table: str,
    values: Mapping[str, Any],
    where: str,
    params: Rows = (),
) -> int:
    assignments = ", ".join(f"{column} = ?" for column in values)
    sql = f"UPDATE {table} SET {assignments} WHERE {where}"
    return conn.execute(sql, [*values.values(), *params]).rowcount


def upsert(conn: sqlite3.Connection, table: str, values: Mapping[str, Any], key: str) -> None:
    """Insert a row, or update it when the ``key`` column already exists."""
    if query_one(conn, f"SELECT 1 FROM {table} WHERE {key} = ?", (values[key],)):
        update(conn, table, values, f"{key} = ?", (values[key],))
    else:
        insert(conn, table, values)


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
