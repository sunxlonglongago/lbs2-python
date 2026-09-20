"""User accounts backed by ``blog_User`` / ``blog_UserGroup``.

Password scheme follows the original ``class/user.asp``: the stored value is
``SHA1(password + user_salt)``. Rows imported from an old LBS install may still
hold a bare uppercase ``MD5(password)``; those are verified and upgraded to the
salted scheme on the first successful login.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from typing import Any

import db

USER_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{3,24}$")
SALT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"

CAPABILITIES = ("view", "post", "edit", "delete", "upload")


def now_stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def sha1_hex(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest().upper()


def random_salt(length: int = 6) -> str:
    import secrets

    return "".join(secrets.choice(SALT_ALPHABET) for _ in range(length))


def hash_password(password: str, salt: str) -> str:
    return sha1_hex(password + salt)


def parse_rights(rights: str) -> dict[str, int]:
    """Turn a five digit rights string into ``{capability: level}``."""
    levels = {}
    for index, capability in enumerate(CAPABILITIES):
        digit = rights[index] if index < len(rights) else "0"
        levels[capability] = int(digit) if digit.isdigit() else 0
    return levels


def can_view_article(
    rights: dict[str, int],
    *,
    logged_in: bool,
    user_id: int,
    mode: int,
    category_hidden: bool,
    author_id: int,
) -> bool:
    """Port of ``lbsUser.checkViewPermission`` (class/user.asp)."""
    view = rights.get("view", 0)
    blocked = (
        (mode == 1 and view < 1)
        or (mode == 2 and (not logged_in or view < 1))
        or ((mode == 3 or category_hidden) and (not logged_in or view < 2))
        or (mode == 4 and (not logged_in or view < 3))
    )
    return (not blocked) or user_id == author_id


def can_operate(rights: dict[str, int], capability: str, *, owner: bool) -> bool:
    """``>1`` applies to every object, ``==1`` only to the user's own."""
    level = rights.get(capability, 0)
    return level > 1 or (level == 1 and owner)


def validate_user_name(name: str) -> str:
    value = (name or "").strip()
    if not USER_NAME_RE.fullmatch(value):
        raise ValueError("username_invalid")
    return value


def validate_password(password: str) -> str:
    if not 6 <= len(password or "") <= 16:
        raise ValueError("password_invalid")
    return password


def row_to_user(row: sqlite3.Row, groups: "dict[int, sqlite3.Row] | None" = None) -> dict[str, Any]:
    group_id = int(row["user_groupID"] or 2)
    group_name = ""
    rights = parse_rights("11110")
    if groups and group_id in groups:
        group_name = groups[group_id]["group_name"]
        rights = parse_rights(groups[group_id]["group_rights"] or "")
    return {
        "id": int(row["user_id"]),
        "name": row["user_name"],
        "group_id": group_id,
        "group_name": group_name,
        "gender": int(row["user_gender"] or 0),
        "email": row["user_email"] or "",
        "hide_email": bool(row["user_hideEmail"]),
        "homepage": row["user_homepage"] or "",
        "article_count": int(row["user_articleCount"] or 0),
        "comment_count": int(row["user_commentCount"] or 0),
        "last_visit": row["user_lastVisit"] or "",
        "ip": row["user_ip"] or "",
        "rights": rights,
    }


def load_groups(conn: sqlite3.Connection) -> dict[int, sqlite3.Row]:
    rows = db.query_all(conn, "SELECT * FROM blog_UserGroup ORDER BY group_id")
    return {int(row["group_id"]): row for row in rows}


def get_by_id(conn: sqlite3.Connection, user_id: int) -> "sqlite3.Row | None":
    return db.query_one(conn, "SELECT * FROM blog_User WHERE user_id = ?", (user_id,))


def get_by_name(conn: sqlite3.Connection, name: str) -> "sqlite3.Row | None":
    return db.query_one(conn, "SELECT * FROM blog_User WHERE user_name = ?", (name,))


def public_user(conn: sqlite3.Connection, user_id: int) -> "dict[str, Any] | None":
    row = get_by_id(conn, user_id)
    if not row:
        return None
    return row_to_user(row, load_groups(conn))


def list_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    groups = load_groups(conn)
    rows = db.query_all(conn, "SELECT * FROM blog_User ORDER BY user_id")
    return [row_to_user(row, groups) for row in rows]


def verify(conn: sqlite3.Connection, name: str, password: str) -> "dict[str, Any] | None":
    """Return the user dict on success, upgrading legacy MD5 rows in place."""
    row = get_by_name(conn, name)
    if not row:
        return None

    salt = row["user_salt"] or ""
    stored = row["user_password"] or ""
    if salt and stored == hash_password(password, salt):
        return row_to_user(row, load_groups(conn))
    if stored.upper() == md5_hex(password):
        salt = random_salt()
        db.update(
            conn,
            "blog_User",
            {"user_password": hash_password(password, salt), "user_salt": salt},
            "user_id = ?",
            (row["user_id"],),
        )
        conn.commit()
        refreshed = get_by_id(conn, int(row["user_id"]))
        return row_to_user(refreshed, load_groups(conn)) if refreshed else None
    return None


def touch_login(conn: sqlite3.Connection, user_id: int, ip: str) -> None:
    db.update(
        conn,
        "blog_User",
        {"user_lastVisit": now_stamp(), "user_ip": (ip or "")[:15]},
        "user_id = ?",
        (user_id,),
    )
    conn.commit()


def create_user(
    conn: sqlite3.Connection,
    name: str,
    password: str,
    *,
    email: str = "",
    homepage: str = "",
    group_id: int = 3,
    gender: int = 0,
    hide_email: bool = False,
    filters: "list[dict] | None" = None,
) -> dict[str, Any]:
    import utils

    name = validate_user_name(name)
    if filters and utils.word_filter(filters, name) is False:
        raise ValueError("username_invalid")
    validate_password(password)
    if get_by_name(conn, name):
        raise ValueError("user_exist")
    if email and not utils.check_email(email):
        raise ValueError("email_invalid")
    if homepage:
        homepage = utils.check_url(homepage)
    if gender not in (0, 1, 2):
        gender = 0
    salt = random_salt()
    user_id = db.insert(
        conn,
        "blog_User",
        {
            "user_name": name,
            "user_password": hash_password(password, salt),
            "user_salt": salt,
            "user_groupID": group_id,
            "user_gender": gender,
            "user_email": email,
            "user_hideEmail": 1 if hide_email else 0,
            "user_homepage": homepage,
            "user_articleCount": 0,
            "user_commentCount": 0,
            "user_lastVisit": now_stamp(),
            "user_ip": "",
            "user_hashKey": "",
        },
    )
    conn.execute(
        "UPDATE blog_Settings SET set_value0 = set_value0 + 1 "
        "WHERE set_name = 'counterUser'"
    )
    conn.commit()
    created = public_user(conn, user_id)
    if not created:
        raise RuntimeError("user create failed")
    return created


def update_user(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    password: "str | None" = None,
    email: "str | None" = None,
    homepage: "str | None" = None,
    gender: "int | None" = None,
    hide_email: "bool | None" = None,
) -> dict[str, Any]:
    row = get_by_id(conn, user_id)
    if not row:
        raise ValueError("user_not_found")
    values: dict[str, Any] = {}
    if password:
        validate_password(password)
        salt = random_salt()
        values["user_password"] = hash_password(password, salt)
        values["user_salt"] = salt
    if email is not None:
        values["user_email"] = email
    if homepage is not None:
        values["user_homepage"] = homepage
    if gender is not None:
        values["user_gender"] = gender
    if hide_email is not None:
        values["user_hideEmail"] = 1 if hide_email else 0
    if values:
        db.update(conn, "blog_User", values, "user_id = ?", (user_id,))
        conn.commit()
    updated = public_user(conn, user_id)
    if not updated:
        raise RuntimeError("user update failed")
    return updated


def delete_user(conn: sqlite3.Connection, user_id: int) -> None:
    row = get_by_id(conn, user_id)
    if not row:
        raise ValueError("user_not_found")
    # Intentional deviation from class/user.asp: refuse to remove the last
    # administrator so a fresh install cannot lock itself out.
    if int(row["user_groupID"]) == 1:
        admins = int(
            db.scalar(
                conn, "SELECT COUNT(*) FROM blog_User WHERE user_groupID = 1"
            )
            or 0
        )
        if admins <= 1:
            raise ValueError("cannot_delete_last_admin")
    conn.execute("DELETE FROM blog_User WHERE user_id = ?", (user_id,))
    # Orphan the content the user wrote, exactly like lbsUser.doDelete.
    conn.execute("UPDATE blog_Article SET log_authorID = 0 WHERE log_authorID = ?", (user_id,))
    conn.execute("UPDATE blog_Comment SET comm_authorID = 0 WHERE comm_authorID = ?", (user_id,))
    conn.execute("UPDATE Guestbook SET gb_userID = 0 WHERE gb_userID = ?", (user_id,))
    conn.execute(
        "UPDATE blog_Settings SET set_value0 = MAX(set_value0 - 1, 0) "
        "WHERE set_name = 'counterUser'"
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Profile page helpers (port of source/src_user.asp)
# ---------------------------------------------------------------------------


def list_users_page(
    conn: sqlite3.Connection, *, page: int = 1, page_size: int = 40
) -> dict[str, Any]:
    total = int(db.scalar(conn, "SELECT COUNT(*) FROM blog_User") or 0)
    page = max(int(page or 1), 1)
    size = max(int(page_size or 40), 1)
    rows = db.query_all(
        conn,
        "SELECT * FROM blog_User "
        "ORDER BY user_articleCount DESC, user_commentCount DESC, user_lastVisit DESC "
        "LIMIT ? OFFSET ?",
        (size, (page - 1) * size),
    )
    groups = load_groups(conn)
    return {
        "items": [row_to_user(row, groups) for row in rows],
        "total": total,
        "page": page,
        "page_size": size,
        "pages": max((total + size - 1) // size, 1),
    }


def can_edit_profile(viewer: dict[str, Any], target_id: int) -> bool:
    """Self service, or an administrator editing anybody."""
    return viewer["id"] == target_id or viewer["group_id"] == 1


def validate_profile_form(
    conn: sqlite3.Connection,
    target: dict[str, Any],
    payload: dict,
    *,
    editor: dict[str, Any],
) -> "tuple[dict[str, Any] | None, list[str]]":
    """Port of ``editUserInfo`` + ``lbsUser.fillFromPost`` for edits."""
    import utils

    errors: list[str] = []
    old_password = str(payload.get("oldpassword") or "")
    if not utils.check_password(old_password):
        errors.append("old_password_invalid")
    else:
        # An administrator confirms with their own password, like the original.
        verifier_id = (
            editor["id"]
            if editor["group_id"] == 1 and editor["id"] != target["id"]
            else target["id"]
        )
        verifier = get_by_id(conn, verifier_id)
        if verifier is None:
            errors.append("user_not_found")
        else:
            salt = verifier["user_salt"] or ""
            if verifier["user_password"] != hash_password(old_password, salt):
                errors.append("old_password_invalid")

    values: dict[str, Any] = {}
    password = str(payload.get("password") or "")
    if password:
        repassword = str(payload.get("repassword") or "")
        if password != repassword or not utils.check_password(password):
            errors.append("password_invalid")
        else:
            salt = random_salt()
            values["user_password"] = hash_password(password, salt)
            values["user_salt"] = salt

    email = str(payload.get("email") or "")
    if email and not utils.check_email(email):
        errors.append("email_invalid")
    else:
        values["user_email"] = email
    values["user_hideEmail"] = 1 if payload.get("hideemail") else 0

    gender = payload.get("gender", 0)
    try:
        gender = int(gender)
    except (TypeError, ValueError):
        gender = 0
    values["user_gender"] = gender if 0 <= gender <= 2 else 0

    homepage = str(payload.get("homepage") or "")
    values["user_homepage"] = utils.check_url(homepage) if homepage else ""

    if editor["group_id"] == 1 and payload.get("groupID") is not None:
        group_id = 0
        try:
            group_id = int(payload.get("groupID"))
        except (TypeError, ValueError):
            group_id = 0
        if group_id in load_groups(conn):
            values["user_groupID"] = group_id

    if errors:
        return None, errors
    return values, errors


def update_profile(
    conn: sqlite3.Connection, target_id: int, values: dict[str, Any]
) -> dict[str, Any]:
    if not get_by_id(conn, target_id):
        raise ValueError("user_not_found")
    db.update(conn, "blog_User", values, "user_id = ?", (target_id,))
    conn.commit()
    updated = public_user(conn, target_id)
    if not updated:
        raise RuntimeError("user update failed")
    return updated
