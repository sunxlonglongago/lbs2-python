"""Trackback receive / list / delete / send (source/src_trackback.asp)."""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import articles
import cache
import db
import settings as settings_module
import users
import utils

DEFAULT_PER_PAGE = 30


def page_size(conn: sqlite3.Connection) -> int:
    return max(settings_module.get_int(conn, "listEntryPerPage", DEFAULT_PER_PAGE), 1)


def list_trackbacks(
    conn: sqlite3.Connection,
    *,
    viewer: "dict | None" = None,
    page: int = 1,
    category: int = 0,
    article_id: int = 0,
    keywords: Sequence[str] = (),
    highlight_words: Sequence[str] = (),
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if category:
        clauses.append("tLog.log_catID = ?")
        params.append(category)
    if article_id:
        clauses.append("tTB.log_id = ?")
        params.append(article_id)
    for word in keywords:
        if utils.length_w(word) > 2:
            clauses.append("(tTB.tb_title LIKE ? OR tTB.tb_excerpt LIKE ?)")
            params.extend([f"%{word}%", f"%{word}%"])
    visibility, visibility_params = articles.visibility_filters(conn, viewer)
    clauses.extend(visibility)
    params.extend(visibility_params)
    source = (
        "FROM blog_Article tLog, blog_Trackback tTB "
        "WHERE tLog.log_id = tTB.log_id"
    )
    if clauses:
        source += " AND " + " AND ".join(clauses)
    total = int(db.scalar(conn, f"SELECT COUNT(tTB.tb_id) {source}", params) or 0)
    size = page_size(conn)
    page = max(int(page or 1), 1)
    rows = db.query_all(
        conn,
        f"SELECT tTB.*, tLog.log_authorID, tLog.log_title {source} "
        "ORDER BY tTB.tb_time DESC LIMIT ? OFFSET ?",
        [*params, size, (page - 1) * size],
    )

    items = []
    for row in rows:
        data = dict(row)
        title = utils.html_encode(data["tb_title"] or "")
        excerpt = utils.html_encode(data["tb_excerpt"] or "")
        if highlight_words:
            title = utils.highlight(title, highlight_words)
            excerpt = utils.highlight(excerpt, highlight_words)
        items.append(
            {
                "id": int(data["tb_id"]),
                "article_id": int(data["log_id"] or 0),
                "article_title": data["log_title"] or "",
                "article_author_id": int(data["log_authorID"] or 0),
                "title": data["tb_title"] or "",
                "title_html": title,
                "url": data["tb_url"] or "",
                "blog": data["tb_blog"] or "",
                "excerpt": data["tb_excerpt"] or "",
                "excerpt_html": excerpt,
                "time": data["tb_time"] or "",
                "ip": data["tb_ip"] or "",
            }
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "pages": max((total + size - 1) // size, 1),
    }


def receive(
    conn: sqlite3.Connection, payload: dict, *, ip: str
) -> "tuple[int, str | None]":
    """Port of ``trackbackSave``; returns ``(error_flag, message)``."""
    filters = cache.word_filters(conn)
    article_id = utils.check_int(payload.get("id"))
    url = utils.trim_text(utils.word_filter(filters, utils.check_url(payload.get("url") or "")))
    title = utils.trim_text(
        utils.word_filter(filters, utils.trim_html(utils.trim_ubb(payload.get("title") or "")))
    )
    excerpt = utils.trim_text(
        utils.word_filter(filters, utils.trim_html(utils.trim_ubb(payload.get("excerpt") or "")))
    )
    blog = utils.trim_text(
        utils.word_filter(
            filters,
            utils.trim_html(utils.trim_ubb(payload.get("blog_name") or "")),
        )
    )
    if title == "":
        title = url

    # Error strings stay in English, like the original.
    if not article_id:
        return 1, "Invalid Article ID"
    if url == "":
        return 1, "Source URL is Blank"
    if False in (url, title, excerpt, blog):
        return 1, "Content contains blocked words"

    article = db.query_one(
        conn,
        "SELECT log_id FROM blog_Article "
        "WHERE log_locked = 0 AND log_mode < 4 AND log_id = ?",
        (article_id,),
    )
    if article is None:
        return 1, "Article does not exist or is locked"

    duplicate = db.scalar(
        conn,
        "SELECT COUNT(tb_id) FROM blog_Trackback WHERE tb_title = ? AND tb_excerpt = ?",
        (title, excerpt),
    )
    if int(duplicate or 0) > 0:
        return 1, "Trackback is already saved"

    db.insert(
        conn,
        "blog_Trackback",
        {
            "log_id": article_id,
            "tb_url": url,
            "tb_title": title,
            "tb_excerpt": excerpt,
            "tb_blog": blog,
            "tb_ip": (ip or "")[:15],
            "tb_time": utils.get_date_time_string(None, None),
        },
    )
    conn.execute(
        "UPDATE blog_Article SET log_trackbackCount = log_trackbackCount + 1 "
        "WHERE log_id = ?",
        (article_id,),
    )
    settings_module.bump(conn, "counterTrackback", 1)
    conn.commit()
    return 0, None


def response_xml(error: int, message: "str | None" = None) -> str:
    body = f'<?xml version="1.0" encoding="iso-8859-1"?><response><error>{error}</error>'
    if error == 1 and message:
        body += f"<message>{message}</message>"
    return body + "</response>"


def can_delete(row: dict, user: dict) -> bool:
    """``theUser.id == article author`` plus delete rights (see the plan note)."""
    return user["group_id"] == 1 or users.can_operate(
        user["rights"],
        "delete",
        owner=int(row.get("log_authorID") or 0) == user["id"],
    )


def delete_trackback(conn: sqlite3.Connection, trackback_id: int) -> int:
    row = db.query_one(
        conn,
        "SELECT tTB.tb_id, tTB.log_id, tLog.log_authorID FROM blog_Article tLog, "
        "blog_Trackback tTB WHERE tLog.log_id = tTB.log_id AND tTB.tb_id = ?",
        (trackback_id,),
    )
    if row is None:
        raise ValueError("trackback_not_found")
    conn.execute("DELETE FROM blog_Trackback WHERE tb_id = ?", (trackback_id,))
    conn.execute(
        "UPDATE blog_Article SET log_trackbackCount = MAX(log_trackbackCount - 1, 0) "
        "WHERE log_id = ?",
        (int(row["log_id"] or 0),),
    )
    settings_module.bump(conn, "counterTrackback", -1)
    conn.commit()
    return int(row["log_id"] or 0)


def send(
    target_url: str,
    *,
    url: str,
    title: str,
    excerpt: str,
    blog_name: str,
    timeout: float = 15.0,
) -> "str | None":
    """Port of ``doTrackback``: POST the form and parse the XML response."""
    import re
    import urllib.parse
    import urllib.request

    payload = urllib.parse.urlencode(
        {
            "title": utils.cut_string(title, 100),
            "url": url,
            "blog_name": utils.cut_string(blog_name, 100),
            "excerpt": utils.trim_ubb(utils.cut_string(excerpt, 252)),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        target_url, data=payload, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return "server_no_response"
            body = response.read().decode("utf-8", "replace")
    except Exception:
        return "server_no_response"
    if "<error>0</error>" in body or "<error>0</error>" in body.replace(" ", ""):
        return None
    match = re.search(r"<message>(.*?)</message>", body, re.S)
    return match.group(1) if match else "parse_error"
