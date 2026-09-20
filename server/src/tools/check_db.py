#!/usr/bin/env python3
"""Check a database against the schema this code expects.

Compares the live database with ``schema.py``: missing or extra tables, column
names and order, SQLite types, primary keys, AUTOINCREMENT and indexes. Run it
after a deploy or an upgrade to confirm the data directory matches the code.

Usage::

    python3 server/src/tools/check_db.py --data dev-data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import db  # noqa: E402
import schema  # noqa: E402


def sqlite_columns(conn, table: str) -> list[tuple[str, str, int]]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [(row["name"], row["type"], row["pk"]) for row in rows]


def table_sql(conn, table: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return (row["sql"] or "") if row else ""


def index_names(conn, table: str) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = ? "
        "AND name NOT LIKE 'sqlite_%'",
        (table,),
    ).fetchall()
    return {row["name"] for row in rows}


def expected_indexes(table: str) -> set[str]:
    return {
        statement.split(" IF NOT EXISTS ")[1].split(" ON ")[0]
        for statement in schema.INDEXES
        if f" ON {table}(" in statement
    }


def compare(conn) -> list[str]:
    problems: list[str] = []
    expected_tables = set(schema.TABLES)
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
        expected = schema.columns(table)
        actual = sqlite_columns(conn, table)

        expected_names = [column[0] for column in expected]
        actual_names = [column[0] for column in actual]
        if expected_names != actual_names:
            problems.append(
                f"{table}: columns differ\n"
                f"    expected: {expected_names}\n"
                f"    actual:   {actual_names}"
            )
            continue

        for name, declaration, declared in expected:
            # "TEXT(255)" -> TEXT, "LONG AUTOINCREMENT" -> LONG
            base = declared.split("(", 1)[0].split()[0]
            want = schema.DECLARED_TO_SQLITE[base]
            found = next(column for column in actual if column[0] == name)
            if found[1].upper() != want:
                problems.append(
                    f"{table}.{name}: sqlite type {found[1]} != {want} "
                    f"(declared {declared})"
                )
            if "PRIMARY KEY" in declaration and not found[2]:
                problems.append(f"{table}.{name}: missing primary key")

        needs_autoincrement = any(
            "AUTOINCREMENT" in declaration for _n, declaration, _d in expected
        )
        if needs_autoincrement and "AUTOINCREMENT" not in table_sql(conn, table).upper():
            problems.append(f"{table}: missing AUTOINCREMENT")

        missing_indexes = expected_indexes(table) - index_names(conn, table)
        if missing_indexes:
            problems.append(f"{table}: missing indexes {sorted(missing_indexes)}")

    return problems


def report(conn) -> None:
    for table in schema.TABLES:
        rows = int(db.scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0)
        columns = len(schema.columns(table))
        print(f"\n{table}  ({rows} rows, {columns} columns)")
        for name, declaration, declared in schema.columns(table):
            print(f"  {name:20} {declared:18} -> {declaration}")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="runtime data directory")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only print problems",
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
        print("\nschema problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nschema matches the code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
