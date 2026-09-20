"""Trackback ping receive, listing and deletion."""

NAME = "trackback"
DOC = "trackbacks: receiving pings, de-duplication, listing, deletion"

CASES = [
    ("trackback.list", "the trackback list is public"),
    ("trackback.ping", "an external ping is accepted with error 0"),
    ("trackback.duplicate", "a ping with the same title and excerpt is de-duplicated"),
    ("trackback.invalid", "missing parameters or a missing article return an error"),
    ("trackback.delete", "an administrator deletes a trackback"),
]


def run(ctx):
    _, listing = ctx.get("anonymous", "/api/articles")
    article_id = listing["items"][0]["id"]

    ctx.case("trackback.list")
    response, payload = ctx.get("anonymous", "/api/trackbacks")
    ctx.check_status(response, 200, "the trackback list is reachable")
    ctx.check("items" in payload, "the trackback list is complete")

    ctx.case("trackback.invalid")
    response, _ = ctx.get("anonymous", "/trackback/999999?url=http://example.org/x")
    ctx.check_status(response, 200, "the ping always answers 200 with XML")
    ctx.check(
        b"<error>1</error>" in response.data,
        "a missing article returns error 1",
    )
    # a bare GET is the list page; only a parameterless ping (POST) returns the XML error.
    response, _ = ctx.post("anonymous", "/trackback", data={})
    ctx.check(b"Invalid Parameter" in response.data, "a ping without id/url returns Invalid Parameter")

    ctx.case("trackback.ping")
    query = (
        f"/trackback/{article_id}?url=http://example.org/e2e&title=E2E%20Ping"
        "&excerpt=E2E%20excerpt&blog_name=E2E%20Blog"
    )
    response, _ = ctx.get("anonymous", query)
    ctx.check(b"<error>0</error>" in response.data, "the first ping is accepted")
    response, _ = ctx.post(
        "anonymous",
        f"/trackback/{article_id}",
        data={
            "url": "http://example.org/e2e-post",
            "title": "E2E Ping Post",
            "excerpt": "E2E excerpt post",
            "blog_name": "E2E Form Blog",
        },
    )
    ctx.check(b"<error>0</error>" in response.data, "the POST form ping is accepted")

    ctx.case("trackback.duplicate")
    response, _ = ctx.get("anonymous", query)
    ctx.check(b"Trackback is already saved" in response.data, "a duplicate ping is refused")

    _, payload = ctx.get("anonymous", "/api/trackbacks")
    entry = next(item for item in payload["items"] if item["title"] == "E2E Ping")
    ctx.check_equal(entry["article_id"], article_id, "the trackback hangs off the target article")
    ctx.check(bool(entry["excerpt_html"]), "the excerpt is rendered")

    ctx.case("trackback.delete")
    ctx.login("admin", "Admin", "comeon")
    response, _ = ctx.delete("admin", f"/api/trackbacks/{entry['id']}")
    ctx.check_status(response, 200, "the administrator deletes the trackback")
    _, payload = ctx.get("anonymous", "/api/trackbacks")
    ctx.check(all(item["id"] != entry["id"] for item in payload["items"]), "the trackback is gone")
