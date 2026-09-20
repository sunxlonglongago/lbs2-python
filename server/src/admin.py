"""Admin backend, ported from ``source/src_admin.asp``.

The ASP version posts bulk edits as comma separated strings (``id``, ``name``,
``order`` ...). The JSON API takes real lists instead; the rules applied to each
row are the ones from ``updateCategories`` / ``updateUserGroup`` / ...
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path
from typing import Any

import config
import db
import lang
import settings as settings_module
import utils

# (setting name, kind, minimum, maximum). Bounds are exclusive, exactly like
# genIntUpdate() in src_admin.asp.
SETTING_RULES: tuple[tuple[str, str, int | None, int | None], ...] = (
    ("blogtitle", "str", None, None),
    ("blogdescription", "str", None, None),
    ("baseurl", "str", None, None),
    ("logoimage", "str", None, None),
    ("blogwebmaster", "str", None, None),
    ("blogwebmasteremail", "str", None, None),
    ("bloglanguage", "str", None, None),
    ("defaultviewmode", "bool", None, None),
    ("articleperpagenormal", "int", 0, 21),
    ("articleperpagelist", "int", 19, 101),
    ("listentryperpage", "int", 9, 101),
    ("commentperpage", "int", -1, 51),
    ("commenttimeorder", "bool", None, None),
    ("showtrackbackwithcomment", "bool", None, None),
    ("showtrackbackposition", "int", -1, 3),
    ("recentarticlelist", "int", 2, 31),
    ("recentcommentlist", "int", 2, 31),
    ("enabledynamiccalendar", "bool", None, None),
    ("enablecontentautosplit", "bool", None, None),
    ("contentautosplitchars", "int", 99, 2001),
    ("enableregister", "bool", None, None),
    ("enablesecuritycode", "bool", None, None),
    ("enabletrackbackin", "bool", None, None),
    ("enabletrackbackout", "bool", None, None),
    ("enablecomment", "bool", None, None),
    ("maxcommentlength", "int", 99, 2001),
    ("enableguestbook", "bool", None, None),
    ("entryperpageguestbook", "int", 2, 31),
    ("stylesheet", "str", None, None),
    ("imagefolder", "str", None, None),
    ("smiliesfolder", "str", None, None),
    ("smiliesperrow", "int", 0, 31),
    ("minpostduration", "int", 0, 601),
    ("enablevisitorrecord", "bool", None, None),
    ("maxvisitorrecord", "int", 0, 301),
    ("enableupload", "bool", None, None),
    ("uploadsize", "int", 1023, 50000001),
    ("uploadpath", "str", None, None),
    ("uploadtypes", "str", None, None),
)


def _clean_path(value: str, *, trailing_slash: bool) -> str:
    text = value.replace("\\", "/")
    if trailing_slash:
        return text if text.endswith("/") else text + "/"
    return text[:-1] if text.endswith("/") else text


def update_settings(conn: sqlite3.Connection, payload: dict) -> list[str]:
    """Port of ``updateSettings``; returns the names actually written."""
    lowered = {str(key).lower(): value for key, value in payload.items()}
    written: list[str] = []
    for name, kind, minimum, maximum in SETTING_RULES:
        if name not in lowered:
            continue
        value = lowered[name]
        if kind == "bool":
            settings_module.put(conn, name, 1 if value else 0)
        elif kind == "int":
            number = utils.check_int(value)
            if not (minimum is not None and number <= minimum) and not (
                maximum is not None and number >= maximum
            ):
                settings_module.put(conn, name, number)
            else:
                continue
        else:
            text = utils.trim_text(str(value or ""))
            if not text:
                continue
            if name == "baseurl":
                text = _clean_path(text, trailing_slash=True)
            elif name == "uploadpath":
                text = _clean_path(text, trailing_slash=True)
            elif name in ("stylesheet", "imagefolder", "smiliesfolder", "logoimage"):
                text = _clean_path(text, trailing_slash=False)
            settings_module.put(conn, name, text)
        written.append(name)
    conn.commit()
    return written


def update_categories(conn: sqlite3.Connection, payload: dict) -> dict[str, Any]:
    """Port of the update / move / delete branches of ``updateCategories``."""
    action = str(payload.get("act") or "update")
    result: dict[str, Any] = {"action": action}

    if action == "update":
        conn.execute("UPDATE blog_Category SET cat_hidden = 0 WHERE cat_id > 0")
        hidden = [utils.check_int(value) for value in payload.get("hidden") or []]
        hidden = [value for value in hidden if value > 0]
        if hidden:
            conn.execute(
                f"UPDATE blog_Category SET cat_hidden = 1 "
                f"WHERE cat_id IN ({', '.join('?' for _ in hidden)})",
                hidden,
            )
        conn.execute("UPDATE blog_Category SET cat_locked = 0 WHERE cat_id > 0")
        locked = [utils.check_int(value) for value in payload.get("locked") or []]
        locked = [value for value in locked if value > 0]
        if locked:
            conn.execute(
                f"UPDATE blog_Category SET cat_locked = 1 "
                f"WHERE cat_id IN ({', '.join('?' for _ in locked)})",
                locked,
            )

        ids = payload.get("id") or []
        names = payload.get("name") or []
        orders = payload.get("order") or []
        written = 0
        for index, raw_id in enumerate(ids):
            category_id = utils.check_int(raw_id)
            name = utils.trim_text(names[index] if index < len(names) else "")
            order = utils.check_int(orders[index] if index < len(orders) else 0)
            if not 1 <= len(name) <= 50:
                continue
            if category_id == 0:
                db.insert(
                    conn,
                    "blog_Category",
                    {
                        "cat_name": name,
                        "cat_order": order,
                        "cat_articleCount": 0,
                        "cat_hidden": 1 if payload.get("newhidden") else 0,
                        "cat_locked": 1 if payload.get("newlocked") else 0,
                    },
                )
                written += 1
            elif category_id > 0:
                db.update(
                    conn, "blog_Category",
                    {"cat_name": name, "cat_order": order},
                    "cat_id = ?", (category_id,),
                )
                written += 1
        result["written"] = written
        conn.commit()
        return result

    if action == "move":
        selected = [utils.check_int(v) for v in payload.get("selected") or []]
        selected = [v for v in selected if v >= 1]
        target = utils.check_int(payload.get("target"))
        if not selected or target < 1:
            result["moved"] = 0
            return result
        placeholders = ", ".join("?" for _ in selected)
        conn.execute(
            f"UPDATE blog_Article SET log_catID = ? "
            f"WHERE log_catID IN ({placeholders})",
            [target, *selected],
        )
        conn.execute(
            f"UPDATE blog_Category SET cat_articleCount = 0 "
            f"WHERE cat_id IN ({placeholders})",
            selected,
        )
        count = db.scalar(
            conn, "SELECT COUNT(log_id) FROM blog_Article WHERE log_catID = ?", (target,)
        )
        conn.execute(
            "UPDATE blog_Category SET cat_articleCount = ? WHERE cat_id = ?",
            (int(count or 0), target),
        )
        conn.commit()
        result["moved"] = len(selected)
        return result

    if action == "delete":
        selected = [utils.check_int(v) for v in payload.get("selected") or []]
        selected = [v for v in selected if v >= 1]
        if not selected:
            result["deleted"] = 0
            return result
        placeholders = ", ".join("?" for _ in selected)
        conn.execute(
            f"DELETE FROM blog_Comment WHERE log_id IN "
            f"(SELECT log_id FROM blog_Article WHERE log_catID IN ({placeholders}))",
            selected,
        )
        conn.execute(
            f"DELETE FROM blog_Trackback WHERE log_id IN "
            f"(SELECT log_id FROM blog_Article WHERE log_catID IN ({placeholders}))",
            selected,
        )
        conn.execute(
            f"DELETE FROM blog_Article WHERE log_catID IN ({placeholders})", selected
        )
        conn.execute(
            f"DELETE FROM blog_Category WHERE cat_id IN ({placeholders})", selected
        )
        _resync_global(conn)
        conn.commit()
        result["deleted"] = len(selected)
        return result

    result["error"] = "invalid_parameter"
    return result


def update_groups(conn: sqlite3.Connection, payload: dict) -> dict[str, Any]:
    """Port of ``updateUserGroup``; the built in Admin group is skipped."""
    action = str(payload.get("act") or "update")
    if action == "delete":
        selected = [utils.check_int(v) for v in payload.get("selected") or []]
        selected = [v for v in selected if v >= 1 and v != 1]
        if selected:
            placeholders = ", ".join("?" for _ in selected)
            conn.execute(
                f"DELETE FROM blog_User WHERE user_groupID IN ({placeholders})",
                selected,
            )
            conn.execute(
                f"DELETE FROM blog_UserGroup WHERE group_id IN ({placeholders})",
                selected,
            )
            _resync_global(conn)
            conn.commit()
        return {"action": action, "deleted": len(selected)}

    ids = payload.get("id") or []
    names = payload.get("name") or []
    views = payload.get("view") or []
    posts = payload.get("post") or []
    edits = payload.get("edit") or []
    deletes = payload.get("delete") or []
    uploads = payload.get("upload") or []
    written = 0

    def level(values, index, low, high):
        if index >= len(values):
            return None
        value = utils.check_int(values[index])
        return value if low <= value <= high else None

    for index, raw_id in enumerate(ids):
        group_id = utils.check_int(raw_id)
        name = utils.trim_text(names[index] if index < len(names) else "")
        view = level(views, index, 0, 3)
        post = level(posts, index, 0, 2)
        edit = level(edits, index, 0, 2)
        delete = level(deletes, index, 0, 2)
        upload = level(uploads, index, 0, 1)
        if group_id == 1:
            continue
        if not 1 <= len(name) <= 50:
            continue
        if None in (view, post, edit, delete, upload):
            continue
        values = {
            "group_name": name,
            "group_rights": f"{view}{post}{edit}{delete}{upload}",
        }
        if group_id == 0:
            db.insert(conn, "blog_UserGroup", values)
            written += 1
        elif group_id > 0:
            db.update(
                conn, "blog_UserGroup", values, "group_id = ?", (group_id,)
            )
            written += 1
    conn.commit()
    return {"action": action, "written": written}


def update_smilies(conn: sqlite3.Connection, payload: dict) -> dict[str, Any]:
    action = str(payload.get("act") or "update")
    if action == "delete":
        selected = [utils.check_int(v) for v in payload.get("selected") or []]
        selected = [v for v in selected if v >= 1]
        if selected:
            placeholders = ", ".join("?" for _ in selected)
            conn.execute(
                f"DELETE FROM blog_Smilies WHERE sm_id IN ({placeholders})", selected
            )
            conn.commit()
        return {"action": action, "deleted": len(selected)}

    ids = payload.get("id") or []
    codes = payload.get("code") or []
    images = payload.get("image") or []
    written = 0
    for index, raw_id in enumerate(ids):
        smiley_id = utils.check_int(raw_id)
        code = utils.trim_text(codes[index] if index < len(codes) else "")
        image = utils.trim_text(images[index] if index < len(images) else "")
        if not 1 <= len(code) <= 25 or not 1 <= len(image) <= 50:
            continue
        values = {"sm_code": code, "sm_image": image}
        if smiley_id == 0:
            db.insert(conn, "blog_Smilies", values)
            written += 1
        elif smiley_id > 0:
            db.update(conn, "blog_Smilies", values, "sm_id = ?", (smiley_id,))
            written += 1
    conn.commit()
    return {"action": action, "written": written}


def update_word_filter(conn: sqlite3.Connection, payload: dict) -> dict[str, Any]:
    action = str(payload.get("act") or "update")
    if action == "delete":
        selected = [utils.check_int(v) for v in payload.get("selected") or []]
        selected = [v for v in selected if v >= 1]
        if selected:
            placeholders = ", ".join("?" for _ in selected)
            conn.execute(
                f"DELETE FROM blog_WordFilter WHERE wf_id IN ({placeholders})",
                selected,
            )
            conn.commit()
        return {"action": action, "deleted": len(selected)}

    conn.execute("UPDATE blog_WordFilter SET wf_regExp = 0 WHERE wf_id > 0")
    regexp = [utils.check_int(v) for v in payload.get("regexp") or []]
    regexp = [v for v in regexp if v > 0]
    if regexp:
        conn.execute(
            f"UPDATE blog_WordFilter SET wf_regExp = 1 "
            f"WHERE wf_id IN ({', '.join('?' for _ in regexp)})",
            regexp,
        )

    ids = payload.get("id") or []
    modes = payload.get("mode") or []
    texts = payload.get("text") or []
    replaces = payload.get("replace") or []
    written = 0
    for index, raw_id in enumerate(ids):
        filter_id = utils.check_int(raw_id)
        mode = utils.check_int(modes[index] if index < len(modes) else 0)
        text = utils.trim_text(texts[index] if index < len(texts) else "")
        replace = utils.trim_text(replaces[index] if index < len(replaces) else "")
        if not 0 <= mode <= 1:
            continue
        if not 1 <= len(text) <= 25:
            continue
        if mode == 0 and not 1 <= len(replace) <= 50:
            continue
        values = {"wf_mode": mode, "wf_text": text, "wf_replace": replace}
        if filter_id == 0:
            values["wf_regExp"] = 1 if payload.get("newregexp") else 0
            db.insert(conn, "blog_WordFilter", values)
            written += 1
        elif filter_id > 0:
            db.update(conn, "blog_WordFilter", values, "wf_id = ?", (filter_id,))
            written += 1
    conn.commit()
    return {"action": action, "written": written}


# ---------------------------------------------------------------------------
# Maintenance (showMisc)
# ---------------------------------------------------------------------------


def _resync_global(conn: sqlite3.Connection) -> dict[str, int]:
    counters = {
        "counterArticle": ("blog_Article", "log_id"),
        "counterComment": ("blog_Comment", "comm_id"),
        "counterTrackback": ("blog_Trackback", "tb_id"),
        "counterUser": ("blog_User", "user_id"),
    }
    result = {}
    for name, (table, column) in counters.items():
        count = int(db.scalar(conn, f"SELECT COUNT({column}) FROM {table}") or 0)
        settings_module.put(conn, name, count)
        result[name] = count
    return result


def resync_categories(conn: sqlite3.Connection) -> int:
    rows = db.query_all(conn, "SELECT cat_id FROM blog_Category")
    for row in rows:
        count = db.scalar(
            conn,
            "SELECT COUNT(log_id) FROM blog_Article WHERE log_catID = ?",
            (row["cat_id"],),
        )
        conn.execute(
            "UPDATE blog_Category SET cat_articleCount = ? WHERE cat_id = ?",
            (int(count or 0), row["cat_id"]),
        )
    conn.commit()
    return len(rows)


def resync_article_stats(conn: sqlite3.Connection, *, start: int = 1, size: int = 20) -> dict:
    rows = db.query_all(
        conn,
        "SELECT log_id FROM blog_Article ORDER BY log_id LIMIT ? OFFSET ?",
        (size, max(start - 1, 0) * size),
    )
    for row in rows:
        comments = db.scalar(
            conn, "SELECT COUNT(comm_id) FROM blog_Comment WHERE log_id = ?",
            (row["log_id"],),
        )
        trackbacks = db.scalar(
            conn, "SELECT COUNT(tb_id) FROM blog_Trackback WHERE log_id = ?",
            (row["log_id"],),
        )
        conn.execute(
            "UPDATE blog_Article SET log_commentCount = ?, log_trackbackCount = ? "
            "WHERE log_id = ?",
            (int(comments or 0), int(trackbacks or 0), row["log_id"]),
        )
    conn.commit()
    return {"processed": len(rows), "next": start + 1 if rows else None}


def resync_user_stats(conn: sqlite3.Connection, *, start: int = 1, size: int = 50) -> dict:
    rows = db.query_all(
        conn,
        "SELECT user_id FROM blog_User ORDER BY user_id LIMIT ? OFFSET ?",
        (size, max(start - 1, 0) * size),
    )
    for row in rows:
        comments = db.scalar(
            conn, "SELECT COUNT(comm_id) FROM blog_Comment WHERE comm_authorID = ?",
            (row["user_id"],),
        )
        articles = db.scalar(
            conn, "SELECT COUNT(log_id) FROM blog_Article WHERE log_authorID = ?",
            (row["user_id"],),
        )
        conn.execute(
            "UPDATE blog_User SET user_commentCount = ?, user_articleCount = ? "
            "WHERE user_id = ?",
            (int(comments or 0), int(articles or 0), row["user_id"]),
        )
    conn.commit()
    return {"processed": len(rows), "next": start + 1 if rows else None}


def clean_inactive_users(conn: sqlite3.Connection, *, days: int = 30) -> int:
    cutoff = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        "DELETE FROM blog_User WHERE user_commentCount = 0 AND user_articleCount = 0 "
        "AND user_lastVisit < ? AND user_groupID <> 1",
        (cutoff,),
    )
    _resync_global(conn)
    conn.commit()
    return cursor.rowcount


def clean_visitor_records(conn: sqlite3.Connection) -> int:
    cursor = conn.execute("DELETE FROM blog_VisitorRecord")
    conn.commit()
    return cursor.rowcount


def clean_guestbook(conn: sqlite3.Connection, *, days: int = 30) -> int:
    cutoff = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute("DELETE FROM Guestbook WHERE gb_postTime < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount


# ---------------------------------------------------------------------------
# Database operations (showDatabase / compactDatabase / backupDatabase)
# ---------------------------------------------------------------------------


def file_size_string(size: int) -> str:
    """Port of ``fileSizeString``."""
    if size > 1024 * 1024 * 1024:
        return f"{round(size / 1024 / 1024 / 1024, 2)}{lang.text('gb')}"
    if size > 1024 * 1024:
        return f"{round(size / 1024 / 1024, 2)}{lang.text('mb')}"
    if size > 1024:
        return f"{round(size / 1024, 2)}{lang.text('kb')}"
    return f"{size}{lang.text('bytes')}"


def database_info(conn: sqlite3.Connection) -> dict[str, Any]:
    path = config.db_path()
    size = path.stat().st_size if path.is_file() else 0
    return {
        "path": str(path),
        "name": path.name,
        "size": size,
        "size_text": file_size_string(size),
        "backups": list_backups(),
    }


def backup_paths() -> "list[Path]":
    data_dir = config.require_data_dir()
    return sorted(data_dir.glob("*.bak"))


def list_backups() -> list[dict[str, Any]]:
    items = []
    for path in backup_paths():
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "size_text": file_size_string(stat.st_size),
                "mtime": dt.datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    return items


def compact_database(conn: sqlite3.Connection) -> dict[str, Any]:
    conn.execute("VACUUM")
    conn.commit()
    return {"ok": True, "size": config.db_path().stat().st_size}


def backup_database(conn: sqlite3.Connection) -> dict[str, Any]:
    """``copy_to_backup``: <name>_YYMMDD_hhiiss.bak next to the database."""
    path = config.db_path()
    stamp = dt.datetime.now().strftime("_%Y%m%d_%H%M%S")
    target = path.with_name(path.stem + stamp + ".bak")
    with sqlite3.connect(str(target)) as destination:
        conn.backup(destination)
    return {
        "ok": True,
        "name": target.name,
        "size": target.stat().st_size,
        "size_text": file_size_string(target.stat().st_size),
    }


def resolve_backup(name: str) -> "Path | None":
    """Only allow plain file names inside the data directory."""
    candidate = (config.require_data_dir() / Path(name).name).resolve()
    if candidate.parent != config.require_data_dir().resolve():
        return None
    return candidate if candidate.is_file() else None


def restore_database(conn: sqlite3.Connection, name: str) -> bool:
    source_path = resolve_backup(name)
    if source_path is None:
        return False
    with sqlite3.connect(str(source_path)) as source:
        source.backup(conn)
    conn.commit()
    return True


def delete_backup(name: str) -> bool:
    path = resolve_backup(name)
    if path is None:
        return False
    path.unlink()
    return True


# ---------------------------------------------------------------------------
# Attachments (showAttachment)
# ---------------------------------------------------------------------------


def upload_dir() -> Path:
    base = config.require_data_dir() / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    return base


def resolve_upload(relative: str) -> "Path | None":
    base = upload_dir().resolve()
    cleaned = str(relative or "").replace("\\", "/").lstrip("/.")
    candidate = (base / cleaned).resolve()
    if candidate != base and base not in candidate.parents:
        return None
    return candidate


def list_attachments(relative: str = "") -> dict[str, Any]:
    base = upload_dir()
    target = resolve_upload(relative)
    if target is None or not target.is_dir():
        target = base
        relative = ""
    items = []
    for entry in sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name)):
        try:
            size = entry.stat().st_size if entry.is_file() else _folder_size(entry)
        except OSError:
            size = 0
        items.append(
            {
                "name": entry.name,
                "size": size,
                "size_text": file_size_string(size),
                "type": "folder" if entry.is_dir() else "file",
            }
        )
    return {"path": relative, "items": items, "base": str(base)}


def _folder_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


def delete_attachment(relative: str, name: str) -> bool:
    folder = resolve_upload(relative)
    if folder is None:
        return False
    target = (folder / Path(name).name).resolve()
    if folder.resolve() not in target.parents:
        return False
    if target.is_dir():
        # The ASP version only removes folders that are already empty.
        if any(target.iterdir()):
            return False
        target.rmdir()
        return True
    if target.is_file():
        target.unlink()
        return True
    return False
