#!/usr/bin/env python3
"""Seed demo data: one hello world style row per table.

The original Access database already carries the 49 site settings, the 20
smilies and the 5 user groups, but every content table is empty. This script
adds the reference rows plus one demo record per content table so the frontend
and backend can be exercised end to end.

Usage::

    python3 server/src/tools/seed_demo.py --data dev-data
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import db  # noqa: E402
import schema  # noqa: E402

# (set_name, set_type, set_value0, set_value1) exactly as shipped by LBS^2.
DEFAULT_SETTINGS = (
    ("announce", 1, 0, "You have installed LBS2.\n"
                       "Please login as Admin and config it in "
                       "[url=admin.asp]Administration Page[/url]."),
    ("announceDate", 1, 0, "2005-03-04 18:46:00"),
    ("announceShow", 0, 1, ""),
    ("announceUBBFlags", 1, 0, "111111"),
    ("articlePerPageList", 0, 40, ""),
    ("articlePerPageNormal", 0, 8, ""),
    ("baseURL", 1, 0, "http://localhost:5059/"),
    ("blogDescription", 1, 0, "A Place for Expression"),
    ("blogLanguage", 1, 0, "en"),
    ("blogTitle", 1, 0, "LBS^2"),
    ("blogWebMaster", 1, 0, "Unknown"),
    ("blogWebMasterEmail", 1, 0, "null@null.com"),
    ("commentPerPage", 0, 0, ""),
    ("commentTimeOrder", 0, 0, ""),
    ("contentAutoSplitChars", 0, 400, ""),
    ("counterArticle", 0, 0, ""),
    ("counterComment", 0, 0, ""),
    ("counterTrackback", 0, 0, ""),
    ("counterUser", 0, 0, ""),
    ("counterVisitor", 0, 0, ""),
    ("defaultViewMode", 0, 0, ""),
    ("enableComment", 0, 1, ""),
    ("enableContentAutoSplit", 0, 1, ""),
    ("enableDynamicCalendar", 0, 1, ""),
    ("enableGuestBook", 0, 1, ""),
    ("enableRegister", 0, 1, ""),
    # Security code (scode.asp) is disabled for now: the endpoint is not
    # implemented yet, so the forms must not render the captcha row.
    ("enableSecurityCode", 0, 0, ""),
    ("enableTrackbackIn", 0, 1, ""),
    ("enableTrackbackOut", 0, 1, ""),
    ("enableUpload", 0, 1, ""),
    ("enableVisitorRecord", 0, 1, ""),
    ("entryPerPageGuestBook", 0, 10, ""),
    ("imageFolder", 1, 0, "styles/default/images"),
    ("links", 1, 0,
     '<a href="http://www.voidland.com/" target="_blank">原文如此.SiC</a><br>'),
    ("listEntryPerPage", 0, 30, ""),
    ("logoImage", 1, 0, "styles/default/images/logo.gif"),
    ("maxCommentLength", 0, 1000, ""),
    ("maxVisitorRecord", 0, 100, ""),
    ("minPostDuration", 0, 180, ""),
    ("recentArticleList", 0, 10, ""),
    ("recentCommentList", 0, 10, ""),
    ("showTrackbackPosition", 0, 0, ""),
    ("showTrackbackWithComment", 0, 1, ""),
    ("smiliesFolder", 1, 0, "styles/default/images/smilies"),
    ("smiliesPerRow", 0, 4, ""),
    ("styleSheet", 1, 0, "styles/default/styles.css"),
    ("uploadPath", 1, 0, "uploads/"),
    ("uploadSize", 0, 40000, ""),
    ("uploadTypes", 1, 0, "ZIP,RAR,GIF,JPG,PNG"),
)

SMILIES = (
    ("[smile]", "icon_smile.gif"),
    ("[confused]", "icon_confused.gif"),
    ("[cool]", "icon_cool.gif"),
    ("[cry]", "icon_cry.gif"),
    ("[eek]", "icon_eek.gif"),
    ("[angry]", "icon_angry.gif"),
    ("[wink]", "icon_wink.gif"),
    ("[sweat]", "icon_sweat.gif"),
    ("[lol]", "icon_lol.gif"),
    ("[stun]", "icon_stun.gif"),
    ("[razz]", "icon_razz.gif"),
    ("[redface]", "icon_redface.gif"),
    ("[rolleyes]", "icon_rolleyes.gif"),
    ("[sad]", "icon_sad.gif"),
    ("[yes]", "icon_yes.gif"),
    ("[no]", "icon_no.gif"),
    ("[heart]", "icon_heart.gif"),
    ("[star]", "icon_star.gif"),
    ("[music]", "icon_music.gif"),
    ("[idea]", "icon_idea.gif"),
)

DEMO_IP = "127.0.0.1"
DEMO_UBB = "111111"
ADMIN_NAME = "Admin"
ADMIN_PASSWORD = "comeon"  # the LBS^2 default, change it after the first login
ADMIN_SALT = "lbs2py"


def password_hash(password: str, salt: str) -> str:
    return hashlib.sha1((password + salt).encode("utf-8")).hexdigest()


def now_stamp(conn) -> str:
    return db.scalar(conn, "SELECT datetime('now', 'localtime')")


def count(conn, table: str) -> int:
    return int(db.scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0)


def seed_settings(conn) -> int:
    written = 0
    for name, set_type, value0, value1 in DEFAULT_SETTINGS:
        db.upsert(
            conn,
            "blog_Settings",
            {
                "set_name": name,
                "set_type": set_type,
                "set_value0": value0,
                "set_value1": value1,
            },
            key="set_name",
        )
        written += 1
    return written


def seed_groups(conn) -> int:
    written = 0
    for group_id, name, rights in schema.BUILTIN_GROUPS:
        if db.query_one(conn, "SELECT 1 FROM blog_UserGroup WHERE group_id = ?", (group_id,)):
            continue
        db.insert(
            conn,
            "blog_UserGroup",
            {"group_id": group_id, "group_name": name, "group_rights": rights},
        )
        written += 1
    return written


def seed_smilies(conn) -> int:
    written = 0
    for code, image in SMILIES:
        if db.query_one(conn, "SELECT 1 FROM blog_Smilies WHERE sm_code = ?", (code,)):
            continue
        db.insert(conn, "blog_Smilies", {"sm_image": image, "sm_code": code})
        written += 1
    return written


def seed_admin(conn, stamp: str) -> int:
    existing = db.query_one(
        conn, "SELECT user_id FROM blog_User WHERE user_name = ?", (ADMIN_NAME,)
    )
    if existing:
        return 0
    db.insert(
        conn,
        "blog_User",
        {
            "user_name": ADMIN_NAME,
            "user_password": password_hash(ADMIN_PASSWORD, ADMIN_SALT),
            "user_salt": ADMIN_SALT,
            "user_groupID": 1,
            "user_gender": 0,
            "user_email": "admin@localhost",
            "user_hideEmail": 0,
            "user_homepage": "",
            "user_articleCount": 1,
            "user_commentCount": 1,
            "user_lastVisit": stamp,
            "user_ip": DEMO_IP,
            "user_hashKey": "",
        },
    )
    return 1


def seed_content(conn, stamp: str) -> dict[str, int]:
    written: dict[str, int] = {}

    if not count(conn, "blog_Category"):
        db.insert(
            conn,
            "blog_Category",
            {
                "cat_name": "Default",
                "cat_order": 1,
                "cat_articleCount": 1,
                "cat_hidden": 0,
                "cat_locked": 0,
            },
        )
        written["blog_Category"] = 1
    category_id = db.scalar(conn, "SELECT cat_id FROM blog_Category ORDER BY cat_order LIMIT 1")

    if not count(conn, "blog_Article"):
        db.insert(
            conn,
            "blog_Article",
            {
                "log_catID": category_id,
                "log_title": "Hello World",
                "log_authorID": 1,
                "log_author": ADMIN_NAME,
                "log_editMark": "",
                "log_trackbackURL": "",
                "log_content0": "Hello World. This is the first entry of the ported "
                                "LBS^2 running on Python and SQLite.",
                "log_content1": "",
                "log_mode": 1,
                "log_locked": 0,
                "log_selected": 1,
                "log_ubbFlags": DEMO_UBB,
                "log_postTime": stamp,
                "log_ip": DEMO_IP,
                "log_commentCount": 1,
                "log_viewCount": 1,
                "log_trackbackCount": 1,
            },
        )
        written["blog_Article"] = 1
    article_id = db.scalar(conn, "SELECT log_id FROM blog_Article ORDER BY log_id LIMIT 1")

    if not count(conn, "blog_Comment"):
        db.insert(
            conn,
            "blog_Comment",
            {
                "log_id": article_id,
                "comm_content": "Hello World comment.",
                "comm_authorID": 1,
                "comm_author": ADMIN_NAME,
                "comm_editMark": "",
                "comm_hidden": 0,
                "comm_ubbFlags": DEMO_UBB,
                "comm_postTime": stamp,
                "comm_ip": DEMO_IP,
            },
        )
        written["blog_Comment"] = 1

    if not count(conn, "blog_Trackback"):
        db.insert(
            conn,
            "blog_Trackback",
            {
                "log_id": article_id,
                "tb_url": "http://localhost:5057/article/1",
                "tb_title": "Hello World",
                "tb_blog": "LBS^2 Demo",
                "tb_excerpt": "Hello World trackback.",
                "tb_time": stamp,
                "tb_ip": DEMO_IP,
            },
        )
        written["blog_Trackback"] = 1

    if not count(conn, "Guestbook"):
        db.insert(
            conn,
            "Guestbook",
            {
                "gb_username": "Guest",
                "gb_userID": 0,
                "gb_content": "Hello World from the guestbook.",
                "gb_editMark": "",
                "gb_ubbFlags": DEMO_UBB,
                "gb_postTime": stamp,
                "gb_replyUsername": ADMIN_NAME,
                "gb_reply": "Hello World, thanks for signing.",
                "gb_replyTime": stamp,
                "gb_hidden": 0,
                "gb_ip": DEMO_IP,
            },
        )
        written["Guestbook"] = 1

    if not count(conn, "blog_VisitorRecord"):
        db.insert(
            conn,
            "blog_VisitorRecord",
            {
                "vr_ip": DEMO_IP,
                "vr_os": "macOS",
                "vr_browser": "Safari",
                "vr_time": stamp,
                "vr_referer": "",
                "vr_target": "/",
            },
        )
        written["blog_VisitorRecord"] = 1

    if not count(conn, "blog_WordFilter"):
        db.insert(
            conn,
            "blog_WordFilter",
            {
                "wf_mode": 0,
                "wf_text": "helloworld",
                "wf_replace": "Hello World",
                "wf_regExp": 0,
            },
        )
        written["blog_WordFilter"] = 1

    return written


def refresh_counters(conn) -> None:
    counters = {
        "counterArticle": "blog_Article",
        "counterComment": "blog_Comment",
        "counterTrackback": "blog_Trackback",
        "counterUser": "blog_User",
        "counterVisitor": "blog_VisitorRecord",
    }
    for name, table in counters.items():
        db.update(
            conn,
            "blog_Settings",
            {"set_value0": count(conn, table)},
            "set_name = ?",
            (name,),
        )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="runtime data directory")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config.set_data_dir(args.data)
    conn = db.connect()
    db.ensure_schema(conn)
    stamp = now_stamp(conn)

    print(f"settings written : {seed_settings(conn)}")
    print(f"groups written   : {seed_groups(conn)}")
    print(f"smilies written  : {seed_smilies(conn)}")
    print(f"admin written    : {seed_admin(conn, stamp)}")
    for table, rows in seed_content(conn, stamp).items():
        print(f"{table:17}: {rows}")
    refresh_counters(conn)

    conn.commit()
    conn.close()
    print(f"\nseeded {config.db_path()}")
    print(f"login: {ADMIN_NAME} / {ADMIN_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
