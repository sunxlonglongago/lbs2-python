"""Database layout.

This module is the single source of truth for the schema: the DDL that creates a
fresh database, the declared field types the documentation and the self check
read, and the built-in user groups.

Table and column names follow the original LBS^2 database this application is
based on (see NOTICE), which is why the ``blog_`` prefix is kept.

Every column is declared as ``(name, sqlite_declaration, declared_type)``. The
declared type records the app level type and, for text columns, the length the
application enforces; SQLite itself only stores an affinity, so it appears in
``docs/database.md`` and in ``tools/check_db.py`` rather than in the DDL.
"""

from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA_VERSION: Final = 1

# Declared type -> SQLite affinity, used by the docs and the schema check.
DECLARED_TO_SQLITE: Final = {
    "YESNO": "INTEGER",
    "BYTE": "INTEGER",
    "INTEGER": "INTEGER",
    "LONG": "INTEGER",
    "DATETIME": "TEXT",
    "TEXT": "TEXT",
    "MEMO": "TEXT",
}

# Table name -> ordered (column, sqlite declaration, declared type) triples.
TABLES: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    "blog_Article": (
        ("log_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("log_catID", "INTEGER", "LONG"),
        ("log_title", "TEXT", "TEXT(255)"),
        ("log_authorID", "INTEGER", "LONG"),
        ("log_author", "TEXT", "TEXT(25)"),
        ("log_editMark", "TEXT", "TEXT(50)"),
        ("log_trackbackURL", "TEXT", "TEXT(255)"),
        ("log_content0", "TEXT", "MEMO"),
        ("log_content1", "TEXT", "MEMO"),
        ("log_mode", "INTEGER", "BYTE"),
        ("log_locked", "INTEGER", "YESNO"),
        ("log_selected", "INTEGER", "YESNO"),
        ("log_ubbFlags", "TEXT", "TEXT(100)"),
        ("log_postTime", "TEXT", "DATETIME"),
        ("log_ip", "TEXT", "TEXT(15)"),
        ("log_commentCount", "INTEGER", "LONG"),
        ("log_viewCount", "INTEGER", "LONG"),
        ("log_trackbackCount", "INTEGER", "LONG"),
    ),
    "blog_Category": (
        ("cat_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("cat_name", "TEXT", "TEXT(50)"),
        ("cat_order", "INTEGER", "LONG"),
        ("cat_articleCount", "INTEGER", "LONG"),
        ("cat_hidden", "INTEGER", "YESNO"),
        ("cat_locked", "INTEGER", "YESNO"),
    ),
    "blog_Comment": (
        ("comm_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("log_id", "INTEGER", "LONG"),
        ("comm_content", "TEXT", "MEMO"),
        ("comm_authorID", "INTEGER", "LONG"),
        ("comm_author", "TEXT", "TEXT(25)"),
        ("comm_editMark", "TEXT", "TEXT(50)"),
        ("comm_hidden", "INTEGER", "YESNO"),
        ("comm_ubbFlags", "TEXT", "TEXT(20)"),
        ("comm_postTime", "TEXT", "DATETIME"),
        ("comm_ip", "TEXT", "TEXT(15)"),
    ),
    "blog_Settings": (
        # COLLATE NOCASE: the admin backend addresses settings with lower case
        # names ("blogtitle") while the stored names are camel case
        # ("blogTitle"), and the original database compared them case
        # insensitively. Without it a write would create a second row.
        ("set_name", "TEXT PRIMARY KEY COLLATE NOCASE", "TEXT(25)"),
        ("set_type", "INTEGER", "BYTE"),
        ("set_value0", "INTEGER", "LONG"),
        ("set_value1", "TEXT", "MEMO"),
    ),
    "blog_Smilies": (
        ("sm_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("sm_image", "TEXT", "TEXT(50)"),
        ("sm_code", "TEXT", "TEXT(25)"),
    ),
    "blog_Trackback": (
        ("tb_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("log_id", "INTEGER", "LONG"),
        ("tb_url", "TEXT", "TEXT(100)"),
        ("tb_title", "TEXT", "TEXT(100)"),
        ("tb_blog", "TEXT", "TEXT(100)"),
        ("tb_excerpt", "TEXT", "MEMO"),
        ("tb_time", "TEXT", "DATETIME"),
        ("tb_ip", "TEXT", "TEXT(15)"),
    ),
    "blog_User": (
        ("user_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        # Same case insensitive comparison as blog_Settings.set_name.
        ("user_name", "TEXT COLLATE NOCASE", "TEXT(25)"),
        ("user_password", "TEXT", "TEXT(40)"),
        ("user_salt", "TEXT", "TEXT(6)"),
        ("user_groupID", "INTEGER", "LONG"),
        ("user_gender", "INTEGER", "BYTE"),
        ("user_email", "TEXT", "TEXT(50)"),
        ("user_hideEmail", "INTEGER", "YESNO"),
        ("user_homepage", "TEXT", "TEXT(50)"),
        ("user_articleCount", "INTEGER", "LONG"),
        ("user_commentCount", "INTEGER", "LONG"),
        ("user_lastVisit", "TEXT", "DATETIME"),
        ("user_ip", "TEXT", "TEXT(15)"),
        ("user_hashKey", "TEXT", "TEXT(40)"),
    ),
    "blog_UserGroup": (
        ("group_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("group_name", "TEXT", "TEXT(50)"),
        ("group_rights", "TEXT", "TEXT(50)"),
    ),
    "blog_VisitorRecord": (
        ("vr_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("vr_ip", "TEXT", "TEXT(15)"),
        ("vr_os", "TEXT", "TEXT(20)"),
        ("vr_browser", "TEXT", "TEXT(30)"),
        ("vr_time", "TEXT", "DATETIME"),
        ("vr_referer", "TEXT", "TEXT(250)"),
        ("vr_target", "TEXT", "TEXT(50)"),
    ),
    "blog_WordFilter": (
        ("wf_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("wf_mode", "INTEGER", "BYTE"),
        ("wf_text", "TEXT", "TEXT(50)"),
        ("wf_replace", "TEXT", "TEXT(50)"),
        ("wf_regExp", "INTEGER", "YESNO"),
    ),
    "Guestbook": (
        ("gb_id", "INTEGER PRIMARY KEY AUTOINCREMENT", "LONG AUTOINCREMENT"),
        ("gb_username", "TEXT", "TEXT(50)"),
        ("gb_userID", "INTEGER", "LONG"),
        ("gb_content", "TEXT", "MEMO"),
        ("gb_editMark", "TEXT", "TEXT(50)"),
        ("gb_ubbFlags", "TEXT", "TEXT(10)"),
        ("gb_postTime", "TEXT", "DATETIME"),
        ("gb_replyUsername", "TEXT", "TEXT(50)"),
        ("gb_reply", "TEXT", "MEMO"),
        ("gb_replyTime", "TEXT", "DATETIME"),
        ("gb_hidden", "INTEGER", "YESNO"),
        ("gb_ip", "TEXT", "TEXT(15)"),
    ),
}

# Indexes derived from the queries the application runs.
INDEXES: Final[tuple[str, ...]] = (
    "CREATE INDEX IF NOT EXISTS idx_article_posttime ON blog_Article(log_postTime DESC)",
    "CREATE INDEX IF NOT EXISTS idx_article_catid ON blog_Article(log_catID)",
    "CREATE INDEX IF NOT EXISTS idx_article_authorid ON blog_Article(log_authorID)",
    "CREATE INDEX IF NOT EXISTS idx_comment_logid ON blog_Comment(log_id)",
    "CREATE INDEX IF NOT EXISTS idx_comment_posttime ON blog_Comment(comm_postTime DESC)",
    "CREATE INDEX IF NOT EXISTS idx_trackback_logid ON blog_Trackback(log_id)",
    "CREATE INDEX IF NOT EXISTS idx_guestbook_posttime ON Guestbook(gb_postTime)",
    "CREATE INDEX IF NOT EXISTS idx_visitor_time ON blog_VisitorRecord(vr_time)",
)

# Built-in groups. The rights string is five digits:
# view / post / edit / delete / upload.
BUILTIN_GROUPS: Final = (
    (1, "Admin", "99999"),
    (2, "Guest", "11110"),
    (3, "Registered", "11110"),
    (4, "Author", "22111"),
    (5, "Editor", "22221"),
)


def columns(table: str) -> tuple[tuple[str, str, str], ...]:
    """Return the ``(name, declaration, declared type)`` triples of ``table``."""
    return TABLES[table]


def column_names(table: str) -> tuple[str, ...]:
    """Return the column names of ``table`` in declaration order."""
    return tuple(name for name, _declaration, _declared in TABLES[table])


def create_statement(table: str) -> str:
    columns_sql = ",\n    ".join(
        f"{name} {declaration}" for name, declaration, _declared in TABLES[table]
    )
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    {columns_sql}\n)"


def create_statements() -> list[str]:
    return [create_statement(table) for table in TABLES] + list(INDEXES)


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create every table and index if they are missing."""
    for statement in create_statements():
        conn.execute(statement)
