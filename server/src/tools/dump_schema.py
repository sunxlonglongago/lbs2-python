#!/usr/bin/env python3
"""Verify the SQLite schema against the Access reference.

Compares table names, column names, column order and primary keys of the
SQLite database with ``tools/access_reference.py`` (extracted from the
original ``.mdb`` files) and reports any drift.

Usage::

    python3 server/src/tools/dump_schema.py --data dev-data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import access_reference  # noqa: E402
import config  # noqa: E402
import db  # noqa: E402
import schema  # noqa: E402


def sqlite_columns(conn, table: str) -> list[tuple[str, str, int]]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [(row["name"], row["type"], row["pk"]) for row in rows]


def has_autoincrement(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return bool(row and row["sql"] and "AUTOINCREMENT" in row["sql"].upper())


def compare(conn) -> list[str]:
    problems: list[str] = []
    expected_tables = set(access_reference.ACCESS_TABLES)
    actual_tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        if not row["name"].startswith("sqlite_")
    }

    for table in sorted(expected_tables - actual_tables):
        problems.append(f"missing table: {table}")
    for table in sorted(actual_tables - expected_tables):
        problems.append(f"unexpected table: {table}")

    for table in sorted(expected_tables & actual_tables):
        expected = access_reference.ACCESS_TABLES[table]
        actual = sqlite_columns(conn, table)

        expected_names = [column[0] for column in expected]
        actual_names = [column[0] for column in actual]
        if expected_names != actual_names:
            problems.append(
                f"{table}: column mismatch\n"
                f"    access: {expected_names}\n"
                f"    sqlite: {actual_names}"
            )
            continue

        for name, access_type, _length, autonumber, primary_key in expected:
            want_type = access_reference.SQLITE_TYPE[access_type]
            found = next(column for column in actual if column[0] == name)
            if found[1].upper() != want_type:
                problems.append(
                    f"{table}.{name}: type {found[1]} != {want_type} "
                    f"(Access {access_type})"
                )
            if primary_key and not found[2]:
                problems.append(f"{table}.{name}: missing primary key")
            if autonumber and not has_autoincrement(conn, table):
                problems.append(f"{table}.{name}: missing AUTOINCREMENT")
    return problems


def report(conn) -> None:
    expected_tables = sorted(access_reference.ACCESS_TABLES)
    for table in expected_tables:
        expected = access_reference.ACCESS_TABLES[table]
        count = db.scalar(conn, f"SELECT COUNT(*) FROM {table}")
        print(f"\n{table}  ({count} rows, {len(expected)} columns)")
        for name, access_type, length, autonumber, primary_key in expected:
            marks = []
            if primary_key:
                marks.append("PK")
            if autonumber:
                marks.append("AUTOINCREMENT")
            suffix = f"  [{' '.join(marks)}]" if marks else ""
            size = f"({length})" if length else ""
            print(
                f"  {name:20} {access_type}{size:6} -> "
                f"{access_reference.SQLITE_TYPE[access_type]}{suffix}"
            )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="runtime data directory")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only print mismatches",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config.set_data_dir(args.data)
    conn = db.connect()
    db.ensure_schema(conn)

    if not args.quiet:
        report(conn)

    problems = compare(conn)
    conn.close()

    if problems:
        print("\nschema mismatches:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nschema matches the Access reference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
