"""Article, comment and trackback queries for the read only views."""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Sequence

import cache
import db
import settings as settings_module
import ubbcode
import users
import utils

DEFAULT_NORMAL_PER_PAGE = 8
DEFAULT_LIST_PER_PAGE = 40


# ---------------------------------------------------------------------------
# Settings and rendering helpers
# ---------------------------------------------------------------------------


def page_size(conn: sqlite3.Connection, mode: int) -> int:
    """Normal and list views use different page sizes (src_default.asp)."""
    if int(mode or 0) == 1:
        return max(settings_module.get_int(conn, "articlePerPageList", DEFAULT_LIST_PER_PAGE), 1)
    return max(
        settings_module.get_int(conn, "articlePerPageNormal", DEFAULT_NORMAL_PER_PAGE), 1
    )


def render(conn: sqlite3.Connection, text: Any, flags: str, *, nofollow: bool = False) -> str:
    values = cache.settings(conn)
    return ubbcode.render(
        text,
        flags,
        image_folder=values.get("imageFolder", ""),
        smilies_folder=values.get("smiliesFolder", ""),
        smilies=cache.smilies(conn),
        base_url=values.get("baseURL", ""),
        link_nofollow=nofollow,
    )


def renderer(conn: sqlite3.Connection) -> ubbcode.UBBRenderer:
    """A UBB renderer wired to the current site settings (used by the feeds)."""
    values = cache.settings(conn)
    return ubbcode.UBBRenderer(
        image_folder=values.get("imageFolder", ""),
        smilies_folder=values.get("smiliesFolder", ""),
        smilies=cache.smilies(conn),
    )


def render_article_content(conn: sqlite3.Connection, row: dict, *, full: bool) -> str:
    """Port of the content branches in ``default.asp`` and ``article.asp``."""
    flags = row.get("log_ubbFlags") or "111111"
    content0 = row.get("log_content0") or ""
    content1 = row.get("log_content1") or ""

    if flags == "html":
        if full:
            joined = content0 + content1
            return re.sub(r"\[separator\]", "", joined, flags=re.IGNORECASE)
        return utils.close_html(content0)

    if full:
        return render(conn, utils.html_encode(content0 + content1), flags)
    return render(conn, utils.close_ubb(utils.html_encode(content0)), flags)


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------


def _hidden_categories(conn: sqlite3.Connection) -> list[int]:
    return [row["id"] for row in cache.categories(conn) if row["hidden"]]


def visibility_filters(
    conn: sqlite3.Connection, viewer: "dict | None"
) -> "tuple[list[str], list[Any]]":
    """Extra WHERE fragments and parameters for the viewer's group rights."""
    rights = (viewer or {}).get("rights") or users.parse_rights("11110")
    logged_in = bool(viewer)
    view = int(rights.get("view", 0))
    clauses: list[str] = []
    params: list[Any] = []

    if view < 1:
        clauses.append("1 = 0")
    elif view == 1:
        clauses.append("log_mode < 3" if logged_in else "log_mode = 1")
    elif view == 2:
        clauses.append("log_mode < 4")

    if view < 2:
        hidden = _hidden_categories(conn)
        if hidden:
            placeholders = ", ".join("?" for _ in hidden)
            clauses.append(f"log_catID NOT IN ({placeholders})")
            params.extend(hidden)
    return clauses, params


def can_view(conn: sqlite3.Connection, row: dict, viewer: "dict | None") -> bool:
    rights = (viewer or {}).get("rights") or users.parse_rights("11110")
    category = cache.get_category(cache.categories(conn), int(row.get("log_catID") or 0))
    return users.can_view_article(
        rights,
        logged_in=bool(viewer),
        user_id=int((viewer or {}).get("id") or 0),
        mode=int(row.get("log_mode") or 1),
        category_hidden=bool(category["hidden"]),
        author_id=int(row.get("log_authorID") or 0),
    )


# ---------------------------------------------------------------------------
# Shaping
# ---------------------------------------------------------------------------


BASE_FIELDS = (
    "log_id",
    "log_catID",
    "log_title",
    "log_authorID",
    "log_author",
    "log_mode",
    "log_locked",
    "log_selected",
    "log_ubbFlags",
    "log_postTime",
    "log_ip",
    "log_commentCount",
    "log_viewCount",
    "log_trackbackCount",
    "log_trackbackURL",
    "log_editMark",
)


def article_summary(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    category = cache.get_category(cache.categories(conn), int(data.get("log_catID") or 0))
    return {
        "id": int(data["log_id"]),
        "title": data["log_title"] or "",
        "author": data["log_author"] or "",
        "author_id": int(data["log_authorID"] or 0),
        "category": category,
        "mode": int(data["log_mode"] or 1),
        "locked": bool(data["log_locked"]),
        "selected": bool(data["log_selected"]),
        "ubb_flags": data["log_ubbFlags"] or "111111",
        "post_time": data["log_postTime"] or "",
        "ip": data["log_ip"] or "",
        "comment_count": int(data["log_commentCount"] or 0),
        "trackback_count": int(data["log_trackbackCount"] or 0),
        "view_count": int(data["log_viewCount"] or 0),
        "trackback_url": data["log_trackbackURL"] or "",
        "edit_mark": data["log_editMark"] or "",
    }


def _select_fields(*, list_mode: bool) -> str:
    fields = list(BASE_FIELDS)
    if not list_mode:
        fields.append("log_content0")
        # The index view only needs to know whether content1 carries text.
        fields.append("substr(log_content1, 1, 2) AS content1_flag")
    return ", ".join(fields)


def build_filters(
    conn: sqlite3.Connection,
    viewer: "dict | None",
    *,
    category: int = 0,
    author: int = 0,
    selected: bool = False,
    keywords: Sequence[str] = (),
    year: int = 0,
    month: int = 0,
    day: int = 0,
) -> "tuple[list[str], list[Any]]":
    clauses: list[str] = []
    params: list[Any] = []
    if selected:
        clauses.append("log_selected = 1")
    if category:
        clauses.append("log_catID = ?")
        params.append(category)
    if author:
        clauses.append("log_authorID = ?")
        params.append(author)
    for word in keywords:
        if utils.length_w(word) > 2:
            clauses.append(
                "(log_title LIKE ? OR log_content0 LIKE ? OR log_content1 LIKE ?)"
            )
            params.extend([f"%{word}%"] * 3)
    if year:
        clauses.append("strftime('%Y', log_postTime) = ?")
        params.append(f"{int(year):04d}")
        if month and 1 <= int(month) <= 12:
            clauses.append("strftime('%m', log_postTime) = ?")
            params.append(f"{int(month):02d}")
            if day and 1 <= int(day) <= 31:
                clauses.append("strftime('%d', log_postTime) = ?")
                params.append(f"{int(day):02d}")
    visibility, visibility_params = visibility_filters(conn, viewer)
    clauses.extend(visibility)
    params.extend(visibility_params)
    return clauses, params


def list_articles(
    conn: sqlite3.Connection,
    *,
    viewer: "dict | None" = None,
    mode: int = 0,
    page: int = 1,
    category: int = 0,
    author: int = 0,
    selected: bool = False,
    keywords: Sequence[str] = (),
    year: int = 0,
    month: int = 0,
    day: int = 0,
) -> dict[str, Any]:
    clauses, params = build_filters(
        conn,
        viewer,
        category=category,
        author=author,
        selected=selected,
        keywords=keywords,
        year=year,
        month=month,
        day=day,
    )
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = int(db.scalar(conn, f"SELECT COUNT(*) FROM blog_Article{where}", params) or 0)

    size = page_size(conn, mode)
    page = max(int(page or 1), 1)
    list_mode = int(mode or 0) == 1
    sql = (
        f"SELECT {_select_fields(list_mode=list_mode)} FROM blog_Article{where} "
        "ORDER BY log_postTime DESC LIMIT ? OFFSET ?"
    )
    rows = db.query_all(conn, sql, [*params, size, (page - 1) * size])

    items = []
    for row in rows:
        item = article_summary(conn, row)
        if list_mode:
            item["content_html"] = ""
            item["has_more"] = False
        else:
            data = dict(row)
            item["content_html"] = render_article_content(conn, data, full=False)
            item["has_more"] = len(str(data.get("content1_flag") or "")) > 1
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "pages": max((total + size - 1) // size, 1),
        "mode": 1 if list_mode else 0,
    }


def get_article(
    conn: sqlite3.Connection, article_id: int, viewer: "dict | None" = None
) -> "dict[str, Any] | None":
    row = db.query_one(conn, "SELECT * FROM blog_Article WHERE log_id = ?", (article_id,))
    if row is None:
        return None
    data = dict(row)
    if not can_view(conn, data, viewer):
        return None
    item = article_summary(conn, row)
    item["content_html"] = render_article_content(conn, data, full=True)
    # The edit form edits the raw markup, separator token included.
    item["content_raw"] = (data.get("log_content0") or "") + (
        data.get("log_content1") or ""
    )
    item["has_more"] = False
    return item


def side_articles(
    conn: sqlite3.Connection, article: dict[str, Any], viewer: "dict | None" = None
) -> "tuple[dict | None, dict | None]":
    """Return ``(previous, next)`` neighbours by post time."""
    clauses, params = build_filters(conn, viewer)
    extra = f" AND {' AND '.join(clauses)}" if clauses else ""

    def neighbour(operator: str, order: str) -> "dict[str, Any] | None":
        row = db.query_one(
            conn,
            f"SELECT log_id, log_title FROM blog_Article "
            f"WHERE log_postTime {operator} ?{extra} "
            f"ORDER BY log_postTime {order} LIMIT 1",
            [article["post_time"], *params],
        )
        if row is None:
            return None
        return {"id": int(row["log_id"]), "title": row["log_title"] or ""}

    return neighbour("<", "DESC"), neighbour(">", "ASC")


def load_comments(
    conn: sqlite3.Connection,
    article_id: int,
    *,
    page: int = 1,
    page_size: int = 0,
    time_order: bool = False,
    with_trackback: bool = True,
    trackback_position: int = 0,
) -> dict[str, Any]:
    """Port of ``lbsArticle.loadComments`` (comments merged with trackbacks)."""
    sql = (
        "SELECT 0 AS type, comm_id, comm_content, comm_authorID, comm_author, "
        "comm_postTime, comm_editMark, comm_ubbFlags, comm_hidden, comm_ip "
        "FROM blog_Comment WHERE log_id = ?"
    )
    params: list[Any] = [article_id]
    if with_trackback:
        sql += (
            " UNION ALL SELECT 1, 0, tb_excerpt, tb_id, tb_title, tb_time, "
            "tb_url, tb_blog, 0, tb_ip FROM blog_Trackback WHERE log_id = ?"
        )
        params.append(article_id)

    sql += " ORDER BY"
    if with_trackback and int(trackback_position) == 1:
        sql += " type DESC,"
    elif with_trackback and int(trackback_position) == 2:
        sql += " type ASC,"
    sql += " comm_postTime DESC" if time_order else " comm_postTime ASC"

    total = int(db.scalar(conn, f"SELECT COUNT(*) FROM ({sql})", params) or 0)
    if page_size and page_size > 0:
        sql += " LIMIT ? OFFSET ?"
        params.extend([page_size, (max(page, 1) - 1) * page_size])

    entries = []
    for row in db.query_all(conn, sql, params):
        data = dict(row)
        if int(data["type"]) == 0:
            entries.append(
                {
                    "type": 0,
                    "id": int(data["comm_id"] or 0),
                    "content_html": render(
                        conn,
                        utils.html_encode(data["comm_content"] or ""),
                        data["comm_ubbFlags"] or "111111",
                        nofollow=True,
                    ),
                    "author_id": int(data["comm_authorID"] or 0),
                    "author": data["comm_author"] or "",
                    "post_time": data["comm_postTime"] or "",
                    "edit_mark": data["comm_editMark"] or "",
                    "hidden": bool(data["comm_hidden"]),
                    "ip": data["comm_ip"] or "",
                }
            )
        else:
            entries.append(
                {
                    "type": 1,
                    "id": int(data["comm_authorID"] or 0),
                    "excerpt": data["comm_content"] or "",
                    "title": data["comm_author"] or "",
                    "post_time": data["comm_postTime"] or "",
                    "ip": data["comm_ip"] or "",
                    "url": data["comm_editMark"] or "",
                    "blog": data["comm_ubbFlags"] or "",
                }
            )
    return {
        "items": entries,
        "total": total,
        "page": max(int(page or 1), 1),
        "page_size": int(page_size or 0),
    }


def recent_articles(
    conn: sqlite3.Connection, viewer: "dict | None", limit: int
) -> list[dict[str, Any]]:
    clauses, params = build_filters(conn, viewer)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.query_all(
        conn,
        f"SELECT log_id, log_title FROM blog_Article{where} "
        "ORDER BY log_postTime DESC LIMIT ?",
        [*params, limit],
    )
    return [
        {"id": int(row["log_id"]), "title": row["log_title"] or ""}
        for row in rows
    ]


def recent_comments(
    conn: sqlite3.Connection, viewer: "dict | None", limit: int
) -> list[dict[str, Any]]:
    rows = db.query_all(
        conn,
        "SELECT tComm.comm_id, tComm.log_id, tComm.comm_author, tComm.comm_content, "
        "tComm.comm_hidden, tComm.comm_postTime, tLog.log_title, tLog.log_mode, "
        "tCat.cat_hidden, tComm.comm_ubbFlags "
        "FROM blog_Article tLog, blog_Comment tComm, blog_Category tCat "
        "WHERE tLog.log_id = tComm.log_id AND tLog.log_catID = tCat.cat_id "
        "ORDER BY tComm.comm_postTime DESC LIMIT ?",
        (limit * 4,),
    )
    rights = (viewer or {}).get("rights") or users.parse_rights("11110")
    view = int(rights.get("view", 0))
    logged_in = bool(viewer)

    results = []
    for row in rows:
        mode = int(row["log_mode"] or 1)
        hidden = bool(row["comm_hidden"])
        cat_hidden = bool(row["cat_hidden"])
        visible = (
            (mode == 1 and (hidden or cat_hidden) and view > 1)
            or (mode == 1 and not hidden and not cat_hidden and view > 0)
            or (mode == 2 and not hidden and not cat_hidden and logged_in and view > 0)
            or (mode == 3 and logged_in and view > 1)
            or (mode == 4 and logged_in and view > 2)
        )
        results.append(
            {
                "id": int(row["comm_id"]),
                "article_id": int(row["log_id"]),
                "author": row["comm_author"] or "",
                "article_title": row["log_title"] or "",
                "visible": visible,
                "excerpt": utils.cut_string(
                    utils.trim_ubb(row["comm_content"] or ""), 24
                ),
                "title_excerpt": utils.cut_string(
                    utils.trim_ubb(row["comm_content"] or ""), 300
                ),
            }
        )
        if len(results) >= limit:
            break
    return results


# ---------------------------------------------------------------------------
# Write paths (port of lbsArticle.fillFromPost / insert / update / doDelete)
# ---------------------------------------------------------------------------


def ubb_flags_from_form(payload: dict, *, comment: bool = False) -> str:
    """Build the six character UBB flag string from the form checkboxes."""
    if payload.get("e_html") and not comment:
        return "html"
    flags = ""
    flags += "1" if payload.get("e_ubb") else "0"
    flags += "1" if payload.get("e_autourl") else "0"
    flags += "2" if comment else ("1" if payload.get("e_image") else "0")
    flags += "2" if comment else ("1" if payload.get("e_media") else "0")
    flags += "1" if payload.get("e_smilies") else "0"
    flags += "1"  # bTextBlock, always on
    return flags


def _split_pos(text: str, chars: int):
    """Port of getSplitPos: snap the cut to a space, UBB tag or newline."""
    if len(text) <= chars or chars == 0:
        return None
    if len(text) <= chars + 50:
        return None
    index = text.find(" ", max(chars - 10, 0))
    if -1 < index < chars + 30:
        chars = index + 1
    index = text.find("[/", max(chars - 10, 0))
    if index > -1:
        index = text.find("]", index)
    if -1 < index < chars + 30:
        chars = index + 1
    index = text.find("\n", max(chars - 10, 0))
    if -1 < index < chars + 30:
        chars = index + 1
    return chars


def _split_pos_html(text: str, chars: int):
    """Port of getSplitPosHTML: keep the cut outside of tags."""
    if len(text) <= chars or chars == 0:
        return None
    if len(text) <= chars + 80:
        return None
    chars += chars - len(utils.trim_html(text[:chars]))
    index = text.find(" ", max(chars - 10, 0))
    if -1 < index < chars + 30:
        chars = index + 1
    index = text.find("<br/>", max(chars - 10, 0))
    if -1 < index < chars + 30:
        chars = index + 5
    index = text.find("</", max(chars - 10, 0))
    if index > -1:
        index = text.find(">", index)
    if -1 < index < chars + 30:
        chars = index + 1
    return chars


def split_content(
    conn: sqlite3.Connection, content: str, *, html: bool
) -> "tuple[str, str]":
    """Split at ``[separator]`` or at the configured auto split point."""
    position = content.find("[separator]")
    if position > 0:
        return content[:position], content[position:]
    if not settings_module.get_flag(conn, "enableContentAutoSplit"):
        return content, ""
    limit = settings_module.get_int(conn, "contentAutoSplitChars", 400)
    position = _split_pos_html(content, limit) if html else _split_pos(content, limit)
    if position:
        return content[:position], content[position:]
    return content, ""


def validate_article_form(
    conn: sqlite3.Connection, payload: dict
) -> "tuple[dict[str, Any] | None, list[str]]":
    """Port of ``lbsArticle.fillFromPost``; returns (fields, errors)."""
    errors: list[str] = []
    title = utils.trim_text(payload.get("log_title") or "")
    content = utils.trim_text(payload.get("message") or payload.get("content") or "")
    category_id = utils.check_int(payload.get("log_catid"))
    mode = utils.check_int(payload.get("log_mode"))

    if not title or not category_id or not content:
        errors.append("form_incomplete")
    if not cache.get_category(cache.categories(conn), category_id)["id"]:
        errors.append("invalid_cat")
    if mode == 0:
        errors.append("invalid_mode")
    if not 1 <= len(title) <= 255:
        errors.append("title_invalid")

    flags = ubb_flags_from_form(payload)
    if flags == "html":
        content = utils.close_html(utils.clean_html(content))
    if len(content) < 2:
        errors.append("content_blank")
    if errors:
        return None, errors

    content0, content1 = split_content(conn, content, html=flags == "html")
    return (
        {
            "log_catID": category_id,
            "log_title": title,
            "log_content0": content0,
            "log_content1": content1,
            "log_mode": mode,
            "log_locked": 1 if payload.get("log_locked") else 0,
            "log_selected": 1 if payload.get("log_selected") else 0,
            "log_ubbFlags": flags,
            "log_trackbackURL": utils.trim_text(payload.get("log_trackbackurl") or ""),
            "log_postTime": utils.get_date_time_string(
                "YY-MM-DD hh:ii:ss",
                utils.parse_date_time(payload.get("log_postTime")) if payload.get("log_postTime") else None,
            ),
        },
        errors,
    )


def create_article(
    conn: sqlite3.Connection, fields: dict[str, Any], author: dict[str, Any]
) -> int:
    values = dict(fields)
    values.update(
        {
            "log_authorID": author["id"],
            "log_author": author["name"],
            "log_ip": (author.get("ip") or "")[:15],
            "log_commentCount": 0,
            "log_viewCount": 0,
            "log_trackbackCount": 0,
            "log_editMark": "",
        }
    )
    article_id = db.insert(conn, "blog_Article", values)
    settings_module.bump(conn, "counterArticle", 1)
    conn.execute(
        "UPDATE blog_User SET user_articleCount = user_articleCount + 1 WHERE user_id = ?",
        (author["id"],),
    )
    conn.execute(
        "UPDATE blog_Category SET cat_articleCount = cat_articleCount + 1 WHERE cat_id = ?",
        (fields["log_catID"],),
    )
    conn.commit()
    cache.invalidate()
    return article_id


def update_article(
    conn: sqlite3.Connection, article_id: int, fields: dict[str, Any], author: dict[str, Any]
) -> None:
    values = dict(fields)
    values["log_ip"] = (author.get("ip") or "")[:15]
    values["log_editMark"] = (
        f"{author['name']}$|${utils.get_date_time_string(None, None)}"
    )
    previous = db.query_one(
        conn, "SELECT log_catID FROM blog_Article WHERE log_id = ?", (article_id,)
    )
    if previous is None:
        raise ValueError("article_not_found")
    db.update(conn, "blog_Article", values, "log_id = ?", (article_id,))
    new_category = int(fields["log_catID"])
    old_category = int(previous["log_catID"] or 0)
    if new_category != old_category:
        conn.execute(
            "UPDATE blog_Category SET cat_articleCount = MAX(cat_articleCount - 1, 0) "
            "WHERE cat_id = ?",
            (old_category,),
        )
        conn.execute(
            "UPDATE blog_Category SET cat_articleCount = cat_articleCount + 1 "
            "WHERE cat_id = ?",
            (new_category,),
        )
    conn.commit()
    cache.invalidate()


def delete_article(conn: sqlite3.Connection, article_id: int) -> None:
    row = db.query_one(
        conn, "SELECT log_catID, log_authorID FROM blog_Article WHERE log_id = ?",
        (article_id,),
    )
    if row is None:
        raise ValueError("article_not_found")
    conn.execute("DELETE FROM blog_Article WHERE log_id = ?", (article_id,))
    conn.execute("DELETE FROM blog_Comment WHERE log_id = ?", (article_id,))
    conn.execute("DELETE FROM blog_Trackback WHERE log_id = ?", (article_id,))
    conn.execute(
        "UPDATE blog_Category SET cat_articleCount = MAX(cat_articleCount - 1, 0) "
        "WHERE cat_id = ?",
        (int(row["log_catID"] or 0),),
    )
    conn.execute(
        "UPDATE blog_User SET user_articleCount = MAX(user_articleCount - 1, 0) "
        "WHERE user_id = ?",
        (int(row["log_authorID"] or 0),),
    )
    settings_module.bump(conn, "counterArticle", -1)
    conn.commit()
    cache.invalidate()
