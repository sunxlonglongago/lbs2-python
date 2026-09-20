"""SQLite schema for the LBS^2 port.

Table names and column names are copied verbatim from the original Access
database (``data/blog.mdb``, ``data/gbook.mdb``) so that the ASP sources and
the Python port can be compared column by column.

Type mapping used by the importer:

===========  ==================  ==============================
Jet type     Access type         SQLite
===========  ==================  ==============================
1            Yes/No              INTEGER (0/1)
2            Byte                INTEGER
3            Integer             INTEGER
4            Long Integer        INTEGER (PRIMARY KEY AUTOINCREMENT when autonumber)
8            Date/Time           TEXT ``YYYY-MM-DD HH:MM:SS``
10           Text(n)             TEXT
12           Memo                TEXT
===========  ==================  ==============================
"""

from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA_VERSION: Final = 1

# Table name -> ordered (column, column definition) pairs.
# The order follows the original Access table definitions.
TABLES: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "blog_Article": (
        ("log_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("log_catID", "INTEGER"),
        ("log_title", "TEXT"),
        ("log_authorID", "INTEGER"),
        ("log_author", "TEXT"),
        ("log_editMark", "TEXT"),
        ("log_trackbackURL", "TEXT"),
        ("log_content0", "TEXT"),
        ("log_content1", "TEXT"),
        ("log_mode", "INTEGER"),
        ("log_locked", "INTEGER"),
        ("log_selected", "INTEGER"),
        ("log_ubbFlags", "TEXT"),
        ("log_postTime", "TEXT"),
        ("log_ip", "TEXT"),
        ("log_commentCount", "INTEGER"),
        ("log_viewCount", "INTEGER"),
        ("log_trackbackCount", "INTEGER"),
    ),
    "blog_Category": (
        ("cat_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("cat_name", "TEXT"),
        ("cat_order", "INTEGER"),
        ("cat_articleCount", "INTEGER"),
        ("cat_hidden", "INTEGER"),
        ("cat_locked", "INTEGER"),
    ),
    "blog_Comment": (
        ("comm_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("log_id", "INTEGER"),
        ("comm_content", "TEXT"),
        ("comm_authorID", "INTEGER"),
        ("comm_author", "TEXT"),
        ("comm_editMark", "TEXT"),
        ("comm_hidden", "INTEGER"),
        ("comm_ubbFlags", "TEXT"),
        ("comm_postTime", "TEXT"),
        ("comm_ip", "TEXT"),
    ),
    "blog_Settings": (
        # COLLATE NOCASE mirrors Access: updateSettings() in src_admin.asp
        # addresses rows by lower case name ("blogtitle") while the stored
        # names are camel case ("blogTitle"), and Jet compares strings case
        # insensitively. Plain SQLite would create a duplicate row instead.
        ("set_name", "TEXT PRIMARY KEY COLLATE NOCASE"),
        ("set_type", "INTEGER"),
        ("set_value0", "INTEGER"),
        ("set_value1", "TEXT"),
    ),
    "blog_Smilies": (
        ("sm_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("sm_image", "TEXT"),
        ("sm_code", "TEXT"),
    ),
    "blog_Trackback": (
        ("tb_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("log_id", "INTEGER"),
        ("tb_url", "TEXT"),
        ("tb_title", "TEXT"),
        ("tb_blog", "TEXT"),
        ("tb_excerpt", "TEXT"),
        ("tb_time", "TEXT"),
        ("tb_ip", "TEXT"),
    ),
    "blog_User": (
        ("user_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        # The ASP sources look users up by name and rely on Access' case
        # insensitive comparison; keep the same behaviour here.
        ("user_name", "TEXT COLLATE NOCASE"),
        ("user_password", "TEXT"),
        ("user_salt", "TEXT"),
        ("user_groupID", "INTEGER"),
        ("user_gender", "INTEGER"),
        ("user_email", "TEXT"),
        ("user_hideEmail", "INTEGER"),
        ("user_homepage", "TEXT"),
        ("user_articleCount", "INTEGER"),
        ("user_commentCount", "INTEGER"),
        ("user_lastVisit", "TEXT"),
        ("user_ip", "TEXT"),
        ("user_hashKey", "TEXT"),
    ),
    "blog_UserGroup": (
        ("group_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("group_name", "TEXT"),
        ("group_rights", "TEXT"),
    ),
    "blog_VisitorRecord": (
        ("vr_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("vr_ip", "TEXT"),
        ("vr_os", "TEXT"),
        ("vr_browser", "TEXT"),
        ("vr_time", "TEXT"),
        ("vr_referer", "TEXT"),
        ("vr_target", "TEXT"),
    ),
    "blog_WordFilter": (
        ("wf_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("wf_mode", "INTEGER"),
        ("wf_text", "TEXT"),
        ("wf_replace", "TEXT"),
        ("wf_regExp", "INTEGER"),
    ),
    "Guestbook": (
        ("gb_id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("gb_username", "TEXT"),
        ("gb_userID", "INTEGER"),
        ("gb_content", "TEXT"),
        ("gb_editMark", "TEXT"),
        ("gb_ubbFlags", "TEXT"),
        ("gb_postTime", "TEXT"),
        ("gb_replyUsername", "TEXT"),
        ("gb_reply", "TEXT"),
        ("gb_replyTime", "TEXT"),
        ("gb_hidden", "INTEGER"),
        ("gb_ip", "TEXT"),
    ),
}

# Indexes derived from the query shapes in the original ASP sources.
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

# Built-in groups shipped with LBS^2. The rights string is five digits:
# view / post / edit / delete / upload.
BUILTIN_GROUPS: Final = (
    (1, "Admin", "99999"),
    (2, "Guest", "11110"),
    (3, "Registered", "11110"),
    (4, "Author", "22111"),
    (5, "Editor", "22221"),
)


def column_names(table: str) -> tuple[str, ...]:
    """Return the column names of ``table`` in original definition order."""
    return tuple(name for name, _ in TABLES[table])


def create_statement(table: str) -> str:
    columns = ",\n    ".join(f"{name} {decl}" for name, decl in TABLES[table])
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    {columns}\n)"


def create_statements() -> list[str]:
    return [create_statement(table) for table in TABLES] + list(INDEXES)


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create every table and index if they are missing."""
    for statement in create_statements():
        conn.execute(statement)
