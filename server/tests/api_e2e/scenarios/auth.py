"""Login, logout, registration and the login failure brake."""

NAME = "auth"
DOC = "login / logout / registration / login brake"

CASES = [
    ("auth.me", "anonymous and logged-in /api/auth/me"),
    ("auth.login", "administrator logs in and gets the rights block"),
    ("auth.bad_password", "a wrong password returns login_fail"),
    ("auth.login_ban", "the fifth failure in one session triggers the temporary ban"),
    ("auth.register", "register a new user and log in automatically"),
    ("auth.register_duplicate", "a duplicate user name is refused"),
    ("auth.logout", "the session is gone after logout"),
]


def run(ctx):
    ctx.case("auth.me")
    response, payload = ctx.get("anonymous", "/api/auth/me")
    ctx.check_status(response, 200, "anonymous me is reachable")
    ctx.check(payload and payload.get("user") is None, "anonymous me returns no user")

    ctx.case("auth.login")
    response, payload = ctx.login("admin", "Admin", "comeon")
    ctx.check_status(response, 200, "administrator logs in")
    user = (payload or {}).get("user", {})
    ctx.check_equal(user.get("group_id"), 1, "administrator is in user_groupID=1")
    ctx.check_equal(user.get("rights", {}).get("view"), 9, "the Admin group has view level 9")

    _, payload = ctx.get("admin", "/api/auth/me")
    ctx.check(payload and payload["user"]["name"] == "Admin", "the logged-in me returns Admin")

    ctx.case("auth.bad_password")
    response, payload = ctx.login("baduser", "Admin", "wrong-password")
    ctx.check_status(response, 401, "a wrong password is refused")
    ctx.check_equal((payload or {}).get("error"), "login_fail", "error code is login_fail")

    ctx.case("auth.login_ban")
    for _ in range(4):
        ctx.post("ban", "/api/auth/login", json={"username": "Admin", "password": "nope"})
    response, payload = ctx.post(
        "ban", "/api/auth/login", json={"username": "Admin", "password": "nope"}
    )
    ctx.check_status(response, 429, "the fifth failure triggers the ban")
    ctx.check_equal((payload or {}).get("error"), "login_fail_ban", "error code is login_fail_ban")

    ctx.case("auth.register")
    response, payload = ctx.post(
        "newbie",
        "/api/auth/register",
        json={
            "username": "newbie",
            "password": "secret123",
            "repassword": "secret123",
            "email": "newbie@example.com",
            "gender": 1,
        },
    )
    ctx.check_status(response, 200, "registration succeeds")
    user = (payload or {}).get("user", {})
    ctx.check_equal(user.get("group_name"), "Registered", "the new user lands in the Registered group")
    ctx.check(user.get("id", 0) > 0, "registration returns a user id")

    ctx.case("auth.register_duplicate")
    response, payload = ctx.post(
        "other",
        "/api/auth/register",
        json={"username": "newbie", "password": "secret123", "repassword": "secret123"},
    )
    ctx.check_status(response, 400, "a duplicate user name is refused")
    ctx.check_equal((payload or {}).get("error"), "user_exist", "error code is user_exist")

    ctx.case("auth.logout")
    response, _ = ctx.post("newbie", "/api/auth/logout")
    ctx.check_status(response, 200, "logout succeeds")
    _, payload = ctx.get("newbie", "/api/auth/me")
    ctx.check(payload and payload.get("user") is None, "me returns no user after logout")
