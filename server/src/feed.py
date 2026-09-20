"""RSS 2.0 and JavaScript feeds (source/src_feed.asp)."""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import articles
import cache
import db
import lang
import settings as settings_module
import utils

VERSION = "2.0.304"
RSS_DATE = "w, DD m YY hh:ii:ss Z"


def _cdata(value: Any) -> str:
    return "<![CDATA[" + str(value or "") + "]]>"


def _hidden_categories(conn: sqlite3.Connection) -> list[int]:
    return [row["id"] for row in cache.categories(conn) if row["hidden"]]


def _channel_head(
    conn: sqlite3.Connection, encoding: str, *, with_wfw: bool = False
) -> str:
    values = cache.settings(conn)
    title = values.get("blogTitle", "")
    base_url = values.get("baseURL", "")
    rss_open = '<rss version="2.0" xmlns:wfw="http://wellformedweb.org/CommentAPI/">' \
        if with_wfw else '<rss version="2.0">'
    return (
        '<?xml version="1.0" encoding="' + encoding + '"?>\n'
        + rss_open + "\n"
        "  <channel>\n"
        f"    <title>{_cdata(title)}</title> \n"
        f"    <link>{base_url}</link> \n"
        f"    <description>{_cdata(values.get('blogDescription', ''))}</description> \n"
        f"    <language>{values.get('blogLanguage', '')}</language> \n"
        f"    <copyright>{_cdata('Copyright ' + utils.get_date_time_string('YY') + ', ' + str(title))}</copyright> \n"
        f"    <webMaster>{_cdata(str(values.get('blogWebMasterEmail', '')) + ' (' + str(values.get('blogWebMaster', '')) + ')')}</webMaster> \n"
        f"    <generator>LBS v{VERSION}</generator> \n"
        f"    <pubDate>{utils.get_date_time_string(RSS_DATE, None, True)}</pubDate> \n"
        "    <ttl>60</ttl>\n"
    )


def article_feed(
    conn: sqlite3.Connection,
    *,
    category: int = 0,
    selected: bool = False,
    limit: int = 10,
) -> str:
    """Port of ``outputRSS2``."""
    values = cache.settings(conn)
    base_url = values.get("baseURL", "")
    clauses = ["tLog.log_mode = 1"]
    params: list[Any] = []
    for hidden in _hidden_categories(conn):
        clauses.append("tLog.log_catID <> ?")
        params.append(hidden)
    if category:
        clauses.append("tLog.log_catID = ?")
        params.append(category)
    if selected:
        clauses.append("tLog.log_selected = 1")

    rows = db.query_all(
        conn,
        "SELECT tLog.log_id, tLog.log_catID, tLog.log_title, tLog.log_author, "
        "tLog.log_ubbFlags, tLog.log_postTime, tLog.log_content0 "
        "FROM blog_Article tLog WHERE " + " AND ".join(clauses) +
        " ORDER BY tLog.log_postTime DESC LIMIT ?",
        [*params, limit],
    )
    renderer = articles.renderer(conn)
    parts = [_channel_head(conn, "utf-8", with_wfw=True)]
    for row in rows:
        data = dict(row)
        category_info = cache.get_category(
            cache.categories(conn), int(data["log_catID"] or 0)
        )
        flags = data["log_ubbFlags"] or "111111"
        if flags == "html":
            description = data["log_content0"] or ""
        else:
            description = renderer.to_html(
                utils.close_ubb(utils.html_encode(data["log_content0"] or "")),
                flags,
                base_url,
            )
        parts.append(
            "    <item>\n"
            f"      <title>{_cdata(utils.html_encode(data['log_title'] or ''))}</title> \n"
            f"      <link>{_cdata(base_url + 'article.asp?id=' + str(data['log_id']))}</link> \n"
            f"      <category>{_cdata(category_info['name'])}</category> \n"
            f"      <author>{_cdata(str(data['log_author'] or '') + ' <null@null.com>')}</author> \n"
            f"      <pubDate>{utils.get_date_time_string(RSS_DATE, data['log_postTime'], True)}</pubDate> \n"
            f"      <description>{_cdata(description)}</description>\n"
            "      <wfw:commentRss>"
            f"{_cdata(base_url + 'feed.asp?q=comment&id=' + str(data['log_id']))}"
            "</wfw:commentRss>\n"
            "    </item>\n"
        )
    parts.append("  </channel>\n</rss>\n")
    return "".join(parts)


def comment_feed(
    conn: sqlite3.Connection, *, article_id: int = 0, limit: int = 10
) -> str:
    """Port of ``outputCommentRSS2``."""
    values = cache.settings(conn)
    base_url = values.get("baseURL", "")
    clauses = ["tLog.log_mode = 1", "tComm.comm_hidden = 0"]
    params: list[Any] = []
    if article_id:
        clauses.append("tLog.log_id = ?")
        params.append(article_id)
    for hidden in _hidden_categories(conn):
        clauses.append("tLog.log_catID <> ?")
        params.append(hidden)
    rows = db.query_all(
        conn,
        "SELECT tComm.comm_id, tComm.log_id, tComm.comm_author, tComm.comm_content, "
        "tComm.comm_postTime, tComm.comm_ubbFlags, tLog.log_title "
        "FROM blog_Article tLog, blog_Comment tComm "
        "WHERE tLog.log_id = tComm.log_id AND " + " AND ".join(clauses) +
        " ORDER BY tComm.comm_postTime DESC LIMIT ?",
        [*params, limit],
    )
    renderer = articles.renderer(conn)
    parts = [_channel_head(conn, "utf-8")]
    for row in rows:
        data = dict(row)
        description = renderer.to_html(
            utils.close_ubb(utils.html_encode(data["comm_content"] or "")),
            data["comm_ubbFlags"] or "111111",
            base_url,
        )
        parts.append(
            "    <item>\n"
            f"      <title>{_cdata(lang.text('comment_on') + ': ' + utils.html_encode(data['log_title'] or ''))}</title> \n"
            f"      <link>{_cdata(base_url + 'article.asp?id=' + str(data['log_id']) + '#comment' + str(data['comm_id']))}</link> \n"
            f"      <author>{_cdata(str(data['comm_author'] or '') + ' <null@null.com>')}</author> \n"
            f"      <pubDate>{utils.get_date_time_string(RSS_DATE, data['comm_postTime'], True)}</pubDate> \n"
            f"      <description>{_cdata(description)}</description>\n"
            "    </item>\n"
        )
    parts.append("  </channel>\n</rss>\n")
    return "".join(parts)


def js_feed(
    conn: sqlite3.Connection, *, category: int = 0, selected: bool = False, limit: int = 10
) -> str:
    """Port of ``outputJS``."""
    values = cache.settings(conn)
    base_url = values.get("baseURL", "")
    clauses = ["tLog.log_mode = 1"]
    params: list[Any] = []
    for hidden in _hidden_categories(conn):
        clauses.append("tLog.log_catID <> ?")
        params.append(hidden)
    if category:
        clauses.append("tLog.log_catID = ?")
        params.append(category)
    if selected:
        clauses.append("tLog.log_selected = 1")
    rows = db.query_all(
        conn,
        "SELECT tLog.log_id, tLog.log_catID, tLog.log_title, tLog.log_author "
        "FROM blog_Article tLog WHERE " + " AND ".join(clauses) +
        " ORDER BY tLog.log_postTime DESC LIMIT ?",
        [*params, limit],
    )
    lines = [f"// LBS v{VERSION} Javascript Output"]
    for row in rows:
        data = dict(row)
        category_info = cache.get_category(
            cache.categories(conn), int(data["log_catID"] or 0)
        )
        title = utils.html_encode(data["log_title"] or "")
        lines.append(
            'document.write("<a href=\\"' + base_url + 'article.asp?id=' +
            str(data["log_id"]) + '\\" title=\\"[' + category_info["name"] + '] ' +
            title + " - " + str(data["log_author"] or "") + '\\">' + title +
            '</a><br />");'
        )
    return "\n".join(lines) + "\n"
