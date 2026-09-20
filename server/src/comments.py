"""Comment writes, ported from ``source/src_comment.asp``.

The guest posting path is kept: an anonymous visitor may comment under a free
display name, or log in by supplying a password, exactly like the ASP version.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import articles
import cache
import db
import settings as settings_module
import users
import utils


def validate_comment_form(
    conn: sqlite3.Connection, payload: dict
) -> "tuple[dict[str, Any] | None, list[str]]":
    """Port of ``checkPostData`` (security code excluded while it is disabled)."""
    errors: list[str] = []
    message = utils.trim_text(payload.get("message") or "")
    if not message:
        errors.append("content_blank")
    else:
        max_length = settings_module.get_int(conn, "maxCommentLength", 1000)
        if len(message) > max_length or len(message) < 2:
            errors.append("length_invalid")
        filtered = utils.word_filter(cache.word_filters(conn), message)
        if filtered is False:
            errors.append("wordfilter_block")
        else:
            message = filtered
    if errors:
        return None, errors
    return (
        {
            "comm_content": message,
            "comm_hidden": 1 if payload.get("comm_hidden") else 0,
            "comm_ubbFlags": articles.ubb_flags_from_form(payload, comment=True),
        },
        errors,
    )


def guest_identity(
    conn: sqlite3.Connection, payload: dict
) -> "tuple[dict[str, Any] | None, str | None]":
    """Resolve the author for an anonymous comment.

    Returns ``(author, error)`` where author is ``{"id": 0, "name": ...}`` for a
    guest, or the verified user when a password was supplied.
    """
    name = str(payload.get("comm_username") or "").strip()
    password = str(payload.get("comm_password") or "")
    if not name:
        return None, "username_invalid"
    if password:
        user = users.verify(conn, name, password)
        if not user:
            return None, "login_fail"
        return {"id": user["id"], "name": user["name"]}, None
    if not utils.check_username(name):
        return None, "username_invalid"
    if users.get_by_name(conn, name):
        return None, "user_exist"
    return {"id": 0, "name": name}, None


def create_comment(
    conn: sqlite3.Connection,
    article_id: int,
    fields: dict[str, Any],
    *,
    author: dict[str, Any],
    ip: str,
) -> int:
    values = dict(fields)
    values.update(
        {
            "log_id": article_id,
            "comm_authorID": author.get("id", 0),
            "comm_author": author.get("name", ""),
            "comm_editMark": "",
            "comm_postTime": utils.get_date_time_string(None, None),
            "comm_ip": (ip or "")[:15],
        }
    )
    comment_id = db.insert(conn, "blog_Comment", values)
    conn.execute(
        "UPDATE blog_Article SET log_commentCount = log_commentCount + 1 "
        "WHERE log_id = ?",
        (article_id,),
    )
    if author.get("id"):
        conn.execute(
            "UPDATE blog_User SET user_commentCount = user_commentCount + 1 "
            "WHERE user_id = ?",
            (author["id"],),
        )
    settings_module.bump(conn, "counterComment", 1)
    conn.commit()
    return comment_id


def update_comment(
    conn: sqlite3.Connection, comment_id: int, fields: dict[str, Any], *, editor: str
) -> None:
    row = db.query_one(
        conn, "SELECT comm_id FROM blog_Comment WHERE comm_id = ?", (comment_id,)
    )
    if row is None:
        raise ValueError("comment_not_found")
    values = dict(fields)
    values["comm_editMark"] = f"{editor}$|${utils.get_date_time_string(None, None)}"
    db.update(conn, "blog_Comment", values, "comm_id = ?", (comment_id,))
    conn.commit()


def delete_comment(conn: sqlite3.Connection, comment_id: int) -> None:
    row = db.query_one(
        conn, "SELECT log_id, comm_authorID FROM blog_Comment WHERE comm_id = ?",
        (comment_id,),
    )
    if row is None:
        raise ValueError("comment_not_found")
    conn.execute("DELETE FROM blog_Comment WHERE comm_id = ?", (comment_id,))
    conn.execute(
        "UPDATE blog_Article SET log_commentCount = MAX(log_commentCount - 1, 0) "
        "WHERE log_id = ?",
        (int(row["log_id"] or 0),),
    )
    if int(row["comm_authorID"] or 0):
        conn.execute(
            "UPDATE blog_User SET user_commentCount = MAX(user_commentCount - 1, 0) "
            "WHERE user_id = ?",
            (int(row["comm_authorID"]),),
        )
    settings_module.bump(conn, "counterComment", -1)
    conn.commit()


# ---------------------------------------------------------------------------
# Comment list page (source/src_comment.asp, default branch)
# ---------------------------------------------------------------------------


def list_comments(
    conn: sqlite3.Connection,
    *,
    viewer: "dict | None" = None,
    page: int = 1,
    category: int = 0,
    author: int = 0,
    keywords: "tuple[str, ...]" = (),
    highlight_words: "tuple[str, ...]" = (),
) -> "dict[str, Any]":
    """Port of ``commentList``: comments across articles, newest first."""
    clauses: list[str] = []
    params: list[Any] = []
    if category:
        clauses.append("tLog.log_catID = ?")
        params.append(category)
    if author:
        clauses.append("tComm.comm_authorID = ?")
        params.append(author)
    for word in keywords:
        if utils.length_w(word) > 2:
            clauses.append("tComm.comm_content LIKE ?")
            params.append(f"%{word}%")

    rights = (viewer or {}).get("rights") or users.parse_rights("11110")
    if int(rights.get("view", 0)) < 2:
        clauses.append("tLog.log_mode = 1")
        hidden = [item["id"] for item in cache.categories(conn) if item["hidden"]]
        if hidden:
            clauses.append(
                f"tLog.log_catID NOT IN ({', '.join('?' for _ in hidden)})"
            )
            params.extend(hidden)

    source = (
        "FROM blog_Article tLog, blog_Comment tComm "
        "WHERE tLog.log_id = tComm.log_id"
    )
    if clauses:
        source += " AND " + " AND ".join(clauses)
    total = int(db.scalar(conn, f"SELECT COUNT(tComm.comm_id) {source}", params) or 0)
    size = max(settings_module.get_int(conn, "listEntryPerPage", 30), 1)
    page = max(int(page or 1), 1)
    rows = db.query_all(
        conn,
        f"SELECT tComm.*, tLog.log_authorID, tLog.log_title {source} "
        "ORDER BY tComm.comm_postTime DESC LIMIT ? OFFSET ?",
        [*params, size, (page - 1) * size],
    )

    items = []
    for row in rows:
        data = dict(row)
        content = articles.render(
            conn,
            utils.html_encode(data["comm_content"] or ""),
            data["comm_ubbFlags"] or "111111",
            nofollow=True,
        )
        if highlight_words:
            content = utils.highlight(content, highlight_words)
        article_author = int(data["log_authorID"] or 0)
        comment_author = int(data["comm_authorID"] or 0)
        items.append(
            {
                "id": int(data["comm_id"]),
                "article_id": int(data["log_id"] or 0),
                "article_title": data["log_title"] or "",
                "article_author_id": article_author,
                "author": data["comm_author"] or "",
                "author_id": comment_author,
                "content": data["comm_content"] or "",
                "content_html": content,
                "hidden": bool(data["comm_hidden"]),
                "post_time": data["comm_postTime"] or "",
                "edit_mark": data["comm_editMark"] or "",
                "ip": data["comm_ip"] or "",
                "ubb_flags": data["comm_ubbFlags"] or "111111",
                "can_edit": bool(viewer) and users.can_operate(
                    viewer["rights"], "edit",
                    owner=viewer["id"] in (article_author, comment_author),
                ),
                "can_delete": bool(viewer) and users.can_operate(
                    viewer["rights"], "delete",
                    owner=viewer["id"] in (article_author, comment_author),
                ),
                "visible": (
                    not data["comm_hidden"]
                    or bool(viewer) and (
                        viewer["id"] == article_author
                        or (comment_author and viewer["id"] == comment_author)
                    )
                ),
            }
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "pages": max((total + size - 1) // size, 1),
    }


def get_comment(conn: sqlite3.Connection, comment_id: int) -> "dict[str, Any] | None":
    row = db.query_one(
        conn,
        "SELECT c.*, a.log_authorID FROM blog_Comment c "
        "JOIN blog_Article a ON a.log_id = c.log_id WHERE c.comm_id = ?",
        (comment_id,),
    )
    if row is None:
        return None
    data = dict(row)
    return {
        "id": int(data["comm_id"]),
        "article_id": int(data["log_id"] or 0),
        "article_author_id": int(data["log_authorID"] or 0),
        "author": data["comm_author"] or "",
        "author_id": int(data["comm_authorID"] or 0),
        "content": data["comm_content"] or "",
        "ubb_flags": data["comm_ubbFlags"] or "111111",
        "hidden": bool(data["comm_hidden"]),
    }
