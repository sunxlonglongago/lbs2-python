"""Session based authentication for the local web app.

A small blueprint plus a global ``before_app_request`` guard, with the
signing key stored next to the database in the runtime data directory.
"""

from __future__ import annotations

import os
import secrets
import time
from datetime import timedelta

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
    session,
)

import config
import cache
import db
import users

_PERMANENT_LIFETIME = timedelta(days=30)

# Endpoints reachable with any HTTP method (they authenticate themselves, or
# are harmless).
PUBLIC_PATHS = (
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/register",
    "/api/auth/me",
)

# Read only API endpoints a visitor may reach without logging in. The original
# blog is public for articles whose ``log_mode`` allows it, so the per object
# rules are enforced inside the handlers rather than by the guard.
PUBLIC_API_GET_PREFIXES = (
    "/api/site",
    "/api/health",
    "/api/lang",
    "/api/articles",
    "/api/categories",
    "/api/archive",
    "/api/stats",
    "/api/smilies",
    "/api/users",
    "/api/guestbook",
    "/api/trackbacks",
    "/api/comments",
)

auth_bp = Blueprint("auth", __name__)


def current_user():
    """Return the logged in user dict, or ``None``."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    with db.connection() as conn:
        return users.public_user(conn, int(user_id))


def is_public(path: str, method: str = "GET") -> bool:
    if path in PUBLIC_PATHS:
        return True
    # Guests may comment and sign the guestbook, exactly like the ASP version;
    # the handlers enforce the group rights.
    if method == "POST" and (path.endswith("/comments") or path == "/api/guestbook"):
        return True
    # Trackback pings arrive as GET or POST from other sites.
    if method == "POST" and path.startswith("/trackback"):
        return True
    if method not in ("GET", "HEAD"):
        return False
    # Pages and static assets are served to everyone; every write goes through
    # an API route that checks permissions itself.
    if not path.startswith("/api/"):
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_API_GET_PREFIXES)


def load_or_create_secret() -> bytes:
    """Read ``data/secret_key`` or create it with 32 random bytes (0600)."""
    data_dir = config.require_data_dir()
    path = data_dir / "secret_key"
    if path.is_file():
        return path.read_bytes()
    data_dir.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    path.write_bytes(key)
    path.chmod(0o600)
    return key


@auth_bp.post("/api/auth/login")
def api_login():
    data = request.get_json(silent=True) or {}
    name = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    remember = bool(data.get("remember"))
    if not name or not password:
        return jsonify({"ok": False, "error": "form_incomplete"}), 400

    # Port of the login failure brake in lbsUser.login (class/user.asp).
    # Note the JScript quirk: an unset loginban makes the comparison NaN, which
    # is falsy, so the counter is only cleared once a ban timestamp exists.
    now = time.time()
    ban_at = session.get("loginban")
    if ban_at is not None and now - float(ban_at) > 180:
        session.pop("loginfail", None)
        session.pop("loginban", None)
    if int(session.get("loginfail") or 0) > 3:
        session["loginban"] = now
        return jsonify({"ok": False, "error": "login_fail_ban"}), 429

    with db.connection() as conn:
        user = users.verify(conn, name, password)
        if user:
            users.touch_login(conn, user["id"], request.remote_addr or "")

    if not user:
        session["loginfail"] = int(session.get("loginfail") or 0) + 1
        return jsonify({"ok": False, "error": "login_fail"}), 401

    session.pop("loginfail", None)
    session.pop("loginban", None)
    session["user_id"] = user["id"]
    session.permanent = remember
    return jsonify({"ok": True, "user": user})


@auth_bp.post("/api/auth/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.get("/api/auth/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify({"ok": True, "user": None})
    return jsonify({"ok": True, "user": user})


@auth_bp.post("/api/auth/register")
def api_register():
    data = request.get_json(silent=True) or {}
    if session.get("registered"):
        return jsonify({"ok": False, "error": "reg_already"}), 403
    with db.connection() as conn:
        if not db.scalar(
            conn, "SELECT set_value0 FROM blog_Settings WHERE set_name = 'enableRegister'"
        ):
            return jsonify({"ok": False, "error": "register_disabled"}), 403
        password = str(data.get("password") or "")
        repassword = str(data.get("repassword") or "")
        if password != repassword:
            return jsonify({"ok": False, "error": "password_invalid"}), 400
        try:
            user = users.create_user(
                conn,
                str(data.get("username") or ""),
                password,
                email=str(data.get("email") or ""),
                homepage=str(data.get("homepage") or ""),
                gender=data.get("gender") or 0,
                hide_email=bool(data.get("hideemail")),
                filters=cache.word_filters(conn),
            )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    session["registered"] = True
    session["user_id"] = user["id"]
    return jsonify({"ok": True, "user": user})


@auth_bp.before_app_request
def guard():
    """Reject unauthenticated requests for every non public path."""
    if is_public(request.path, request.method):
        return None
    if session.get("user_id"):
        return None
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "login_required"}), 401
    return redirect(f"/login?next={request.path}")


def init_auth(app) -> None:
    app.config["SECRET_KEY"] = load_or_create_secret()
    app.config["PERMANENT_SESSION_LIFETIME"] = _PERMANENT_LIFETIME
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (
        os.environ.get("SESSION_COOKIE_SECURE", "1") not in ("0", "false", "no")
    )
    app.register_blueprint(auth_bp)
