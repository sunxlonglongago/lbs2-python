#!/usr/bin/env python3
"""Write docs/openapi.json from openapi_spec.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openapi_spec  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
DEFAULT_OUTPUT = ROOT_DIR / "docs" / "openapi.json"


def write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(openapi_spec.build(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    target = write(Path(args.output))
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
