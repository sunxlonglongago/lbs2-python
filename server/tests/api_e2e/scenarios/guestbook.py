"""Guestbook: guest entries, replies, visibility and deletion."""

NAME = "guestbook"
DOC = "guestbook: guest entries, admin reply, deletion"

CASES = [
    ("guestbook.list", "the guestbook list is public"),
    ("guestbook.post", "a guest signs the guestbook"),
    ("guestbook.edit", "an administrator edits an entry and writes a reply"),
    ("guestbook.delete", "an administrator deletes an entry"),
]


def run(ctx):
    ctx.case("guestbook.list")
    response, listing = ctx.get("anonymous", "/api/guestbook")
    ctx.check_status(response, 200, "the guestbook list is reachable")
    ctx.check("items" in listing and "page_links" in listing, "the guestbook list is complete")
    ctx.check("can_post" in listing, "the response says whether posting is allowed")

    ctx.case("guestbook.post")
    response, payload = ctx.post(
        "bookguest",
        "/api/guestbook",
        json={
            "message": "E2E guestbook entry",
            "comm_username": "bookguest",
            "e_ubb": True,
            "e_autourl": True,
            "e_smilies": True,
        },
    )
    ctx.check_status(response, 200, "the guest entry is stored")
    entry_id = payload["id"]

    ctx.case("guestbook.edit")
    ctx.login("admin", "Admin", "comeon")
    response, entry = ctx.get("admin", f"/api/guestbook/{entry_id}")
    ctx.check_status(response, 200, "an administrator can read the raw entry")
    ctx.check(
        (entry or {}).get("entry", {}).get("show_reply_area") is True,
        "with edit>2 the reply area is exposed",
    )
    response, _ = ctx.patch(
        "admin",
        f"/api/guestbook/{entry_id}",
        json={
            "entry": "E2E guestbook entry",
            "message": "Thanks for signing",
            "e_ubb": True,
        },
    )
    ctx.check_status(response, 200, "the administrator edits and replies")
    _, detail = ctx.get("anonymous", f"/api/guestbook")
    target = next(item for item in detail["items"] if item["id"] == entry_id)
    ctx.check(target["has_reply"] is True, "the reply was stored")
    ctx.check("Thanks for signing" in target["reply_html"], "the reply body matches")
    ctx.check_equal(target["edit_mark"], "", "an unchanged body keeps the edit mark empty")

    ctx.case("guestbook.delete")
    response, _ = ctx.delete("admin", f"/api/guestbook/{entry_id}")
    ctx.check_status(response, 200, "the administrator deletes the entry")
    _, detail = ctx.get("anonymous", "/api/guestbook")
    ctx.check(
        all(item["id"] != entry_id for item in detail["items"]),
        "the deleted entry no longer shows up",
    )
