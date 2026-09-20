"""File upload (upload.asp + class/upload.asp).

The ASP version parses the multipart body by hand; here the WSGI layer does it
and this module applies the same rules: group upload right, size limit,
extension whitelist, ``YYMM`` sub folder and a ``DD_hhiiss_`` prefixed name.
"""

from __future__ import annotations

import datetime as dt
import re
import sqlite3
from pathlib import Path

import admin
import settings as settings_module
import utils

FILENAME_RE = re.compile(r"[^_\.a-zA-Z\d]")

IMAGE_EXT = ("gif", "jpg", "bmp", "png", "tif")
WMP_EXT = ("wma", "mp3", "avi", "wmv", "asf")
RM_EXT = ("ra", "rm", "rmvb")


def upload_types(conn: sqlite3.Connection) -> list[str]:
    raw = settings_module.get_text(conn, "uploadTypes", "")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def clean_file_name(name: str) -> str:
    """Port of ``cleanFileName``."""
    cleaned = FILENAME_RE.sub("", name or "")
    return re.sub(r"^[/\.]+", "", cleaned)


def is_valid_type(conn: sqlite3.Connection, extension: str) -> bool:
    return extension.lower() in upload_types(conn)


def store(conn: sqlite3.Connection, storage) -> "tuple[dict | None, str | None]":
    """Save an uploaded file; returns ``(info, error)``."""
    filename = storage.filename or ""
    if not filename:
        return None, "upload"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not is_valid_type(conn, extension):
        return None, "type"

    data = storage.read()
    if not data:
        return None, "upload"
    limit = settings_module.get_int(conn, "uploadSize", 40000)
    if len(data) > limit:
        return None, "size"

    now = dt.datetime.now()
    folder_name = now.strftime("%y%m")
    folder = admin.upload_dir() / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    base = clean_file_name(Path(filename).name)
    if not base:
        base = "upload"
    new_name = now.strftime("%d_%H%M%S") + "_" + base
    new_name = new_name[:120]
    target = folder / f"{new_name}.{extension}"
    try:
        target.write_bytes(data)
    except OSError:
        return None, "write"

    prefix = settings_module.get_text(conn, "uploadPath", "uploads/")
    relative = f"{prefix}{folder_name}/{target.name}"
    return {
        "path": relative,
        "url": "/" + relative.lstrip("/"),
        "size": len(data),
        "extension": extension,
        "ubb": ubb_snippet(extension, relative),
    }, None


def ubb_snippet(extension: str, path: str) -> str:
    """Port of ``outputUploadDone``: the tag inserted into the message box."""
    if extension in IMAGE_EXT:
        return f"[img]{path}[/img]"
    if extension in WMP_EXT:
        return f"[wmp]{path}[/wmp]"
    if extension in RM_EXT:
        return f"[rm]{path}[/rm]"
    if extension == "swf":
        return f"[swf]{path}[/swf]"
    if extension == "mov":
        return f"[qt]{path}[/qt]"
    return f"[file={path}]Click Here To Download[/file]"
