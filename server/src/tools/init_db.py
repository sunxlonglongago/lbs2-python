#!/usr/bin/env python3
"""Initialise a data directory.

Creates the database when it is missing and fills in what a running site needs:
the default settings, the built-in user groups, the smilies and one
administrator account. Safe to run again - rows are only inserted when they are
missing, so settings an administrator has changed are never overwritten.

``--demo`` additionally writes a hello world article, comment, trackback,
guestbook entry, visitor record and word filter, which is convenient for a
first look and is what the end-to-end tests expect.

Usage::

    python3 server/src/tools/init_db.py --data dev-data
    python3 server/src/tools/init_db.py --data dev-data --demo
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
import uploads  # noqa: E402

# (set_name, set_type, set_value0, set_value1) - the defaults the software ships.
DEFAULT_SETTINGS = (
    ("announce", 1, 0, "You have installed LBS2.\n"
                       "Please login as Admin and config it in "
                       "[url=admin.asp]Administration Page[/url]."),
    # Stamped with the install time by seed_settings; the value here is only a
    # placeholder so the tuple keeps its (name, type, value0, value1) shape.
    ("announceDate", 1, 0, ""),
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
    ("enableSecurityCode", 0, 0, ""),
    ("enableTrackbackIn", 0, 1, ""),
    ("enableTrackbackOut", 0, 1, ""),
    ("enableUpload", 0, 1, ""),
    ("enableVisitorRecord", 0, 1, ""),
    ("entryPerPageGuestBook", 0, 10, ""),
    ("imageFolder", 1, 0, "styles/default/images"),
    ("links", 1, 0,
     '<a href="https://github.com/sunxlonglongago/lbs2-python" target="_blank">'
     'LBS^2 Python port</a><br>'),
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
    ("uploadSize", 0, uploads.DEFAULT_UPLOAD_LIMIT, ""),
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

DEFAULT_ADMIN = "Admin"
DEFAULT_PASSWORD = "comeon"
ADMIN_SALT = "lbs2py"
DEMO_IP = "127.0.0.1"
DEMO_UBB = "111111"


def password_hash(password: str, salt: str) -> str:
    return hashlib.sha1((password + salt).encode("utf-8")).hexdigest()


def now_stamp(conn) -> str:
    return db.scalar(conn, "SELECT datetime('now', 'localtime')")


def count(conn, table: str) -> int:
    return int(db.scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0)


def seed_settings(conn, stamp: str) -> int:
    """Insert defaults that are missing; never touch an existing value."""
    written = 0
    for name, set_type, value0, value1 in DEFAULT_SETTINGS:
        if db.query_one(
            conn, "SELECT 1 FROM blog_Settings WHERE set_name = ?", (name,)
        ):
            continue
        if name == "announceDate":
            value1 = stamp
        db.insert(
            conn,
            "blog_Settings",
            {
                "set_name": name,
                "set_type": set_type,
                "set_value0": value0,
                "set_value1": value1,
            },
        )
        written += 1
    return written


def seed_groups(conn) -> int:
    written = 0
    for group_id, name, rights in schema.BUILTIN_GROUPS:
        if db.query_one(
            conn, "SELECT 1 FROM blog_UserGroup WHERE group_id = ?", (group_id,)
        ):
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


def seed_admin(conn, stamp: str, password: str, name: str = DEFAULT_ADMIN) -> bool:
    """Create the administrator account when there is none yet."""
    if db.query_one(conn, "SELECT 1 FROM blog_User WHERE user_name = ?", (name,)):
        return False
    db.insert(
        conn,
        "blog_User",
        {
            "user_name": name,
            "user_password": password_hash(password, ADMIN_SALT),
            "user_salt": ADMIN_SALT,
            "user_groupID": 1,
            "user_gender": 0,
            "user_email": "",
            "user_hideEmail": 0,
            "user_homepage": "",
            "user_articleCount": 0,
            "user_commentCount": 0,
            "user_lastVisit": stamp,
            "user_ip": DEMO_IP,
            "user_hashKey": "",
        },
    )
    return True


def seed_demo_content(conn, stamp: str) -> dict[str, int]:
    """One hello world row per content table, only when it is still empty."""
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
    category_id = db.scalar(
        conn, "SELECT cat_id FROM blog_Category ORDER BY cat_order LIMIT 1"
    )

    if not count(conn, "blog_Article"):
        db.insert(
            conn,
            "blog_Article",
            {
                "log_catID": category_id,
                "log_title": "Hello World",
                "log_authorID": 1,
                "log_author": DEFAULT_ADMIN,
                "log_editMark": "",
                "log_trackbackURL": "",
                "log_content0": "Hello World. This is the first entry of a fresh "
                                "install, running on Flask and SQLite.",
                "log_content1": "",
                "log_mode": 1,
                "log_locked": 0,
                "log_selected": 1,
                "log_ubbFlags": DEMO_UBB,
                "log_postTime": stamp,
                "log_ip": DEMO_IP,
                "log_commentCount": 1,
                "log_viewCount": 0,
                "log_trackbackCount": 1,
            },
        )
        written["blog_Article"] = 1
    article_id = db.scalar(
        conn, "SELECT log_id FROM blog_Article ORDER BY log_id LIMIT 1"
    )

    if not count(conn, "blog_Comment"):
        db.insert(
            conn,
            "blog_Comment",
            {
                "log_id": article_id,
                "comm_content": "Hello World comment.",
                "comm_authorID": 1,
                "comm_author": DEFAULT_ADMIN,
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
                "tb_url": "http://localhost:5059/article.asp?id=1",
                "tb_title": "Hello World",
                "tb_blog": "Example blog",
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
                "gb_replyUsername": DEFAULT_ADMIN,
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
    """Keep the counter settings in step with the actual row counts."""
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
    parser.add_argument(
        "--demo",
        action="store_true",
        help="also write the hello world demo content",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"password for the administrator account (default: {DEFAULT_PASSWORD})",
    )
    parser.add_argument(
        "--admin",
        default=DEFAULT_ADMIN,
        help=f"administrator account name (default: {DEFAULT_ADMIN})",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config.set_data_dir(args.data)
    conn = db.connect()
    db.ensure_schema(conn)
    stamp = now_stamp(conn)

    settings_added = seed_settings(conn, stamp)
    groups_added = seed_groups(conn)
    smilies_added = seed_smilies(conn)
    admin_added = seed_admin(conn, stamp, args.password, args.admin)

    print(f"settings added  : {settings_added}")
    print(f"groups added    : {groups_added}")
    print(f"smilies added   : {smilies_added}")
    print(f"admin created   : {'yes' if admin_added else 'already there'}")

    if args.demo:
        for table, rows in seed_demo_content(conn, stamp).items():
            print(f"{table:16}: {rows} demo row(s)")

    refresh_counters(conn)
    conn.commit()
    conn.close()

    print(f"\ndatabase ready: {config.db_path()}")
    if admin_added:
        print(f"login: {args.admin} / {args.password}   <- change this password now")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
