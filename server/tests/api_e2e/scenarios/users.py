"""User list, profile edits, password change and deletion rules."""

NAME = "users"
DOC = "user list / profile edits / password change / deletion rules"

CASES = [
    ("users.list", "the user list is public but hides emails"),
    ("users.profile", "the profile returns the group name and rights"),
    ("users.update_wrong_password", "a wrong current password blocks the save"),
    ("users.update", "the new password works after the change"),
    ("users.group_change", "changing the group changes the rights"),
    ("users.delete_last_admin", "deleting the last administrator is refused"),
]


def run(ctx):
    ctx.case("users.list")
    response, listing = ctx.get("anonymous", "/api/users")
    ctx.check_status(response, 200, "the user list is reachable")
    ctx.check(listing["total"] >= 2, "it holds the seed user and the registered one")
    admin = next(item for item in listing["items"] if item["name"] == "Admin")
    ctx.check(admin["email_visible"] is False, "emails stay hidden from guests")

    ctx.case("users.profile")
    response, payload = ctx.get("anonymous", f"/api/users/{admin['id']}")
    ctx.check_status(response, 200, "the profile page is reachable")
    ctx.check_equal(payload["user"]["group_name"], "Admin", "the group name is returned")
    ctx.check(payload["user"]["rights"]["view"] == 9, "the expanded rights are returned")

    newbie_id = next(
        item["id"] for item in listing["items"] if item["name"] == "newbie"
    )

    ctx.case("users.update_wrong_password")
    ctx.login("newbie", "newbie", "secret123")
    response, payload = ctx.patch(
        "newbie",
        f"/api/users/{newbie_id}",
        json={"oldpassword": "not-my-password", "email": "x@example.com"},
    )
    ctx.check_status(response, 400, "a wrong current password is refused")
    ctx.check_equal((payload or {}).get("error"), "old_password_invalid", "error code is old_password_invalid")

    ctx.case("users.update")
    response, payload = ctx.patch(
        "newbie",
        f"/api/users/{newbie_id}",
        json={
            "oldpassword": "secret123",
            "password": "brandnew123",
            "repassword": "brandnew123",
            "email": "newbie2@example.com",
            "homepage": "http://example.com/newbie",
            "gender": 2,
            "hideemail": True,
        },
    )
    ctx.check_status(response, 200, "the profile is saved")
    user = (payload or {}).get("user", {})
    ctx.check_equal(user.get("email"), "newbie2@example.com", "the email is updated")
    ctx.check_equal(user.get("gender"), 2, "the gender is updated")
    ctx.check_equal(user.get("hide_email"), True, "the hide-email flag is updated")
    response, _ = ctx.post("other", "/api/auth/login", json={"username": "newbie", "password": "brandnew123"})
    ctx.check_status(response, 200, "the new password logs in")

    ctx.case("users.group_change")
    ctx.login("admin", "Admin", "comeon")
    response, payload = ctx.patch(
        "admin",
        f"/api/users/{newbie_id}",
        json={"oldpassword": "comeon", "groupID": 4},
    )
    ctx.check_status(response, 200, "an administrator changes the group")
    ctx.check_equal(
        (payload or {}).get("user", {}).get("group_name"), "Author", "the group becomes Author"
    )
    ctx.check_equal(
        (payload or {}).get("user", {}).get("rights", {}).get("post"), 2, "the post right follows the group"
    )

    ctx.case("users.delete_last_admin")
    response, payload = ctx.delete("admin", f"/api/users/{admin['id']}")
    ctx.check_status(response, 400, "deleting the last administrator is refused")
    ctx.check_equal(
        (payload or {}).get("error"), "cannot_delete_last_admin",
        "the error code explains why",
    )
