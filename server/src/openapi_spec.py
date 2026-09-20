"""OpenAPI 3.1 description of the ported LBS^2 HTTP API.

Kept as a declarative table so ``docs/api.md`` and ``docs/openapi.json`` can be
regenerated with ``make docs`` whenever a route changes.
"""

from __future__ import annotations

from typing import Any

INFO = {
    "title": "LBS^2 (Python port) API",
    "version": "2.0.304",
    "description": (
        "HTTP API of the LBS^2 v2.0.304 port (ASP + JScript + Access) on Flask + SQLite. "
        "Table and column names match the original Access database, and permissions use the same five digit group_rights string."
    ),
}

SERVER = {"url": "/", "description": "frontend and API share one origin"}

TAGS = [
    {"name": "auth", "description": "login, logout, registration (auth.py / login.asp)"},
    {"name": "articles", "description": "article listing and writes (articles.py / default.asp, article.asp)"},
    {"name": "comments", "description": "comments (comments.py / comment.asp)"},
    {"name": "guestbook", "description": "guestbook (guestbook.py / gbook.asp)"},
    {"name": "trackback", "description": "trackbacks (trackback.py / trackback.asp)"},
    {"name": "users", "description": "user profiles and listing (users.py / user.asp)"},
    {"name": "site", "description": "site metadata, language pack, statistics, feeds (app.py, feed.py)"},
    {"name": "upload", "description": "attachments (uploads.py / upload.asp)"},
    {"name": "admin", "description": "admin backend (admin.py / admin.asp); needs an administrator past the second login"},
]

SCHEMAS: dict[str, Any] = {
    "ApiError": {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean", "const": False},
            "error": {"type": "string", "description": "language string key, translated by the frontend through /api/lang"},
            "errors": {"type": "array", "items": {"type": "string"}},
        },
    },
    "Category": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "order": {"type": "integer"},
            "article_count": {"type": "integer"},
            "hidden": {"type": "boolean"},
            "locked": {"type": "boolean"},
        },
    },
    "Rights": {
        "type": "object",
        "description": "the five group_rights digits expanded; 0 none, 1 own objects, 2 everything",
        "properties": {
            "view": {"type": "integer"},
            "post": {"type": "integer"},
            "edit": {"type": "integer"},
            "delete": {"type": "integer"},
            "upload": {"type": "integer"},
        },
    },
    "User": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "group_id": {"type": "integer"},
            "group_name": {"type": "string"},
            "gender": {"type": "integer"},
            "email": {"type": "string"},
            "email_visible": {"type": "boolean"},
            "hide_email": {"type": "boolean"},
            "homepage": {"type": "string"},
            "article_count": {"type": "integer"},
            "comment_count": {"type": "integer"},
            "last_visit": {"type": "string"},
            "ip": {"type": "string"},
            "rights": {"$ref": "#/components/schemas/Rights"},
        },
    },
    "Article": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "title_html": {"type": "string", "description": "title with search highlighting applied"},
            "author": {"type": "string"},
            "author_id": {"type": "integer"},
            "category": {"$ref": "#/components/schemas/Category"},
            "mode": {"type": "integer", "description": "1 public, 2 draft, 3 hidden, 4 private"},
            "locked": {"type": "boolean"},
            "selected": {"type": "boolean"},
            "ubb_flags": {"type": "string"},
            "post_time": {"type": "string"},
            "ip": {"type": "string"},
            "comment_count": {"type": "integer"},
            "trackback_count": {"type": "integer"},
            "view_count": {"type": "integer"},
            "content_html": {"type": "string", "description": "server rendered body"},
            "content_raw": {"type": "string", "description": "only on the detail endpoint, for the edit form"},
            "has_more": {"type": "boolean"},
        },
    },
    "ArticleForm": {
        "type": "object",
        "required": ["log_catid", "log_mode", "log_title", "message"],
        "properties": {
            "log_catid": {"type": "integer"},
            "log_mode": {"type": "integer", "enum": [1, 2, 3, 4]},
            "log_title": {"type": "string"},
            "message": {"type": "string", "description": "body; a [separator] token splits it by hand"},
            "log_postTime": {"type": "string"},
            "log_trackbackurl": {"type": "string"},
            "log_locked": {"type": "boolean"},
            "log_selected": {"type": "boolean"},
            "e_html": {"type": "boolean"},
            "e_ubb": {"type": "boolean"},
            "e_autourl": {"type": "boolean"},
            "e_image": {"type": "boolean"},
            "e_media": {"type": "boolean"},
            "e_smilies": {"type": "boolean"},
        },
    },
    "Comment": {
        "type": "object",
        "properties": {
            "type": {"type": "integer", "description": "0 comment, 1 trackback"},
            "id": {"type": "integer"},
            "author": {"type": "string"},
            "author_id": {"type": "integer"},
            "post_time": {"type": "string"},
            "content_html": {"type": "string"},
            "hidden": {"type": "boolean"},
            "ip": {"type": "string"},
        },
    },
    "GuestbookEntry": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "user_id": {"type": "integer"},
            "username": {"type": "string"},
            "content_html": {"type": "string"},
            "reply_html": {"type": "string"},
            "has_reply": {"type": "boolean"},
            "hidden": {"type": "boolean"},
            "visible": {"type": "boolean"},
            "post_time": {"type": "string"},
            "reply_time": {"type": "string"},
            "ip": {"type": "string"},
            "can_edit": {"type": "boolean"},
            "can_delete": {"type": "boolean"},
        },
    },
    "Trackback": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "article_id": {"type": "integer"},
            "article_title": {"type": "string"},
            "article_author_id": {"type": "integer"},
            "title": {"type": "string"},
            "title_html": {"type": "string"},
            "url": {"type": "string"},
            "blog": {"type": "string"},
            "excerpt": {"type": "string"},
            "excerpt_html": {"type": "string"},
            "time": {"type": "string"},
            "ip": {"type": "string"},
        },
    },
    "Settings": {
        "type": "object",
        "description": "blog_Settings flattened to {set_name: value}; set_type=0 reads set_value0, =1 reads set_value1",
        "additionalProperties": True,
    },
    "PageLinks": {"type": "string", "description": "HTML produced by the original generatePageLinks"},
}


def _op(
    summary: str,
    *,
    tag: str,
    description: str = "",
    auth: "str | None" = None,
    params: "list[tuple] | None" = None,
    request: "str | None" = None,
    response: "str | None" = None,
    response_list: "str | None" = None,
    extra: "dict | None" = None,
) -> dict:
    """Build one operation object."""
    operation: dict[str, Any] = {
        "tags": [tag],
        "summary": summary,
        "responses": {},
    }
    if description:
        operation["description"] = description
    if auth:
        operation["security"] = [{auth: []}]
        operation["description"] = (description + "\n\n" if description else "") + auth
    if params:
        operation["parameters"] = []
        for name, where, schema_type, note in params:
            operation["parameters"].append(
                {
                    "name": name,
                    "in": where,
                    "required": False,
                    "schema": {"type": schema_type},
                    "description": note,
                }
            )
    if request:
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{request}"}
                }
            },
        }
    ok_schema: dict[str, Any] = {"type": "object", "properties": {"ok": {"const": True}}}
    if response:
        ok_schema["properties"]["data"] = {"$ref": f"#/components/schemas/{response}"}
    if response_list:
        ok_schema["properties"]["items"] = {
            "type": "array",
            "items": {"$ref": f"#/components/schemas/{response_list}"},
        }
    if extra:
        ok_schema["properties"].update(extra)
    operation["responses"]["200"] = {
        "description": "OK",
        "content": {"application/json": {"schema": ok_schema}},
    }
    operation["responses"]["401"] = {
        "description": "not logged in",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}
        },
    }
    operation["responses"]["403"] = {
        "description": "no permission",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}
        },
    }
    return operation


PAGE_PARAMS = [
    ("page", "query", "integer", "page number, starting at 1"),
    ("q", "query", "string", "search keywords, space separated"),
    ("hl", "query", "string", "highlight keywords, defaults to q"),
]

ENDPOINTS: "list[tuple[str, str, dict]]" = [
    ("post", "/api/auth/login", _op(
        "Log in", tag="auth", description="Mirrors login.asp?act=login",
        request="User", extra={"user": {"$ref": "#/components/schemas/User"}},
    )),
    ("post", "/api/auth/logout", _op("Log out", tag="auth")),
    ("get", "/api/auth/me", _op(
        "Current user", tag="auth",
        extra={"user": {"$ref": "#/components/schemas/User"}},
    )),
    ("post", "/api/auth/register", _op(
        "Register", tag="auth", description="Mirrors register.asp; needs enableRegister=1",
    )),
    ("get", "/api/site", _op(
        "Site metadata", tag="site",
        description="title, description, theme paths, feature switches, counters, online users, sidebar and announcement",
    )),
    ("get", "/api/lang", _op("Language pack", tag="site", description="every string from lang/blog.asp and lang/admin.asp")),
    ("get", "/api/health", _op("Health check and counters", tag="site")),
    ("get", "/api/articles", _op(
        "Article list", tag="articles",
        description="Mirrors default.asp: view mode, category, author, featured, search and date filters plus pagination",
        params=[
            ("mode", "query", "string", "normal or list"),
            ("cat", "query", "integer", "category id"),
            ("user", "query", "integer", "author id"),
            ("selected", "query", "string", "true for featured articles only"),
            ("date", "query", "string", "YYYY-MM-DD"),
            *PAGE_PARAMS,
        ],
        response_list="Article",
        extra={
            "total": {"type": "integer"},
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
            "pages": {"type": "integer"},
            "page_links": {"$ref": "#/components/schemas/PageLinks"},
        },
    )),
    ("get", "/api/articles/{article_id}", _op(
        "Article detail", tag="articles",
        description="Mirrors article.asp: body, neighbours, comments merged with trackbacks; the view counter is incremented",
        params=[("article_id", "path", "integer", "article id"), ("page", "query", "integer", "comment page")],
        extra={
            "article": {"$ref": "#/components/schemas/Article"},
            "comments": {"type": "object"},
            "previous": {"type": "object"},
            "next": {"type": "object"},
            "can_comment": {"type": "boolean"},
        },
    )),
    ("post", "/api/articles", _op(
        "Create article", tag="articles", description="Mirrors article.asp?act=save; needs rights.post>1",
        auth="login required and rights.post>1", request="ArticleForm",
    )),
    ("patch", "/api/articles/{article_id}", _op(
        "Update article", tag="articles", description="Mirrors act=update",
        auth="login required and rights.edit>1, or rights.edit==1 on your own article",
        params=[("article_id", "path", "integer", "article id")],
        request="ArticleForm",
    )),
    ("delete", "/api/articles/{article_id}", _op(
        "Delete article", tag="articles", description="Mirrors act=delete; comments and trackbacks go with it",
        auth="login required and rights.delete>1, or rights.delete==1 on your own article",
        params=[("article_id", "path", "integer", "article id")],
    )),
    ("post", "/api/articles/{article_id}/comments", _op(
        "Post comment", tag="comments",
        description="Mirrors comment.asp?act=save; anonymous visitors may post, a supplied comm_password is verified first",
        params=[("article_id", "path", "integer", "article id")],
    )),
    ("patch", "/api/comments/{comment_id}", _op(
        "Edit comment", tag="comments", auth="login required and rights.edit allows it",
        params=[("comment_id", "path", "integer", "comment id")],
    )),
    ("delete", "/api/comments/{comment_id}", _op(
        "Delete comment", tag="comments", auth="login required and rights.delete allows it",
        params=[("comment_id", "path", "integer", "comment id")],
    )),
    ("get", "/api/guestbook", _op(
        "Guestbook list", tag="guestbook", params=PAGE_PARAMS, response_list="GuestbookEntry",
    )),
    ("get", "/api/guestbook/{entry_id}", _op(
        "Single guestbook entry (for editing)", tag="guestbook", auth="login required and rights.edit>=1",
        params=[("entry_id", "path", "integer", "entry id")],
        response="GuestbookEntry",
    )),
    ("post", "/api/guestbook", _op(
        "Post guestbook entry", tag="guestbook", description="anonymous visitors may post, with the same rules as comments",
    )),
    ("patch", "/api/guestbook/{entry_id}", _op(
        "Edit or reply to a guestbook entry", tag="guestbook",
        auth="login required; the reply area needs rights.edit>2",
        params=[("entry_id", "path", "integer", "entry id")],
    )),
    ("delete", "/api/guestbook/{entry_id}", _op(
        "Delete guestbook entry", tag="guestbook", auth="login required and rights.delete allows it, or administrator",
        params=[("entry_id", "path", "integer", "entry id")],
    )),
    ("get", "/api/trackbacks", _op(
        "Trackback list", tag="trackback",
        params=[("id", "query", "integer", "filter by article"), ("cat", "query", "integer", "filter by category"), *PAGE_PARAMS],
        response_list="Trackback",
    )),
    ("delete", "/api/trackbacks/{trackback_id}", _op(
        "Delete trackback", tag="trackback", auth="login required and rights.delete allows it",
        params=[("trackback_id", "path", "integer", "trackback id")],
    )),
    ("get", "/trackback/{article_id}", _op(
        "Receive a Trackback ping", tag="trackback",
        description="Mirrors the default branch of trackback.asp; answers text/xml with <response><error>0</error></response>",
        params=[
            ("article_id", "path", "integer", "target article id"),
            ("url", "query", "string", "source URL"),
            ("title", "query", "string", "title"),
            ("excerpt", "query", "string", "excerpt"),
            ("blog_name", "query", "string", "blog name"),
        ],
    )),
    ("get", "/feed", _op(
        "RSS/JS feed", tag="site",
        params=[
            ("cat", "query", "integer", "category filter"),
            ("selected", "query", "string", "true for featured entries only"),
            ("q", "query", "string", "use comment for the comment feed"),
            ("id", "query", "integer", "comment feed of one article"),
            ("type", "query", "string", "use js for a document.write snippet"),
        ],
    )),
    ("get", "/api/categories", _op("Category list", tag="articles", response_list="Category")),
    ("get", "/api/archive", _op(
        "Sidebar calendar", tag="site",
        params=[("year", "query", "integer", "year"), ("month", "query", "integer", "month")],
    )),
    ("get", "/api/stats", _op("Site counters", tag="site", response_list="User")),
    ("get", "/api/stats/visitors", _op(
        "Visitor records", tag="site", auth="administrator", description="Mirrors stats.asp",
    )),
    ("get", "/api/users", _op(
        "User list", tag="users",
        params=[("page", "query", "integer", "page number")], response_list="User",
    )),
    ("get", "/api/users/{user_id}", _op(
        "User profile", tag="users",
        params=[("user_id", "path", "integer", "user id")], response="User",
    )),
    ("patch", "/api/users/{user_id}", _op(
        "Update profile", tag="users",
        description="Mirrors user.asp?act=update; an administrator editing somebody else confirms with their own password, groupID is administrator-only",
        auth="self or administrator",
        params=[("user_id", "path", "integer", "user id")],
    )),
    ("delete", "/api/users/{user_id}", _op(
        "Delete user", tag="users",
        description="author ids in articles, comments and guestbook entries become 0; deleting the last administrator is refused",
        auth="self or administrator",
        params=[("user_id", "path", "integer", "user id")],
    )),
    ("post", "/api/upload", _op(
        "Upload attachment", tag="upload",
        description="multipart/form-data with the field named File; stored under data/uploads/YYMM/DD_hhiiss_<name>.ext",
        auth="login required, rights.upload>0 and enableUpload=1",
    )),
    ("get", "/api/upload/limits", _op("Upload limits", tag="upload")),
    ("get", "/uploads/{name}", _op("Download an attachment", tag="upload")),
    ("post", "/api/admin/login", _op(
        "Admin second login", tag="admin", description="Mirrors admin.asp?act=login",
        auth="site administrator",
    )),
    ("post", "/api/admin/logout", _op("Leave the admin backend", tag="admin")),
    ("get", "/api/admin/info", _op(
        "Server and counter information", tag="admin", auth="administrator with the second login done",
    )),
    ("get", "/api/admin/settings", _op(
        "Read every setting", tag="admin", auth="administrator with the second login done", response="Settings",
    )),
    ("post", "/api/admin/settings", _op(
        "Save settings", tag="admin",
        description="validates each field the way updateSettings does: empty strings are skipped, integers use exclusive bounds, booleans are always written",
        auth="administrator with the second login done",
    )),
    ("get", "/api/admin/categories", _op("Admin category list", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/categories", _op(
        "Bulk category operation", tag="admin",
        description="act=update renames, reorders and inserts; act=move relocates articles; act=delete removes their articles, comments and trackbacks too",
        auth="administrator with the second login done",
    )),
    ("get", "/api/admin/groups", _op("User group list", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/groups", _op(
        "Bulk user group operation", tag="admin", description="the built-in Admin group is skipped; deleting a group removes its users too",
        auth="administrator with the second login done",
    )),
    ("get", "/api/admin/smilies", _op("Smiley list", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/smilies", _op("Bulk smiley operation", tag="admin", auth="administrator with the second login done")),
    ("get", "/api/admin/wordfilter", _op("Word filter list", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/wordfilter", _op("Bulk word filter operation", tag="admin", auth="administrator with the second login done")),
    ("get", "/api/admin/database", _op(
        "Database info and backup list", tag="admin", auth="administrator with the second login done",
    )),
    ("post", "/api/admin/database", _op(
        "Database operation", tag="admin",
        description="act=compact runs VACUUM, act=backup writes a _YYMMDD_hhiiss.bak file, act=restore and act=delete manage the backups",
        auth="administrator with the second login done",
    )),
    ("get", "/api/admin/attachments", _op(
        "Attachment listing", tag="admin",
        params=[("path", "query", "string", "sub path relative to data/uploads")],
        auth="administrator with the second login done",
    )),
    ("post", "/api/admin/attachments", _op(
        "Delete an attachment or an empty folder", tag="admin", auth="administrator with the second login done",
    )),
    ("get", "/api/admin/announce", _op("Read the announcement", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/announce", _op("Save the announcement", tag="admin", auth="administrator with the second login done")),
    ("get", "/api/admin/links", _op("Read the links", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/links", _op("Save the links", tag="admin", auth="administrator with the second login done")),
    ("post", "/api/admin/misc", _op(
        "Maintenance", tag="admin",
        description="act=resync_g/resync_c/resync_a/resync_u recompute counters; clean_u/clean_vc/clean_gb remove stale rows",
        auth="administrator with the second login done",
    )),
    ("post", "/api/admin/site-state", _op(
        "Open or close the site", tag="admin", auth="administrator with the second login done",
    )),
]


def asp_path(path: str) -> str:
    """Public paths all end in .asp; the WSGI layer strips the suffix before routing."""
    head, _, tail = path.rpartition("/")
    if not tail:
        return path + ".asp"
    return f"{head}/{tail}.asp"


def build() -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for method, path, operation in ENDPOINTS:
        paths.setdefault(asp_path(path), {})[method] = operation
    return {
        "openapi": "3.1.0",
        "info": INFO,
        "servers": [SERVER],
        "tags": TAGS,
        "components": {"schemas": SCHEMAS},
        "paths": paths,
    }
