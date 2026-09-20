#!/usr/bin/env python3
"""Import the original Access databases into the SQLite runtime database.

Usage::

    python3 server/src/tools/import_access.py --data dev-data

``access_parser`` (``python3 -m pip install access_parser``) is only needed for
this offline import step; the server itself never reads Access files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import access_reference  # noqa: E402
import config  # noqa: E402
import db  # noqa: E402
import schema  # noqa: E402

# Directory holding the original Access files; point --blog/--gbook or LBS_SOURCE_DATA at your copy.
DEFAULT_SOURCE_ROOT = Path(
    os.environ.get("LBS_SOURCE_DATA", "~/lbs/data")
).expanduser()


def load_access_parser():
    try:
        from access_parser import AccessParser
    except ImportError:  # pragma: no cover - offline tooling only
        sys.exit(
            "access_parser is required for the import step:\n"
            "    python3 -m pip install access_parser"
        )
    return AccessParser


def normalize(value):
    """Convert a value read from Access into something SQLite accepts."""
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, dt.date):
        return value.strftime("%Y-%m-%d 00:00:00")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def read_table(parser, table: str) -> dict[str, list]:
    data = parser.parse_table(table)
    if not data:
        return {}
    return {name: list(values) for name, values in data.items()}


def import_table(conn, parser, table: str, *, clear: bool) -> int:
    data = read_table(parser, table)
    columns = [name for name in schema.column_names(table) if name in data]
    if not columns:
        return 0
    row_count = len(data[columns[0]])
    if clear:
        conn.execute(f"DELETE FROM {table}")
    placeholders = ", ".join("?" for _ in columns)
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )
    rows = [
        tuple(normalize(data[column][index]) for column in columns)
        for index in range(row_count)
    ]
    if rows:
        conn.executemany(sql, rows)
    return len(rows)


def import_file(conn, parser, path: Path, *, clear: bool) -> dict[str, int]:
    tables = set(parser.catalog) & set(access_reference.ACCESS_TABLES)
    counts: dict[str, int] = {}
    for table in sorted(tables):
        counts[table] = import_table(conn, parser, table, clear=clear)
    return counts


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="runtime data directory")
    parser.add_argument(
        "--blog",
        default=str(DEFAULT_SOURCE_ROOT / "blog.mdb"),
        help="path to the original blog.mdb (defaults to $LBS_SOURCE_DATA/blog.mdb)",
    )
    parser.add_argument(
        "--gbook",
        default=str(DEFAULT_SOURCE_ROOT / "gbook.mdb"),
        help="path to the original gbook.mdb (defaults to $LBS_SOURCE_DATA/gbook.mdb)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="append instead of replacing the existing rows",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    AccessParser = load_access_parser()
    config.set_data_dir(args.data)
    target = config.db_path()

    conn = db.connect()
    db.ensure_schema(conn)

    totals: dict[str, int] = {}
    for source in (Path(args.blog), Path(args.gbook)):
        if not source.is_file():
            print(
                f"skip: {source} not found "
                " (point --blog/--gbook or LBS_SOURCE_DATA at your copy of the original)"
            )
            continue
        parser = AccessParser(str(source))
        counts = import_file(conn, parser, source, clear=not args.no_clear)
        if counts:
            print(f"{source.name}:")
            for table, count in counts.items():
                print(f"  {table:22} {count} rows")
        totals.update(counts)

    conn.commit()
    conn.close()
    print(f"\nimported {len(totals)} tables into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
