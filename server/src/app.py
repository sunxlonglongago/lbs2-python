#!/usr/bin/env python3
"""LBS^2 web application.

Flask + SQLite port of the original ASP code. The public frontend is served
from ``static/``; every dynamic value comes from the ``/api/*`` endpoints.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session

import admin
import articles
import auth
import cache
import calendar_view
import comments
import config
import db
import feed as feed_module
import guestbook
import lang
import settings as settings_module
import state
import stats as stats_module
import trackback as trackback_module
import uploads
import utils
import users
import visitors

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def parse_runtime_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LBS^2 web server")
    parser.add_argument(
        "--data",
        required=True,
        help="runtime data directory holding the SQLite database and secrets",
    )
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5059")))
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    return args


runtime_args = parse_runtime_args()
DATA_DIR = config.set_data_dir(runtime_args.data)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
auth.init_auth(app)

STATIC_PREFIXES = ("/static/", "/styles/", "/js/", "/uploads/", "/favicon.ico")


class AspPathMiddleware:
    """Let every route be addressed as ``*.asp``, keeping the original ASP look.

    The files on disk stay ``.html``; the trailing ``.asp`` is removed before
    routing: ``/api/articles.asp`` → ``/api/articles``, ``/article.asp`` →
    ``/article``, ``/upload.asp`` → ``/upload``. No ``.html`` page URL is
    exposed.
    """

    SUFFIX = ".asp"

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.lower().endswith(self.SUFFIX):
            stripped = path[: -len(self.SUFFIX)]
            environ["PATH_INFO"] = stripped or "/"
        return self.wsgi_app(environ, start_response)


app.wsgi_app = AspPathMiddleware(app.wsgi_app)


@app.before_request
def track_visitor():
    """Record a page view and refresh the online counter (port of _common.asp)."""
    if request.method != "GET" or request.path.startswith("/api/"):
        return None
    if request.path.startswith(STATIC_PREFIXES):
        return None
    with db.connection() as conn:
        db.ensure_schema(conn)
        visitors.touch_online(session)
        if settings_module.get_flag(conn, "enableVisitorRecord", True) and not session.get(
            "recorded"
        ):
            target = request.path
            if request.query_string:
                target += "?" + request.query_string.decode("utf-8", "replace")
            visitors.record_visit(
                conn,
                ip=request.remote_addr or "",
                user_agent=request.headers.get("User-Agent", ""),
                referer=request.headers.get("Referer", ""),
                target=target[:50],
                max_records=settings_module.get_int(conn, "maxVisitorRecord", 100),
            )
            session["recorded"] = True
    return None


def site_closed() -> bool:
    return state.site_closed()


@app.get("/api/health")
def api_health():
    with db.connection() as conn:
        db.ensure_schema(conn)
        counters = settings_module.counters(conn)
    return jsonify({"ok": True, "counters": counters})


def _sidebar(conn, viewer) -> dict:
    values = cache.settings(conn)
    today = dt.date.today()
    return {
        "categories": [
            category
            for category in cache.categories(conn)
            if not category["hidden"] or (viewer and viewer["rights"]["view"] > 1)
        ],
        "recent_articles": articles.recent_articles(
            conn, viewer, int(values.get("recentArticleList") or 0)
        ),
        "recent_comments": articles.recent_comments(
            conn, viewer, int(values.get("recentCommentList") or 0)
        ),
        "calendar_html": calendar_view.generate_calendar(
            conn, today.year, today.month, today=today
        ),
        "smilies": cache.smilies(conn),
        "smilies_per_row": int(values.get("smiliesPerRow") or 4),
    }


def _announcement(conn) -> dict:
    """Port of the announcement block in default.asp."""
    values = cache.settings(conn)
    body = values.get("announce") or ""
    flags = values.get("announceUBBFlags") or "111111"
    if flags != "html":
        body = articles.render(conn, utils.html_encode(body), flags)
    return {
        "show": int(values.get("announceShow") or 0) == 1,
        "date": values.get("announceDate") or "",
        "html": body,
    }


@app.get("/api/site")
def api_site():
    """Public site metadata: titles, theme files, counters."""
    with db.connection() as conn:
        db.ensure_schema(conn)
        values = cache.settings(conn)
        counters = settings_module.counters(conn)
        user = auth.current_user()
        sidebar = _sidebar(conn, user)
    return jsonify(
        {
            "ok": True,
            "site": {
                "title": values.get("blogTitle", ""),
                "description": values.get("blogDescription", ""),
                "language": values.get("blogLanguage", "en"),
                "base_url": values.get("baseURL", ""),
                "webmaster": values.get("blogWebMaster", ""),
                "webmaster_email": values.get("blogWebMasterEmail", ""),
                "style_sheet": values.get("styleSheet", ""),
                "image_folder": values.get("imageFolder", ""),
                "smilies_folder": values.get("smiliesFolder", ""),
                "logo_image": values.get("logoImage", ""),
                "links": values.get("links", ""),
                "closed": site_closed(),
                "features": {
                    "comment": bool(values.get("enableComment", 0)),
                    "guestbook": bool(values.get("enableGuestBook", 0)),
                    "register": bool(values.get("enableRegister", 0)),
                    "security_code": bool(values.get("enableSecurityCode", 0)),
                    "upload": bool(values.get("enableUpload", 0)),
                    "trackback_in": bool(values.get("enableTrackbackIn", 0)),
                    "trackback_out": bool(values.get("enableTrackbackOut", 0)),
                },
            },
            "counters": counters,
            "online": visitors.online_count(),
            "sidebar": sidebar,
            "announcement": _announcement(conn),
            "user": user,
        }
    )


@app.get("/api/lang")
def api_lang():
    return jsonify({"ok": True, "strings": lang.STRINGS})


def _url_prefix(args) -> str:
    """Rebuild ``strURLPrefix`` from src_default.asp."""
    parts: list[str] = []
    if args.get("selected") == "true":
        parts.append("selected=true")
    if utils.check_int(args.get("cat")) > 0:
        parts.append(f"cat={utils.check_int(args.get('cat'))}")
    if utils.check_int(args.get("user")) > 0:
        parts.append(f"user={utils.check_int(args.get('user'))}")
    if args.get("q"):
        parts.append(f"q={args['q']}")
    if args.get("hl"):
        parts.append(f"hl={args['hl']}")
    if args.get("date"):
        parts.append(f"date={args['date']}")
    return "?" + "&amp;".join(parts) if parts else "?"


def _date_parts(raw: str) -> "tuple[int, int, int]":
    pieces = [utils.check_int(piece) for piece in str(raw or "").split("-")[:3]]
    while len(pieces) < 3:
        pieces.append(0)
    year, month, day = pieces
    if not 0 < month < 13:
        month = 0
    if not 0 < day < 32:
        day = 0
    return year, month, day


@app.get("/api/articles")
def api_articles():
    args = request.args
    mode = 1 if args.get("mode") == "list" else 0
    page = max(utils.check_int(args.get("page")) or 1, 1)
    selected = args.get("selected") == "true"
    keywords = (args.get("q") or "").split(" ") if args.get("q") else []
    year, month, day = _date_parts(args.get("date", ""))

    with db.connection() as conn:
        viewer = auth.current_user()
        result = articles.list_articles(
            conn,
            viewer=viewer,
            mode=mode,
            page=page,
            category=utils.check_int(args.get("cat")),
            author=utils.check_int(args.get("user")),
            selected=selected,
            keywords=keywords,
            year=year,
            month=month,
            day=day,
        )
        highlight_words = (
            (args.get("hl") or args.get("q") or "").split(" ")
            if (args.get("hl") or args.get("q"))
            else []
        )
        if highlight_words:
            for item in result["items"]:
                item["title_html"] = utils.highlight(
                    utils.html_encode(item["title"]), highlight_words
                )
                if item.get("content_html"):
                    item["content_html"] = utils.highlight(
                        item["content_html"], highlight_words
                    )
        result["page_links"] = utils.generate_page_links(
            result["total"],
            result["page_size"],
            result["page"],
            15,
            _url_prefix(args),
        )
        result["filters"] = {
            "mode": "list" if mode else "normal",
            "category": utils.check_int(args.get("cat")),
            "author": utils.check_int(args.get("user")),
            "selected": selected,
            "keywords": keywords,
            "highlight": highlight_words,
            "date": args.get("date", ""),
        }
        return jsonify({"ok": True, **result})


@app.get("/api/articles/<int:article_id>")
def api_article(article_id: int):
    page = max(utils.check_int(request.args.get("page")) or 1, 1)
    with db.connection() as conn:
        db.ensure_schema(conn)
        viewer = auth.current_user()
        item = articles.get_article(conn, article_id, viewer)
        if item is None:
            return jsonify({"ok": False, "error": "article_not_found"}), 404

        values = cache.settings(conn)
        comment_page_size = int(values.get("commentPerPage") or 0)
        comments = articles.load_comments(
            conn,
            article_id,
            page=page,
            page_size=comment_page_size,
            time_order=int(values.get("commentTimeOrder") or 0) == 1,
            with_trackback=int(values.get("showTrackbackWithComment") or 0) == 1,
            trackback_position=int(values.get("showTrackbackPosition") or 0),
        )
        previous, following = articles.side_articles(conn, item, viewer)

        # The original increments the view counter while rendering article.asp.
        conn.execute(
            "UPDATE blog_Article SET log_viewCount = log_viewCount + 1 WHERE log_id = ?",
            (article_id,),
        )
        conn.commit()
        item["view_count"] += 1

        if comment_page_size > 0:
            comments["page_links"] = utils.generate_page_links(
                comments["total"], comment_page_size, page, 15,
                f"?id={article_id}",
                "#comments",
            )
        else:
            comments["page_links"] = ""

        return jsonify(
            {
                "ok": True,
                "article": item,
                "comments": comments,
                "previous": previous,
                "next": following,
                "can_comment": (
                    not item["locked"]
                    and not item["category"]["locked"]
                    and int(values.get("enableComment") or 0) == 1
                ),
            }
        )


@app.get("/api/categories")
def api_categories():
    with db.connection() as conn:
        viewer = auth.current_user()
        categories = [
            category
            for category in cache.categories(conn)
            if not category["hidden"] or (viewer and viewer["rights"]["view"] > 1)
        ]
    return jsonify({"ok": True, "categories": categories})


@app.get("/api/archive")
def api_archive():
    year = utils.check_int(request.args.get("year"))
    month = utils.check_int(request.args.get("month"))
    if not 0 < month < 13 or not year:
        today = dt.date.today()
        year, month = today.year, today.month
    with db.connection() as conn:
        html = calendar_view.generate_calendar(conn, year, month)
    return jsonify({"ok": True, "year": year, "month": month, "html": html})


@app.get("/api/stats")
def api_stats():
    with db.connection() as conn:
        counters = settings_module.counters(conn)
        recent = db.query_all(
            conn,
            "SELECT vr_ip, vr_os, vr_browser, vr_time, vr_referer, vr_target "
            "FROM blog_VisitorRecord ORDER BY vr_time DESC LIMIT 20",
        )
    return jsonify(
        {
            "ok": True,
            "counters": counters,
            "visitors": [dict(row) for row in recent],
        }
    )


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def _logged_in_user():
    return auth.current_user()


def _errors_response(errors):
    return jsonify({"ok": False, "error": errors[0], "errors": errors}), 400


def _can_edit_article(user, article: dict) -> bool:
    return users.can_operate(
        user["rights"], "edit", owner=article["author_id"] == user["id"]
    )


def _can_delete_article(user, article: dict) -> bool:
    return users.can_operate(
        user["rights"], "delete", owner=article["author_id"] == user["id"]
    )


@app.post("/api/articles")
def api_article_create():
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    if user["rights"].get("post", 0) < 2:
        return jsonify({"ok": False, "error": "no_rights"}), 403
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        fields, errors = articles.validate_article_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        article_id = articles.create_article(conn, fields, user)
        # Port of the "send trackback on save" step in articleNew().
        trackback_result = None
        target = fields.get("log_trackbackURL") or ""
        if (
            target
            and int(fields.get("log_mode") or 0) == 1
            and settings_module.get_flag(conn, "enableTrackbackOut", True)
        ):
            base_url = settings_module.get_text(conn, "baseURL", "")
            error = trackback_module.send(
                target,
                url=base_url + "article.asp?id=" + str(article_id),
                title=fields["log_title"],
                excerpt=fields.get("log_content0") or "",
                blog_name=settings_module.get_text(conn, "blogTitle", ""),
            )
            trackback_result = {"sent": error is None, "error": error}
    return jsonify({"ok": True, "id": article_id, "trackback": trackback_result})


@app.patch("/api/articles/<int:article_id>")
def api_article_update(article_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        article = articles.get_article(conn, article_id, user)
        if article is None:
            return jsonify({"ok": False, "error": "article_not_found"}), 404
        if not _can_edit_article(user, article):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        fields, errors = articles.validate_article_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        articles.update_article(conn, article_id, fields, user)
    return jsonify({"ok": True, "id": article_id})


@app.delete("/api/articles/<int:article_id>")
def api_article_delete(article_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        article = articles.get_article(conn, article_id, user)
        if article is None:
            return jsonify({"ok": False, "error": "article_not_found"}), 404
        if not _can_delete_article(user, article):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        articles.delete_article(conn, article_id)
    return jsonify({"ok": True})


def _flood_check(conn) -> bool:
    """``True`` when the visitor may still post (port of the Session check)."""
    import time

    from flask import session

    window = settings_module.get_int(conn, "minPostDuration", 180) * 1000
    last = session.get("flood_control")
    now_ms = time.time() * 1000
    if last is not None and now_ms - float(last) < window:
        session["flood_control"] = now_ms
        return False
    return True


def _mark_posted():
    import time

    from flask import session

    session["flood_control"] = time.time() * 1000


@app.post("/api/articles/<int:article_id>/comments")
def api_comment_create(article_id: int):
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        db.ensure_schema(conn)
        if not settings_module.get_flag(conn, "enableComment", True):
            return jsonify({"ok": False, "error": "comment_disabled"}), 403
        viewer = _logged_in_user()
        rights = viewer["rights"] if viewer else users.parse_rights("11110")
        if int(rights.get("post", 0)) < 1:
            return jsonify({"ok": False, "error": "no_rights"}), 403
        if not _flood_check(conn):
            return jsonify({"ok": False, "error": "flood_control"}), 429

        article = articles.get_article(conn, article_id, viewer)
        if article is None:
            return jsonify({"ok": False, "error": "article_not_found"}), 404
        if article["locked"] or article["category"]["locked"]:
            return jsonify({"ok": False, "error": "comment_disabled"}), 403

        if viewer:
            author = {"id": viewer["id"], "name": viewer["name"]}
        else:
            author, error = comments.guest_identity(conn, payload)
            if error:
                return jsonify({"ok": False, "error": error}), 400

        fields, errors = comments.validate_comment_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        comment_id = comments.create_comment(
            conn, article_id, fields, author=author, ip=request.remote_addr or ""
        )
    _mark_posted()
    return jsonify({"ok": True, "id": comment_id})


def _comment_permission(conn, comment_id: int, user, capability: str) -> bool:
    row = db.query_one(
        conn,
        "SELECT c.comm_authorID, a.log_authorID FROM blog_Comment c "
        "JOIN blog_Article a ON a.log_id = c.log_id WHERE c.comm_id = ?",
        (comment_id,),
    )
    if row is None:
        return False
    owner = user["id"] in (
        int(row["comm_authorID"] or 0),
        int(row["log_authorID"] or 0),
    )
    return users.can_operate(user["rights"], capability, owner=owner)


@app.patch("/api/comments/<int:comment_id>")
def api_comment_update(comment_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        if not _comment_permission(conn, comment_id, user, "edit"):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        fields, errors = comments.validate_comment_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        comments.update_comment(conn, comment_id, fields, editor=user["name"])
    return jsonify({"ok": True, "id": comment_id})


@app.get("/api/comments")
def api_comments():
    """Comment list page (source/src_comment.asp default branch)."""
    args = request.args
    keywords = (args.get("q") or "").split(" ") if args.get("q") else []
    highlight_words = (
        (args.get("hl") or args.get("q") or "").split(" ")
        if (args.get("hl") or args.get("q"))
        else []
    )
    with db.connection() as conn:
        db.ensure_schema(conn)
        viewer = _logged_in_user()
        result = comments.list_comments(
            conn,
            viewer=viewer,
            page=utils.check_int(args.get("page")) or 1,
            category=utils.check_int(args.get("cat")),
            author=utils.check_int(args.get("user")),
            keywords=keywords,
            highlight_words=highlight_words,
        )
        result["filters"] = {"keywords": keywords, "highlight": highlight_words}
        result["page_links"] = utils.generate_page_links(
            result["total"], result["page_size"], result["page"], 15, "?",
        )
        return jsonify({"ok": True, **result})


@app.get("/api/comments/<int:comment_id>")
def api_comment(comment_id: int):
    """Single comment, used by the edit form."""
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        comment = comments.get_comment(conn, comment_id)
        if comment is None:
            return jsonify({"ok": False, "error": "comment_not_found"}), 404
        if not _comment_permission(conn, comment_id, user, "edit"):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        return jsonify({"ok": True, "comment": comment})


@app.delete("/api/comments/<int:comment_id>")
def api_comment_delete(comment_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        if not _comment_permission(conn, comment_id, user, "delete"):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        comments.delete_comment(conn, comment_id)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Guestbook
# ---------------------------------------------------------------------------


@app.get("/api/guestbook")
def api_guestbook():
    args = request.args
    keywords = (args.get("q") or "").split(" ") if args.get("q") else []
    highlight_words = (
        (args.get("hl") or args.get("q") or "").split(" ")
        if (args.get("hl") or args.get("q"))
        else []
    )
    with db.connection() as conn:
        db.ensure_schema(conn)
        if not settings_module.get_flag(conn, "enableGuestBook", True):
            return jsonify({"ok": False, "error": "gbook_disabled"}), 403
        viewer = _logged_in_user()
        result = guestbook.list_entries(
            conn,
            viewer=viewer,
            page=utils.check_int(args.get("page")) or 1,
            keywords=keywords,
            highlight_words=highlight_words,
        )
        result["filters"] = {
            "keywords": keywords,
            "highlight": highlight_words,
        }
        result["page_links"] = utils.generate_page_links(
            result["total"],
            result["page_size"],
            result["page"],
            15,
            f"?q={args.get('q')}&amp;" if args.get("q") else "?",
        )
        result["can_post"] = bool(
            settings_module.get_flag(conn, "enableComment", True)
        )
        return jsonify({"ok": True, **result})


@app.get("/api/guestbook/<int:entry_id>")
def api_guestbook_entry(entry_id: int):
    with db.connection() as conn:
        viewer = _logged_in_user()
        entry = guestbook.get_entry(conn, entry_id)
        if entry is None:
            return jsonify({"ok": False, "error": "comment_not_found"}), 404
        if not viewer or not guestbook.can_edit(entry, viewer):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        entry["show_reply_area"] = int(viewer["rights"].get("edit", 0)) > 2
        return jsonify({"ok": True, "entry": entry})


@app.post("/api/guestbook")
def api_guestbook_create():
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        db.ensure_schema(conn)
        if not settings_module.get_flag(conn, "enableGuestBook", True):
            return jsonify({"ok": False, "error": "gbook_disabled"}), 403
        if not settings_module.get_flag(conn, "enableComment", True):
            return jsonify({"ok": False, "error": "comment_disabled"}), 403
        viewer = _logged_in_user()
        rights = viewer["rights"] if viewer else users.parse_rights("11110")
        if int(rights.get("post", 0)) < 1:
            return jsonify({"ok": False, "error": "no_rights"}), 403
        if not _flood_check(conn):
            return jsonify({"ok": False, "error": "flood_control"}), 429

        if viewer:
            author = {"id": viewer["id"], "name": viewer["name"]}
        else:
            author, error = comments.guest_identity(conn, payload)
            if error:
                return jsonify({"ok": False, "error": error}), 400

        fields, errors = guestbook.validate_entry_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        entry_id = guestbook.create_entry(
            conn, fields, author=author, ip=request.remote_addr or ""
        )
    _mark_posted()
    return jsonify({"ok": True, "id": entry_id})


@app.patch("/api/guestbook/<int:entry_id>")
def api_guestbook_update(entry_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        entry = guestbook.get_entry(conn, entry_id)
        if entry is None:
            return jsonify({"ok": False, "error": "comment_not_found"}), 404
        if not guestbook.can_edit(entry, user):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        fields, errors = guestbook.validate_entry_form(conn, payload)
        if fields is None:
            return _errors_response(errors)
        guestbook.update_entry(
            conn,
            entry_id,
            fields,
            user=user,
            allow_reply=int(user["rights"].get("edit", 0)) > 1,
        )
    return jsonify({"ok": True, "id": entry_id})


@app.delete("/api/guestbook/<int:entry_id>")
def api_guestbook_delete(entry_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        entry = guestbook.get_entry(conn, entry_id)
        if entry is None:
            return jsonify({"ok": False, "error": "comment_not_found"}), 404
        if not guestbook.can_delete(entry, user):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        guestbook.delete_entry(conn, entry_id)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def _profile_payload(user: dict, viewer: "dict | None") -> dict:
    """Hide the email unless the viewer may see it (outputUserInfo rules)."""
    visible = bool(viewer) and (
        not user.get("hide_email") or (viewer and viewer["group_id"] == 1)
    )
    payload = dict(user)
    payload["email_visible"] = visible
    if not visible:
        payload["email"] = ""
    payload["is_admin"] = bool(viewer and viewer["group_id"] == 1)
    payload["can_edit"] = bool(
        viewer
        and (viewer["id"] == user["id"] or viewer["group_id"] == 1)
    )
    return payload


@app.get("/api/users")
def api_users():
    args = request.args
    with db.connection() as conn:
        db.ensure_schema(conn)
        viewer = _logged_in_user()
        size = settings_module.get_int(conn, "articlePerPageList", 40)
        result = users.list_users_page(
            conn, page=utils.check_int(args.get("page")) or 1, page_size=size
        )
        result["items"] = [_profile_payload(user, viewer) for user in result["items"]]
        result["page_links"] = utils.generate_page_links(
            result["total"], result["page_size"], result["page"], 15,
            f"?q={args.get('q')}&amp;" if args.get("q") else "?",
        )
        result["logged_in"] = bool(viewer)
        result["is_admin"] = bool(viewer and viewer["group_id"] == 1)
        return jsonify({"ok": True, **result})


@app.get("/api/users/<int:user_id>")
def api_user(user_id: int):
    with db.connection() as conn:
        db.ensure_schema(conn)
        viewer = _logged_in_user()
        user = users.public_user(conn, user_id)
        if user is None:
            return jsonify({"ok": False, "error": "user_not_found"}), 404
        payload = _profile_payload(user, viewer)
        payload["groups"] = [
            {"id": group["id"], "name": group["name"]}
            for group in cache.groups(conn).values()
        ]
        return jsonify({"ok": True, "user": payload})


@app.patch("/api/users/<int:user_id>")
def api_user_update(user_id: int):
    viewer = _logged_in_user()
    if not viewer:
        return jsonify({"ok": False, "error": "login_required"}), 401
    if not users.can_edit_profile(viewer, user_id):
        return jsonify({"ok": False, "error": "no_rights"}), 403
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        target = users.public_user(conn, user_id)
        if target is None:
            return jsonify({"ok": False, "error": "user_not_found"}), 404
        values, errors = users.validate_profile_form(
            conn, target, payload, editor=viewer
        )
        if values is None:
            return _errors_response(errors)
        updated = users.update_profile(conn, user_id, values)
        updated["groups"] = []
        return jsonify({"ok": True, "user": updated})


@app.delete("/api/users/<int:user_id>")
def api_user_delete(user_id: int):
    viewer = _logged_in_user()
    if not viewer:
        return jsonify({"ok": False, "error": "login_required"}), 401
    if not users.can_edit_profile(viewer, user_id):
        return jsonify({"ok": False, "error": "no_rights"}), 403
    with db.connection() as conn:
        try:
            users.delete_user(conn, user_id)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
    if viewer["id"] == user_id:
        session.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Admin backend (source/src_admin.asp)
# ---------------------------------------------------------------------------

ADMIN_KEY = "admin"


def _require_admin():
    """Group 1 plus the second admin login the ASP version requires."""
    user = auth.current_user()
    if not user or user["group_id"] != 1:
        return None, (jsonify({"ok": False, "error": "no_rights"}), 403)
    if not session.get(ADMIN_KEY):
        return None, (jsonify({"ok": False, "error": "admin_login"}), 403)
    return user, None


@app.post("/api/admin/login")
def api_admin_login():
    user = auth.current_user()
    if not user or user["group_id"] != 1:
        return jsonify({"ok": False, "error": "no_rights"}), 403
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password") or "")
    with db.connection() as conn:
        row = users.get_by_id(conn, user["id"])
        salt = (row["user_salt"] or "") if row else ""
        if row is None or row["user_password"] != users.hash_password(password, salt):
            session.pop(ADMIN_KEY, None)
            return jsonify({"ok": False, "error": "password_invalid"}), 401
    session[ADMIN_KEY] = True
    return jsonify({"ok": True})


@app.post("/api/admin/logout")
def api_admin_logout():
    session.pop(ADMIN_KEY, None)
    return jsonify({"ok": True})


@app.get("/api/admin/info")
def api_admin_info():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        db.ensure_schema(conn)
        counters = settings_module.counters(conn)
        info = admin.database_info(conn)
    return jsonify(
        {
            "ok": True,
            "software": "LBS^2 Python port (Flask)",
            "time": utils.get_date_time_string("YY-MM-DD hh:ii:ss Z", None),
            "data_dir": str(config.require_data_dir()),
            "database": info,
            "counters": counters,
            "site_closed": state.site_closed(),
            "online": visitors.online_count(),
            "admin": {"id": user["id"], "name": user["name"]},
        }
    )


@app.get("/api/admin/settings")
def api_admin_settings():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        values = settings_module.load_all(conn)
    return jsonify({"ok": True, "settings": values})


@app.post("/api/admin/settings")
def api_admin_settings_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        written = admin.update_settings(conn, payload)
    cache.invalidate()
    return jsonify({"ok": True, "written": written})


@app.get("/api/admin/categories")
def api_admin_categories():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        return jsonify({"ok": True, "categories": cache.categories(conn)})


@app.post("/api/admin/categories")
def api_admin_categories_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        result = admin.update_categories(conn, payload)
    cache.invalidate()
    return jsonify({"ok": True, **result})


@app.get("/api/admin/groups")
def api_admin_groups():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        rows = db.query_all(
            conn, "SELECT group_id, group_name, group_rights FROM blog_UserGroup "
            "ORDER BY group_id"
        )
    return jsonify(
        {
            "ok": True,
            "groups": [
                {
                    "id": int(row["group_id"]),
                    "name": row["group_name"] or "",
                    "rights": row["group_rights"] or "",
                    "levels": users.parse_rights(row["group_rights"] or ""),
                }
                for row in rows
            ],
        }
    )


@app.post("/api/admin/groups")
def api_admin_groups_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        result = admin.update_groups(conn, payload)
    cache.invalidate()
    return jsonify({"ok": True, **result})


@app.get("/api/admin/smilies")
def api_admin_smilies():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        return jsonify({"ok": True, "smilies": cache.smilies(conn)})


@app.post("/api/admin/smilies")
def api_admin_smilies_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        result = admin.update_smilies(conn, payload)
    cache.invalidate()
    return jsonify({"ok": True, **result})


@app.get("/api/admin/wordfilter")
def api_admin_wordfilter():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        return jsonify({"ok": True, "filters": cache.word_filters(conn)})


@app.post("/api/admin/wordfilter")
def api_admin_wordfilter_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        result = admin.update_word_filter(conn, payload)
    cache.invalidate()
    return jsonify({"ok": True, **result})


@app.get("/api/admin/database")
def api_admin_database():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        db.ensure_schema(conn)
        return jsonify({"ok": True, "database": admin.database_info(conn)})


@app.post("/api/admin/database")
def api_admin_database_action():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("act") or "")
    with db.connection() as conn:
        db.ensure_schema(conn)
        if action == "compact":
            state.set_site_closed(True)
            result = admin.compact_database(conn)
            state.set_site_closed(False)
            return jsonify({"ok": True, "action": action, **result})
        if action == "backup":
            result = admin.backup_database(conn)
            return jsonify({"ok": True, "action": action, **result})
        if action == "restore":
            if not admin.restore_database(conn, str(payload.get("file") or "")):
                return jsonify({"ok": False, "error": "error_occured"}), 400
            return jsonify({"ok": True, "action": action})
        if action == "delete":
            if not admin.delete_backup(str(payload.get("file") or "")):
                return jsonify({"ok": False, "error": "error_occured"}), 400
            return jsonify({"ok": True, "action": action})
    return jsonify({"ok": False, "error": "invalid_parameter"}), 400


@app.get("/api/admin/attachments")
def api_admin_attachments():
    user, error = _require_admin()
    if error:
        return error
    listing = admin.list_attachments(request.args.get("path", ""))
    return jsonify({"ok": True, **listing})


@app.post("/api/admin/attachments")
def api_admin_attachments_delete():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    deleted = admin.delete_attachment(
        str(payload.get("path") or ""), str(payload.get("name") or "")
    )
    if not deleted:
        return jsonify({"ok": False, "error": "error_occured"}), 400
    return jsonify({"ok": True})


@app.get("/api/admin/announce")
def api_admin_announce():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        values = settings_module.load_all(conn)
    return jsonify(
        {
            "ok": True,
            "announcement": {
                "show": int(values.get("announceShow") or 0) == 1,
                "message": values.get("announce") or "",
                "date": values.get("announceDate") or "",
                "ubb_flags": values.get("announceUBBFlags") or "111111",
            },
        }
    )


@app.post("/api/admin/announce")
def api_admin_announce_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    flags = articles.ubb_flags_from_form(payload)
    with db.connection() as conn:
        settings_module.put_many(
            conn,
            {
                "announceShow": 1 if payload.get("show") else 0,
                "announceUBBFlags": flags,
                "announce": str(payload.get("message") or ""),
                "announceDate": utils.get_date_time_string("YY-MM-DD hh:ii:ss", None),
            },
        )
    cache.invalidate()
    return jsonify({"ok": True})


@app.get("/api/admin/links")
def api_admin_links():
    user, error = _require_admin()
    if error:
        return error
    with db.connection() as conn:
        return jsonify({"ok": True, "links": settings_module.get_text(conn, "links", "")})


@app.post("/api/admin/links")
def api_admin_links_update():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    with db.connection() as conn:
        settings_module.put_many(conn, {"links": str(payload.get("links") or "")})
    cache.invalidate()
    return jsonify({"ok": True})


@app.post("/api/admin/misc")
def api_admin_misc():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("act") or "")
    with db.connection() as conn:
        db.ensure_schema(conn)
        if action == "resync_g":
            result = admin._resync_global(conn)
            conn.commit()
            cache.invalidate()
            return jsonify({"ok": True, "action": action, "counters": result})
        if action == "resync_c":
            count = admin.resync_categories(conn)
            cache.invalidate()
            return jsonify({"ok": True, "action": action, "processed": count})
        if action == "resync_a":
            result = admin.resync_article_stats(
                conn, start=utils.check_int(payload.get("start")) or 1
            )
            cache.invalidate()
            return jsonify({"ok": True, "action": action, **result})
        if action == "resync_u":
            result = admin.resync_user_stats(
                conn, start=utils.check_int(payload.get("start")) or 1
            )
            return jsonify({"ok": True, "action": action, **result})
        if action == "clean_u":
            return jsonify({"ok": True, "action": action,
                            "deleted": admin.clean_inactive_users(conn)})
        if action == "clean_vc":
            return jsonify({"ok": True, "action": action,
                            "deleted": admin.clean_visitor_records(conn)})
        if action == "clean_gb":
            return jsonify({"ok": True, "action": action,
                            "deleted": admin.clean_guestbook(conn)})
    return jsonify({"ok": False, "error": "invalid_parameter"}), 400


@app.post("/api/admin/site-state")
def api_admin_site_state():
    user, error = _require_admin()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    state.set_site_closed(bool(payload.get("closed")))
    return jsonify({"ok": True, "closed": state.site_closed()})


# ---------------------------------------------------------------------------
# Trackback (source/src_trackback.asp)
# ---------------------------------------------------------------------------


def _trackback_payload() -> dict:
    payload = dict(request.args)
    payload.update(request.form)
    body = request.get_json(silent=True)
    if isinstance(body, dict):
        payload.update(body)
    if "id" not in payload and "article" in payload:
        payload["id"] = payload["article"]
    return payload


def _trackback_response(error: int, message: "str | None" = None):
    body = trackback_module.response_xml(error, message)
    response = app.response_class(body, mimetype="text/xml")
    response.headers["Content-Type"] = "text/xml; charset=iso-8859-1"
    return response


@app.route("/trackback/<int:article_id>", methods=["GET", "POST"])
def trackback_ping(article_id: int):
    payload = _trackback_payload()
    payload.setdefault("id", article_id)
    with db.connection() as conn:
        db.ensure_schema(conn)
        if not settings_module.get_flag(conn, "enableTrackbackIn", True):
            return _trackback_response(1, "Trackback Disabled")
        if not payload.get("url"):
            return _trackback_response(1, "Invalid Parameter")
        error, message = trackback_module.receive(
            conn, payload, ip=request.remote_addr or ""
        )
    return _trackback_response(error, message)


@app.route("/trackback", methods=["GET", "POST"])
def trackback_entry():
    """``trackback.asp`` both receives pings and serves the list page, as in the original."""
    payload = _trackback_payload()
    is_ping = request.method == "POST" or bool(payload.get("url") or payload.get("id"))
    if not is_ping:
        return send_from_directory(STATIC_DIR, "trackback.html")
    if not payload.get("id") or not payload.get("url"):
        return _trackback_response(1, "Invalid Parameter")
    return trackback_ping(utils.check_int(payload.get("id")))


@app.get("/api/trackbacks")
def api_trackbacks():
    args = request.args
    keywords = (args.get("q") or "").split(" ") if args.get("q") else []
    highlight_words = (
        (args.get("hl") or args.get("q") or "").split(" ")
        if (args.get("hl") or args.get("q"))
        else []
    )
    with db.connection() as conn:
        db.ensure_schema(conn)
        viewer = _logged_in_user()
        result = trackback_module.list_trackbacks(
            conn,
            viewer=viewer,
            page=utils.check_int(args.get("page")) or 1,
            category=utils.check_int(args.get("cat")),
            article_id=utils.check_int(args.get("id")),
            keywords=keywords,
            highlight_words=highlight_words,
        )
        result["filters"] = {"keywords": keywords, "highlight": highlight_words}
        result["page_links"] = utils.generate_page_links(
            result["total"], result["page_size"], result["page"], 15, "?act=list",
        )
        return jsonify({"ok": True, **result})


@app.delete("/api/trackbacks/<int:trackback_id>")
def api_trackback_delete(trackback_id: int):
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        row = db.query_one(
            conn,
            "SELECT tTB.tb_id, tTB.log_id, tLog.log_authorID FROM blog_Article tLog, "
            "blog_Trackback tTB WHERE tLog.log_id = tTB.log_id AND tTB.tb_id = ?",
            (trackback_id,),
        )
        if row is None:
            return jsonify({"ok": False, "error": "trackback_not_found"}), 404
        if not trackback_module.can_delete(dict(row), user):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        article_id = trackback_module.delete_trackback(conn, trackback_id)
    return jsonify({"ok": True, "article_id": article_id})


# ---------------------------------------------------------------------------
# Feeds (source/src_feed.asp)
# ---------------------------------------------------------------------------


@app.get("/feed")
def feed_page():
    args = request.args
    with db.connection() as conn:
        db.ensure_schema(conn)
        if args.get("q") == "comment":
            body = feed_module.comment_feed(
                conn, article_id=utils.check_int(args.get("id"))
            )
        elif args.get("type") == "js":
            body = feed_module.js_feed(
                conn,
                category=utils.check_int(args.get("cat")),
                selected=args.get("selected") == "true",
            )
            return app.response_class(body, mimetype="text/javascript")
        else:
            body = feed_module.article_feed(
                conn,
                category=utils.check_int(args.get("cat")),
                selected=args.get("selected") == "true",
            )
    response = app.response_class(body, mimetype="text/xml")
    response.headers["Content-Type"] = "text/xml; charset=utf-8"
    return response


# ---------------------------------------------------------------------------
# Upload (upload.asp)
# ---------------------------------------------------------------------------


@app.post("/api/upload")
def api_upload():
    user = _logged_in_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401
    with db.connection() as conn:
        db.ensure_schema(conn)
        if int(user["rights"].get("upload", 0)) < 1:
            return jsonify({"ok": False, "error": "no_rights"}), 403
        if not settings_module.get_flag(conn, "enableUpload", True):
            return jsonify({"ok": False, "error": "no_rights"}), 403
        storage = request.files.get("File") or request.files.get("file")
        if storage is None:
            return jsonify({"ok": False, "error": "upload"}), 400
        info, error = uploads.store(conn, storage)
        if error:
            return jsonify({"ok": False, "error": error}), 400
    return jsonify({"ok": True, **info})


@app.get("/api/upload/limits")
def api_upload_limits():
    with db.connection() as conn:
        db.ensure_schema(conn)
        return jsonify(
            {
                "ok": True,
                "size": settings_module.get_int(conn, "uploadSize", 40000),
                "types": uploads.upload_types(conn),
                "enabled": settings_module.get_flag(conn, "enableUpload", True),
            }
        )


# ---------------------------------------------------------------------------
# Visitor statistics (source/src_stats.asp)
# ---------------------------------------------------------------------------


@app.get("/api/stats/visitors")
def api_stats_visitors():
    user = _logged_in_user()
    if not user or user["group_id"] != 1:
        return jsonify({"ok": False, "error": "no_rights"}), 403
    with db.connection() as conn:
        db.ensure_schema(conn)
        return jsonify({"ok": True, "visitors": stats_module.visitor_list(conn)})


@app.get("/uploads/<path:name>")
def uploaded_file(name: str):
    """Uploaded attachments live in the data directory, not in the static tree."""
    target = admin.resolve_upload(name)
    if target is None or not target.is_file():
        return jsonify({"ok": False, "error": "not_found"}), 404
    return send_from_directory(target.parent, target.name)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

# Old ASP entry points. The middleware strips ".asp", so /default.asp arrives
# here as "/default"; the dictionary is keyed by the bare page name.
LEGACY_PAGES = {
    "default": "index.html",
    "article": "article.html",
    "user": "user.html",
    "gbook": "gbook.html",
    "login": "login.html",
    "register": "register.html",
    "stats": "stats.html",
    "about": "about.html",
    "admin": "admin.html",
    "comment": "comment.html",
    "trackback": "trackback.html",
    "upload": "upload.html",
    "index": "index.html",
}

# Every .html address redirects to its .asp form; the real files come from LEGACY_PAGES.
PAGE_REDIRECTS = {
    "index.html": "default.asp",
    "article.html": "article.asp",
    "user.html": "user.asp",
    "gbook.html": "gbook.asp",
    "login.html": "login.asp",
    "register.html": "register.asp",
    "stats.html": "stats.asp",
    "about.html": "about.asp",
    "admin.html": "admin.asp",
    "comment.html": "comment.asp",
    "trackback.html": "trackback.asp",
    "upload.html": "upload.asp",
}


@app.get("/")
def index():
    """The root path keeps the .asp look too."""
    from flask import redirect

    return redirect("/default.asp", code=302)


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(STATIC_DIR, "favicon.ico")


@app.get("/<path:path>")
def static_or_page(path: str):
    """Serve a static asset, then ``<name>.html``, then the app shell."""
    name = path.rsplit("/", 1)[-1].lower()
    if name in PAGE_REDIRECTS:
        from flask import redirect

        target = "/" + PAGE_REDIRECTS[name]
        if request.query_string:
            target += "?" + request.query_string.decode("utf-8", "replace")
        return redirect(target, code=302)
    if (STATIC_DIR / path).is_file():
        return send_from_directory(STATIC_DIR, path)
    legacy = LEGACY_PAGES.get(name.split(".")[0])
    if legacy and (STATIC_DIR / legacy).is_file():
        return send_from_directory(STATIC_DIR, legacy)
    page = STATIC_DIR / f"{path}.html"
    if page.is_file():
        return send_from_directory(STATIC_DIR, page.name)
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "not_found"}), 404
    shell = STATIC_DIR / "index.html"
    if shell.is_file():
        return send_from_directory(STATIC_DIR, "index.html")
    return (
        "Frontend assets are missing. Run `make fe` to copy frontend/ into "
        "server/src/static/.",
        404,
    )


def main() -> int:
    db.ensure_schema(db.connect())
    app.run(host=runtime_args.host, port=runtime_args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
