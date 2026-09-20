"""Admin backend: second login gate, settings rules, maintenance operations."""

NAME = "admin"
DOC = "admin: second login, settings validation, database and maintenance"

CASES = [
    ("admin.gate", "non-admins and sessions without the second login are blocked"),
    ("admin.login", "admin login: wrong password refused, right password accepted"),
    ("admin.settings", "settings follow the original rules (exclusive bounds, empty strings skipped)"),
    ("admin.categories", "rename and add categories"),
    ("admin.groups", "add a user group and check the rights digits"),
    ("admin.database", "backup and compact"),
    ("admin.misc", "recompute counters and clean up"),
    ("admin.site_state", "close and open the site"),
]


def run(ctx):
    ctx.case("admin.gate")
    response, payload = ctx.get("anonymous", "/api/admin/info")
    ctx.check_status(response, 401, "anonymous access hits the login guard")
    ctx.login("newbie", "newbie", "brandnew123")
    response, payload = ctx.get("newbie", "/api/admin/info")
    ctx.check_status(response, 403, "a logged-in non-admin gets 403")
    ctx.check_equal((payload or {}).get("error"), "no_rights", "error code is no_rights")
    ctx.login("admin", "Admin", "comeon")
    response, payload = ctx.get("admin", "/api/admin/info")
    ctx.check_status(response, 403, "the site login alone is not enough, a second login is required")
    ctx.check_equal((payload or {}).get("error"), "admin_login", "error code is admin_login")

    ctx.case("admin.login")
    response, payload = ctx.admin_login("admin", "wrong")
    ctx.check_status(response, 401, "a wrong admin password is refused")
    ctx.check_equal((payload or {}).get("error"), "password_invalid", "error code is password_invalid")
    response, _ = ctx.admin_login("admin", "comeon")
    ctx.check_status(response, 200, "the admin login succeeds")
    response, info = ctx.get("admin", "/api/admin/info")
    ctx.check_status(response, 200, "the admin info can be read")
    ctx.check("counters" in info and "database" in info, "the info carries counters and database details")

    ctx.case("admin.settings")
    response, payload = ctx.post(
        "admin",
        "/api/admin/settings",
        json={
            "blogtitle": "E2E Title",
            "articleperpagenormal": 10,
            "articleperpagelist": 500,
            "blogdescription": "",
        },
    )
    ctx.check_status(response, 200, "the settings are saved")
    written = (payload or {}).get("written", [])
    ctx.check("blogtitle" in written, "string settings are written")
    ctx.check("articleperpagelist" not in written, "out of range integers are skipped")
    ctx.check("blogdescription" not in written, "empty strings are skipped")
    _, settings = ctx.get("admin", "/api/admin/settings")
    ctx.check_equal(settings["settings"]["blogTitle"], "E2E Title", "the title is updated")
    ctx.check_equal(settings["settings"]["articlePerPageNormal"], 10, "a valid integer is updated")
    ctx.check_equal(settings["settings"]["articlePerPageList"], 40, "an out of range integer keeps its value")
    ctx.post("admin", "/api/admin/settings", json={"blogtitle": "LBS^2"})

    ctx.case("admin.categories")
    _, data = ctx.get("admin", "/api/admin/categories")
    existing = data["categories"]
    names = [item["name"] for item in existing] + ["E2E Category"]
    orders = [item["order"] for item in existing] + [len(existing) + 1]
    ids = [item["id"] for item in existing] + [0]
    response, payload = ctx.post(
        "admin",
        "/api/admin/categories",
        json={"act": "update", "id": ids, "name": names, "order": orders},
    )
    ctx.check_status(response, 200, "the categories are saved")
    _, data = ctx.get("admin", "/api/admin/categories")
    ctx.check(
        any(item["name"] == "E2E Category" for item in data["categories"]),
        "the new category exists",
    )

    ctx.case("admin.groups")
    response, payload = ctx.post(
        "admin",
        "/api/admin/groups",
        json={
            "act": "update",
            "id": [0],
            "name": ["E2E Group"],
            "view": [2],
            "post": [2],
            "edit": [1],
            "delete": [1],
            "upload": [0],
        },
    )
    ctx.check_status(response, 200, "the user group is saved")
    _, data = ctx.get("admin", "/api/admin/groups")
    group = next((item for item in data["groups"] if item["name"] == "E2E Group"), None)
    ctx.check(group is not None, "the new group exists")
    ctx.check_equal((group or {}).get("rights"), "22110", "the rights string is five digits")

    ctx.case("admin.database")
    response, payload = ctx.post("admin", "/api/admin/database", json={"act": "backup"})
    ctx.check_status(response, 200, "the backup succeeds")
    ctx.check((payload or {}).get("name", "").endswith(".bak"), "the backup file ends in .bak")
    response, payload = ctx.post("admin", "/api/admin/database", json={"act": "compact"})
    ctx.check_status(response, 200, "compaction succeeds")
    response, payload = ctx.post(
        "admin", "/api/admin/database", json={"act": "delete", "file": "nope.bak"}
    )
    ctx.check_status(response, 400, "a missing backup file is refused")

    ctx.case("admin.misc")
    response, payload = ctx.post("admin", "/api/admin/misc", json={"act": "resync_g"})
    ctx.check_status(response, 200, "the global counters are recomputed")
    counters = (payload or {}).get("counters", {})
    ctx.check(counters.get("counterArticle", 0) >= 1, "the article counter was recomputed")
    response, payload = ctx.post("admin", "/api/admin/misc", json={"act": "resync_c"})
    ctx.check_status(response, 200, "the category counters are recomputed")
    response, payload = ctx.post("admin", "/api/admin/misc", json={"act": "clean_vc"})
    ctx.check_status(response, 200, "the visitor records are cleaned")

    ctx.case("admin.site_state")
    response, payload = ctx.post("admin", "/api/admin/site-state", json={"closed": True})
    ctx.check_status(response, 200, "closing the site succeeds")
    ctx.check_equal((payload or {}).get("closed"), True, "the closed state is returned")
    _, site = ctx.get("anonymous", "/api/site")
    ctx.check_equal(site["site"]["closed"], True, "site metadata reflects the closed state")
    ctx.post("admin", "/api/admin/site-state", json={"closed": False})
