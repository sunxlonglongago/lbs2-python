"""Runtime configuration shared by the server and the offline tooling."""

from __future__ import annotations

import os
from pathlib import Path

from typing import Union

BASE_DIR = Path(__file__).resolve().parent

# Name of the SQLite file inside the runtime data directory.
DB_FILENAME = "lbs.sqlite3"

_DATA_DIR: "Path | None" = None

PathLike = Union[str, os.PathLike]


def set_data_dir(path: PathLike) -> Path:
    """Remember the runtime data directory (``--data <dir>``)."""
    global _DATA_DIR
    _DATA_DIR = Path(path).expanduser().resolve()
    return _DATA_DIR


def require_data_dir() -> Path:
    if _DATA_DIR is None:
        raise RuntimeError("Data directory is not set; start with --data <dir>.")
    return _DATA_DIR


def resolve_data_dir(path: "PathLike | None" = None) -> Path:
    """Return ``path`` (or the configured data directory) as an absolute path."""
    if path is not None:
        return Path(path).expanduser().resolve()
    return require_data_dir()


def db_path(data_dir: "PathLike | None" = None) -> Path:
    return resolve_data_dir(data_dir) / DB_FILENAME


def ensure_data_dir(data_dir: "PathLike | None" = None) -> Path:
    base = resolve_data_dir(data_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base
