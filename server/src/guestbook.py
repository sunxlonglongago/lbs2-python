"""Guestbook reads and writes, ported from ``source/src_gbook.asp``.

The guestbook lives in its own ``Guestbook`` table alongside everything else in
the single SQLite file.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import articles
import cache
import db
import settings as settings_module
import utils

DEFAULT_PER_PAGE = 10


def page_size(conn: sqlite3.Connection) -> int:
    return max(
        settings_module.get_int(conn, "entryPerPageGuestBook", DEFAULT_PER_PAGE), 1
    )


def _render(conn: sqlite3.Connection, text: Any, flags: str) -> str:
    return articles.render(conn, utils.html_encode(text or ""), flags, nofollow=True)


def visible(entry: dict[str, Any], viewer: "dict | None") -> bool:
    """``!hidden || (own entry) || rights.view > 2``."""
    if not entry["hidden"]:
        return True
    if not viewer:
        return False
    if entry["user_id"] and entry["user_id"] == viewer["id"]:
        return True
    return int(viewer["rights"].get("view", 0)) > 2


def list_entries(
    conn: sqlite3.Connection,
    *,
    viewer: "dict | None" = None,
    page: int = 1,
    keywords: Sequence[str] = (),
    highlight_words: Sequence[str] = (),
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if keywords:
        clauses.append("gb_hidden = 0")
        for word in keywords:
            if utils.length_w(word) > 2:
                clauses.append("(gb_content LIKE ? OR gb_reply LIKE ?)")
                params.extend([f"%{word}%", f"%{word}%"])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = int(db.scalar(conn, f"SELECT COUNT(*) FROM Guestbook{where}", params) or 0)

    size = page_size(conn)
    page = max(int(page or 1), 1)
    rows = db.query_all(
        conn,
        f"SELECT * FROM Guestbook{where} ORDER BY gb_postTime DESC LIMIT ? OFFSET ?",
        [*params, size, (page - 1) * size],
    )

    items = []
    for row in rows:
        data = dict(row)
        entry = {
            "id": int(data["gb_id"]),
            "user_id": int(data["gb_userID"] or 0),
            "username": data["gb_username"] or "",
            "post_time": data["gb_postTime"] or "",
            "ip": data["gb_ip"] or "",
            "hidden": bool(data["gb_hidden"]),
            "edit_mark": data["gb_editMark"] or "",
            "reply_username": data["gb_replyUsername"] or "",
            "reply_time": data["gb_replyTime"] or "",
            "has_reply": bool(data["gb_reply"]),
        }
        entry["visible"] = visible(entry, viewer)
        if entry["visible"]:
            content = _render(conn, data["gb_content"] or "", data["gb_ubbFlags"] or "111111")
            reply = _render(conn, data["gb_reply"] or "", "110011")
            if highlight_words:
                content = utils.highlight(content, highlight_words)
                reply = utils.highlight(reply, highlight_words)
            entry["content_html"] = content
            entry["reply_html"] = reply
        else:
            entry["content_html"] = ""
            entry["reply_html"] = ""
        entry["can_edit"] = bool(viewer) and (
            int(viewer["rights"].get("edit", 0)) > 1
            or (int(viewer["rights"].get("edit", 0)) == 1
                and entry["user_id"] == viewer["id"])
        )
        entry["can_delete"] = bool(viewer) and (
            int(viewer["rights"].get("delete", 0)) > 1
            or (int(viewer["rights"].get("delete", 0)) == 1
                and entry["user_id"] == viewer["id"])
            or viewer["group_id"] == 1
        )
        items.append(entry)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "pages": max((total + size - 1) // size, 1),
    }


def validate_content(
    conn: sqlite3.Connection, value: Any, *, code_key: str = "content_blank"
) -> "tuple[str | None, str | None]":
    text_value = utils.trim_text(value or "")
    if not text_value:
        return None, code_key
    max_length = settings_module.get_int(conn, "maxCommentLength", 1000)
    if len(text_value) > max_length or len(text_value) < 2:
        return None, "length_invalid"
    filtered = utils.word_filter(cache.word_filters(conn), text_value)
    if filtered is False:
        return None, "wordfilter_block"
    return filtered, None


def validate_entry_form(
    conn: sqlite3.Connection, payload: dict
) -> "tuple[dict[str, Any] | None, list[str]]":
    errors: list[str] = []
    content, error = validate_content(conn, payload.get("message"))
    if error:
        errors.append(error)
    reply = None
    if payload.get("entry") is not None:
        # Port of the content/reply swap in checkPostData: "entry" carries the
        # original text and "message" the reply when the reply area is shown.
        content, error = validate_content(conn, payload.get("entry"))
        if error:
            errors.append(error)
        reply, error = validate_content(conn, payload.get("message"))
        if error:
            errors.append(error)
    if errors:
        return None, errors
    fields = {
        "gb_content": content,
        "gb_ubbFlags": articles.ubb_flags_from_form(payload, comment=True),
        "gb_hidden": 1 if payload.get("comm_hidden") else 0,
    }
    if reply is not None:
        fields["_reply"] = reply
    return fields, errors


def create_entry(
    conn: sqlite3.Connection, fields: dict[str, Any], *, author: dict[str, Any], ip: str
) -> int:
    values = dict(fields)
    values.pop("_reply", None)
    values.update(
        {
            "gb_userID": author.get("id", 0),
            "gb_username": author.get("name", ""),
            "gb_editMark": "",
            "gb_postTime": utils.get_date_time_string(None, None),
            "gb_replyUsername": "",
            "gb_reply": "",
            "gb_replyTime": "",
            "gb_ip": (ip or "")[:15],
        }
    )
    entry_id = db.insert(conn, "Guestbook", values)
    conn.commit()
    return entry_id


def get_entry(conn: sqlite3.Connection, entry_id: int) -> "dict[str, Any] | None":
    row = db.query_one(conn, "SELECT * FROM Guestbook WHERE gb_id = ?", (entry_id,))
    if row is None:
        return None
    data = dict(row)
    return {
        "id": int(data["gb_id"]),
        "user_id": int(data["gb_userID"] or 0),
        "username": data["gb_username"] or "",
        "content": data["gb_content"] or "",
        "reply": data["gb_reply"] or "",
        "ubb_flags": data["gb_ubbFlags"] or "110011",
        "hidden": bool(data["gb_hidden"]),
        "post_time": data["gb_postTime"] or "",
        "reply_time": data["gb_replyTime"] or "",
        "reply_username": data["gb_replyUsername"] or "",
        "ip": data["gb_ip"] or "",
        "edit_mark": data["gb_editMark"] or "",
    }


def update_entry(
    conn: sqlite3.Connection,
    entry_id: int,
    fields: dict[str, Any],
    *,
    user: dict[str, Any],
    allow_reply: bool,
) -> None:
    existing = get_entry(conn, entry_id)
    if existing is None:
        raise ValueError("comment_not_found")
    values = dict(fields)
    reply = values.pop("_reply", None)
    if values["gb_content"] != existing["content"]:
        values["gb_editMark"] = (
            f"{user['name']}$|${utils.get_date_time_string(None, None)}"
        )
    if allow_reply and reply is not None:
        values["gb_reply"] = reply
        values["gb_replyUsername"] = user["name"]
        values["gb_replyTime"] = utils.get_date_time_string(None, None)
    db.update(conn, "Guestbook", values, "gb_id = ?", (entry_id,))
    conn.commit()


def can_edit(entry: dict[str, Any], user: dict[str, Any]) -> bool:
    level = int(user["rights"].get("edit", 0))
    return level >= 1 and (level > 1 or entry["user_id"] == user["id"])


def can_delete(entry: dict[str, Any], user: dict[str, Any]) -> bool:
    level = int(user["rights"].get("delete", 0))
    if level < 1:
        return False
    if user["group_id"] == 1 or level > 1:
        return True
    return entry["user_id"] == user["id"]


def delete_entry(conn: sqlite3.Connection, entry_id: int) -> None:
    if get_entry(conn, entry_id) is None:
        raise ValueError("comment_not_found")
    conn.execute("DELETE FROM Guestbook WHERE gb_id = ?", (entry_id,))
    conn.commit()
