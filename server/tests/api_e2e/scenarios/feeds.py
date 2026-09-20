"""RSS, JavaScript and site metadata endpoints."""

NAME = "feeds"
DOC = "site metadata / language pack / RSS / JS output"

CASES = [
    ("feeds.site", "site metadata carries theme paths, switches, sidebar and announcement"),
    ("feeds.lang", "the language pack covers the keys the frontend uses"),
    ("feeds.rss", "the article RSS is well formed"),
    ("feeds.comment_rss", "the comment RSS filters by article"),
    ("feeds.js", "type=js emits a document.write snippet"),
    ("feeds.categories", "the category and calendar endpoints"),
]


def run(ctx):
    ctx.case("feeds.site")
    response, payload = ctx.get("anonymous", "/api/site")
    ctx.check_status(response, 200, "site metadata is reachable")
    site = payload["site"]
    for key in ("title", "description", "style_sheet", "image_folder", "features"):
        ctx.check(key in site, f"site metadata carries {key}")
    ctx.check("sidebar" in payload and "calendar_html" in payload["sidebar"], "the sidebar payload is complete")
    ctx.check("announcement" in payload, "the announcement is present")
    ctx.check_equal(payload["site"]["language"], "en", "the UI language is English")

    ctx.case("feeds.lang")
    response, payload = ctx.get("anonymous", "/api/lang")
    strings = payload["strings"]
    ctx.check_status(response, 200, "the language pack is reachable")
    for key in ("index", "guestbook", "login", "post_comment", "admin_panel"):
        ctx.check(key in strings, f"the language pack carries {key}")

    ctx.case("feeds.rss")
    response, _ = ctx.get("anonymous", "/feed")
    body = response.get_data(as_text=True)
    ctx.check_status(response, 200, "the RSS feed is reachable")
    ctx.check(body.startswith("<?xml"), "the RSS starts with an XML declaration")
    ctx.check("<rss version=\"2.0\"" in body, "it is RSS 2.0")
    ctx.check("<ttl>60</ttl>" in body, "it carries a ttl")
    ctx.check("<item>" in body, "it carries an item")
    ctx.check("wfw:commentRss" in body, "it carries the comment feed URL")

    ctx.case("feeds.comment_rss")
    _, listing = ctx.get("anonymous", "/api/articles")
    article_id = listing["items"][0]["id"]
    response, _ = ctx.get("anonymous", f"/feed?q=comment&id={article_id}")
    body = response.get_data(as_text=True)
    ctx.check_status(response, 200, "the comment RSS is reachable")
    ctx.check("Comment on" in body, "the comment item title matches the original format")

    ctx.case("feeds.js")
    response, _ = ctx.get("anonymous", "/feed?type=js")
    body = response.get_data(as_text=True)
    ctx.check_status(response, 200, "the JS output is reachable")
    ctx.check(body.startswith("// LBS v"), "the JS output starts with the version comment")
    ctx.check("document.write" in body, "it emits document.write")

    ctx.case("feeds.categories")
    response, payload = ctx.get("anonymous", "/api/categories")
    ctx.check_status(response, 200, "the category endpoint is reachable")
    ctx.check(payload["categories"], "there is at least one category")
    response, payload = ctx.get("anonymous", "/api/archive")
    ctx.check_status(response, 200, "the calendar endpoint is reachable")
    ctx.check("id=\"calendar\"" in payload["html"], "the calendar HTML matches the theme markup")
