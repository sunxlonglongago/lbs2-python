#!/usr/bin/env python3
"""Full business API end-to-end tests.

Creates a throw away data directory (or copies an existing one), imports the
original Access databases when ``access_parser`` is available, seeds the demo
rows and runs every scenario against the Flask test client.

Usage::

    python3 server/tests/api_full_e2e.py
    python3 server/tests/api_full_e2e.py --data-dir /path/to/existing/data
    python3 server/tests/api_full_e2e.py --only articles --only comments
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SERVER_SRC = ROOT_DIR / "server" / "src"
TESTS_DIR = ROOT_DIR / "server" / "tests"
E2E_DIR = TESTS_DIR / "api_e2e"
CASES_PATH = E2E_DIR / "CASES.md"


def build_data_dir(target: Path, source: "Path | None") -> None:
    target.mkdir(parents=True, exist_ok=True)
    if source is not None:
        if not source.is_dir():
            sys.exit(f"data directory does not exist: {source}")
        shutil.copytree(source, target, dirs_exist_ok=True)
        return
    importer = SERVER_SRC / "tools" / "import_access.py"
    result = subprocess.run(
        [sys.executable, str(importer), "--data", str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("skipping the Access import (needs access_parser):", result.stderr.strip()[-120:])
    seed = SERVER_SRC / "tools" / "seed_demo.py"
    subprocess.run([sys.executable, str(seed), "--data", str(target)], check=True)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default=os.environ.get("E2E_DATA_DIR") or os.environ.get("DATA_DIR"),
        help="existing data directory; when given it is copied to a temporary directory first, the original is never touched",
    )
    parser.add_argument(
        "--only", action="append", default=None,
        help="run only the given scenario; may be repeated",
    )
    parser.add_argument(
        "--keep", action="store_true", help="keep the temporary data directory and print its path",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source = Path(args.data_dir).expanduser().resolve() if args.data_dir else None
    temp_dir = Path(tempfile.mkdtemp(prefix="lbs-e2e-"))
    data_dir = temp_dir / "data"
    print(f"temporary data directory: {data_dir}" + (f" (copied from {source}）" if source else ""))
    build_data_dir(data_dir, source)

    # app.py parses --data while it is imported, so set the arguments first.
    sys.argv = ["api_full_e2e", "--data", str(data_dir)]
    sys.path.insert(0, str(SERVER_SRC))
    sys.path.insert(0, str(E2E_DIR))
    import app as app_module  # noqa: E402
    import runner  # noqa: E402

    app_module.app.config["TESTING"] = True
    try:
        return runner.run(
            app_module, data_dir, only=args.only, cases_path=CASES_PATH
        )
    finally:
        if args.keep:
            print(f"keeping data directory: {data_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
