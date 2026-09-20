"""Column reference extracted from the original Access databases.

Generated from ``data/blog.mdb`` and ``data/gbook.mdb`` (LBS^2 v2.0.304) by
reading the Jet table definition pages. Each entry is
``(column, access_type, text_length, autonumber, primary_key)``.

``text_length`` is the number of characters for ``TEXT`` columns (the Jet
definition stores bytes for Unicode compressed columns, so the value is
halved). It is ``None`` for other types.

This file is the contract used by ``dump_schema.py`` to verify that the
SQLite port still matches the original table layout.
"""

from __future__ import annotations

from typing import Final

ACCESS_TABLES: Final = {
    "blog_Article": (
        ("log_id", "LONG", None, True, True),
        ("log_catID", "LONG", None, False, False),
        ("log_title", "TEXT", 255, False, False),
        ("log_authorID", "LONG", None, False, False),
        ("log_author", "TEXT", 25, False, False),
        ("log_editMark", "TEXT", 50, False, False),
        ("log_trackbackURL", "TEXT", 255, False, False),
        ("log_content0", "MEMO", None, False, False),
        ("log_content1", "MEMO", None, False, False),
        ("log_mode", "BYTE", None, False, False),
        ("log_locked", "YESNO", None, False, False),
        ("log_selected", "YESNO", None, False, False),
        ("log_ubbFlags", "TEXT", 100, False, False),
        ("log_postTime", "DATETIME", None, False, False),
        ("log_ip", "TEXT", 15, False, False),
        ("log_commentCount", "LONG", None, False, False),
        ("log_viewCount", "LONG", None, False, False),
        ("log_trackbackCount", "LONG", None, False, False),
    ),
    "blog_Category": (
        ("cat_id", "LONG", None, True, True),
        ("cat_name", "TEXT", 50, False, False),
        ("cat_order", "LONG", None, False, False),
        ("cat_articleCount", "LONG", None, False, False),
        ("cat_hidden", "YESNO", None, False, False),
        ("cat_locked", "YESNO", None, False, False),
    ),
    "blog_Comment": (
        ("comm_id", "LONG", None, True, True),
        ("log_id", "LONG", None, False, False),
        ("comm_content", "MEMO", None, False, False),
        ("comm_authorID", "LONG", None, False, False),
        ("comm_author", "TEXT", 25, False, False),
        ("comm_editMark", "TEXT", 50, False, False),
        ("comm_hidden", "YESNO", None, False, False),
        ("comm_ubbFlags", "TEXT", 20, False, False),
        ("comm_postTime", "DATETIME", None, False, False),
        ("comm_ip", "TEXT", 15, False, False),
    ),
    "blog_Settings": (
        ("set_name", "TEXT", 25, False, True),
        ("set_type", "BYTE", None, False, False),
        ("set_value0", "LONG", None, False, False),
        ("set_value1", "MEMO", None, False, False),
    ),
    "blog_Smilies": (
        ("sm_id", "LONG", None, True, True),
        ("sm_image", "TEXT", 50, False, False),
        ("sm_code", "TEXT", 25, False, False),
    ),
    "blog_Trackback": (
        ("tb_id", "LONG", None, True, True),
        ("log_id", "LONG", None, False, False),
        ("tb_url", "TEXT", 100, False, False),
        ("tb_title", "TEXT", 100, False, False),
        ("tb_blog", "TEXT", 100, False, False),
        ("tb_excerpt", "MEMO", None, False, False),
        ("tb_time", "DATETIME", None, False, False),
        ("tb_ip", "TEXT", 15, False, False),
    ),
    "blog_User": (
        ("user_id", "LONG", None, True, True),
        ("user_name", "TEXT", 25, False, False),
        ("user_password", "TEXT", 40, False, False),
        ("user_salt", "TEXT", 6, False, False),
        ("user_groupID", "LONG", None, False, False),
        ("user_gender", "BYTE", None, False, False),
        ("user_email", "TEXT", 50, False, False),
        ("user_hideEmail", "YESNO", None, False, False),
        ("user_homepage", "TEXT", 50, False, False),
        ("user_articleCount", "LONG", None, False, False),
        ("user_commentCount", "LONG", None, False, False),
        ("user_lastVisit", "DATETIME", None, False, False),
        ("user_ip", "TEXT", 15, False, False),
        ("user_hashKey", "TEXT", 40, False, False),
    ),
    "blog_UserGroup": (
        ("group_id", "LONG", None, True, True),
        ("group_name", "TEXT", 50, False, False),
        ("group_rights", "TEXT", 50, False, False),
    ),
    "blog_VisitorRecord": (
        ("vr_id", "LONG", None, True, True),
        ("vr_ip", "TEXT", 15, False, False),
        ("vr_os", "TEXT", 20, False, False),
        ("vr_browser", "TEXT", 30, False, False),
        ("vr_time", "DATETIME", None, False, False),
        ("vr_referer", "TEXT", 250, False, False),
        ("vr_target", "TEXT", 50, False, False),
    ),
    "blog_WordFilter": (
        ("wf_id", "LONG", None, True, True),
        ("wf_mode", "BYTE", None, False, False),
        ("wf_text", "TEXT", 50, False, False),
        ("wf_replace", "TEXT", 50, False, False),
        ("wf_regExp", "YESNO", None, False, False),
    ),
    "Guestbook": (
        ("gb_id", "LONG", None, True, True),
        ("gb_username", "TEXT", 50, False, False),
        ("gb_userID", "LONG", None, False, False),
        ("gb_content", "MEMO", None, False, False),
        ("gb_editMark", "TEXT", 50, False, False),
        ("gb_ubbFlags", "TEXT", 10, False, False),
        ("gb_postTime", "DATETIME", None, False, False),
        ("gb_replyUsername", "TEXT", 50, False, False),
        ("gb_reply", "MEMO", None, False, False),
        ("gb_replyTime", "DATETIME", None, False, False),
        ("gb_hidden", "YESNO", None, False, False),
        ("gb_ip", "TEXT", 15, False, False),
    ),
}

# Access type -> SQLite affinity used by schema.py.
SQLITE_TYPE: Final = {
    "YESNO": "INTEGER",
    "BYTE": "INTEGER",
    "INTEGER": "INTEGER",
    "LONG": "INTEGER",
    "DATETIME": "TEXT",
    "TEXT": "TEXT",
    "MEMO": "TEXT",
}
