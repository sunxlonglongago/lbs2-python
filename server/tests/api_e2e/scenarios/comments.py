"""Comment posting: guests, members, validation, word filter, flood control."""

NAME = "comments"
DOC = "comments: guests and members, validation, word filter, flood control"

CASES = [
    ("comments.guest_requires_name", "a guest without a name is refused"),
    ("comments.guest", "a guest posts under a display name"),
    ("comments.member", "a logged-in user posts a hidden comment"),
    ("comments.visibility", "comments show up in the article detail with the hidden flag"),
    ("comments.validation", "empty and oversized comments are refused"),
    ("comments.wordfilter", "a word filter hit is replaced as configured"),
    ("comments.flood", "posting again too soon is refused"),
]


def run(ctx):
    _, listing = ctx.get("anonymous", "/api/articles")
    article_id = listing["items"][0]["id"]
    ctx.login("admin", "Admin", "comeon")

    # Validation first: a successful post starts the flood control window.
    ctx.case("comments.validation")
    response, payload = ctx.post(
        "admin", f"/api/articles/{article_id}/comments", json={"message": ""}
    )
    ctx.check_status(response, 400, "an empty comment is refused")
    ctx.check_equal((payload or {}).get("error"), "content_blank", "error code is content_blank")
    response, payload = ctx.post(
        "admin", f"/api/articles/{article_id}/comments", json={"message": "x" * 5000}
    )
    ctx.check_status(response, 400, "an oversized comment is refused")
    ctx.check_equal((payload or {}).get("error"), "length_invalid", "error code is length_invalid")

    ctx.case("comments.guest_requires_name")
    response, payload = ctx.post(
        "guest1", f"/api/articles/{article_id}/comments", json={"message": "no name"}
    )
    ctx.check_status(response, 400, "a guest without a name is refused")
    ctx.check_equal((payload or {}).get("error"), "username_invalid", "error code is username_invalid")

    ctx.case("comments.guest")
    response, payload = ctx.post(
        "guest1",
        f"/api/articles/{article_id}/comments",
        json={
            "message": "Hello from a visitor",
            "comm_username": "visitor1",
            "e_ubb": True,
            "e_autourl": True,
            "e_smilies": True,
        },
    )
    ctx.check_status(response, 200, "the guest comment is stored")
    guest_comment = payload["id"]

    ctx.case("comments.member")
    response, payload = ctx.post(
        "admin",
        f"/api/articles/{article_id}/comments",
        json={"message": "Admin reply", "comm_hidden": True, "e_ubb": True},
    )
    ctx.check_status(response, 200, "the member comment is stored")
    member_comment = payload["id"]

    ctx.case("comments.visibility")
    _, detail = ctx.get("admin", f"/api/articles/{article_id}")
    comments = [item for item in detail["comments"]["items"] if item["type"] == 0]
    authors = [item["author"] for item in comments]
    ctx.check("visitor1" in authors, "the guest comment shows up in the list")
    ctx.check("Admin" in authors, "the admin comment shows up in the list")
    ctx.check(any(item["hidden"] for item in comments), "the hidden comment is flagged")
    ctx.check(
        any(item["author_id"] == 0 for item in comments),
        "a guest comment has author_id 0",
    )

    ctx.case("comments.wordfilter")
    response, _ = ctx.post(
        "filter1",
        f"/api/articles/{article_id}/comments",
        json={"message": "say helloworld now", "comm_username": "filteruser"},
    )
    ctx.check_status(response, 200, "the comment passes in replace mode")
    _, detail = ctx.get("anonymous", f"/api/articles/{article_id}")
    contents = [item.get("content_html", "") for item in detail["comments"]["items"]]
    ctx.check(any("Hello World" in content for content in contents), "the word filter replaced the text")

    ctx.case("comments.flood")
    response, payload = ctx.post(
        "filter1",
        f"/api/articles/{article_id}/comments",
        json={"message": "second post", "comm_username": "filteruser"},
    )
    ctx.check_status(response, 429, "flood control kicks in")
    ctx.check_equal((payload or {}).get("error"), "flood_control", "error code is flood_control")

    ctx.delete("admin", f"/api/comments/{guest_comment}")
    ctx.delete("admin", f"/api/comments/{member_comment}")
