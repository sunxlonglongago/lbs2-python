"""Article listing, visibility, drafts and article CRUD permissions."""

NAME = "articles"
DOC = "article list / visibility / write permissions"

CASES = [
    ("articles.list", "the index list returns the seed article and paging data"),
    ("articles.detail", "the detail returns body, merged comments and the view counter"),
    ("articles.create", "an administrator creates an article; [separator] sets has_more on the list"),
    ("articles.visibility", "a private article is 404 for guests and visible to the administrator"),
    ("articles.create_forbidden", "a regular user without post rights is refused"),
    ("articles.edit_forbidden", "a regular user cannot edit somebody else's article"),
    ("articles.delete", "a deleted article is no longer reachable"),
]


def run(ctx):
    ctx.case("articles.list")
    response, listing = ctx.get("anonymous", "/api/articles")
    ctx.check_status(response, 200, "the index list is reachable")
    ctx.check(listing.get("total", 0) >= 1, "there is at least the seed article")
    first = listing["items"][0]
    ctx.check(bool(first.get("content_html")), "the list carries rendered bodies")
    ctx.check("page_links" in listing, "the list carries pagination HTML")
    article_id = first["id"]
    category_id = first["category"]["id"]

    ctx.case("articles.detail")
    response, payload = ctx.get("anonymous", f"/api/articles/{article_id}")
    ctx.check_status(response, 200, "the article detail is reachable")
    ctx.check(bool(payload["article"].get("content_html")), "the detail carries content_html")
    ctx.check("items" in payload["comments"], "the detail carries the comment list")
    ctx.check(payload["article"]["view_count"] >= 1, "the view counter was incremented")

    ctx.login("admin", "Admin", "comeon")

    ctx.case("articles.create")
    response, payload = ctx.post(
        "admin",
        "/api/articles",
        json={
            "log_catid": category_id,
            "log_mode": 1,
            "log_title": "E2E Public Post",
            "message": "first part[separator]second part",
            "log_postTime": "2026-01-02 03:04:05",
            "log_selected": True,
            "e_ubb": True,
            "e_autourl": True,
        },
    )
    ctx.check_status(response, 200, "an administrator creates an article")
    created_id = payload["id"]
    _, listing = ctx.get("anonymous", "/api/articles")
    entry = next(item for item in listing["items"] if item["id"] == created_id)
    ctx.check(entry["has_more"] is True, "[separator] sets has_more on the list")
    ctx.check_equal(entry["post_time"], "2026-01-02 03:04:05", "the post time comes from the form")
    ctx.check(entry["selected"] is True, "the featured flag is stored")

    ctx.case("articles.visibility")
    response, payload = ctx.post(
        "admin",
        "/api/articles",
        json={
            "log_catid": category_id,
            "log_mode": 4,
            "log_title": "E2E Private Note",
            "message": "hidden from guests",
            "e_ubb": True,
        },
    )
    ctx.check_status(response, 200, "an administrator can create a private article")
    private_id = payload["id"]
    _, guest_listing = ctx.get("anonymous", "/api/articles")
    ctx.check(
        all(item["id"] != private_id for item in guest_listing["items"]),
        "a private article stays out of the guest list",
    )
    response, _ = ctx.get("anonymous", f"/api/articles/{private_id}")
    ctx.check_status(response, 404, "a guest hitting the private article gets 404")
    _, admin_listing = ctx.get("admin", "/api/articles")
    ctx.check(
        any(item["id"] == private_id for item in admin_listing["items"]),
        "the private article shows up for the administrator",
    )

    ctx.case("articles.create_forbidden")
    # the users scenario changes the password, so try both when articles runs alone.
    if ctx.login("newbie", "newbie", "secret123")[0].status_code != 200:
        ctx.login("newbie", "newbie", "brandnew123")
    response, payload = ctx.post(
        "newbie",
        "/api/articles",
        json={
            "log_catid": category_id,
            "log_mode": 1,
            "log_title": "Nope",
            "message": "nope",
        },
    )
    ctx.check_status(response, 403, "the Registered group cannot post")
    ctx.check_equal((payload or {}).get("error"), "no_rights", "error code is no_rights")

    ctx.case("articles.edit_forbidden")
    response, _ = ctx.patch(
        "newbie",
        f"/api/articles/{created_id}",
        json={
            "log_catid": category_id,
            "log_mode": 1,
            "log_title": "Hacked",
            "message": "hacked",
        },
    )
    ctx.check_status(response, 403, "a third party cannot edit the article")

    ctx.case("articles.delete")
    response, _ = ctx.delete("admin", f"/api/articles/{created_id}")
    ctx.check_status(response, 200, "an administrator deletes the article")
    response, _ = ctx.get("anonymous", f"/api/articles/{created_id}")
    ctx.check_status(response, 404, "the deleted article is unreachable")
    ctx.delete("admin", f"/api/articles/{private_id}")
