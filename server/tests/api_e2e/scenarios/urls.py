"""URL shape: every route is reachable as .asp, real .html files stay put."""

import re

NAME = "urls"
DOC = "URL shape: pages and API all end in .asp"

CASES = [
    ("urls.root", "the root redirects to default.asp"),
    ("urls.pages", "every page entry point is served as .asp"),
    ("urls.api_suffix", "API paths behave the same with and without .asp"),
    ("urls.api_items", "API paths with parameters accept .asp too"),
    ("urls.html_redirect", ".html pages 302 to their .asp form"),
    ("urls.upload", "upload.asp serves the upload page, upload.html redirects to it"),
    ("urls.no_html_pages", "no .html page URLs are exposed"),
    ("urls.panel_wiring", "sidebar element ids line up with the layout.js fill code"),
    ("urls.feed", "feed.asp and trackback.asp work"),
]

PAGES = (
    "default.asp",
    "article.asp",
    "user.asp",
    "gbook.asp",
    "login.asp",
    "register.asp",
    "stats.asp",
    "about.asp",
    "admin.asp",
    "comment.asp",
    "trackback.asp",
    "upload.asp",
)

API_SAMPLES = (
    "/api/site",
    "/api/lang",
    "/api/health",
    "/api/articles",
    "/api/categories",
    "/api/archive",
    "/api/stats",
    "/api/trackbacks",
    "/api/guestbook",
    "/api/users",
)


def run(ctx):
    ctx.case("urls.root")
    response, _ = ctx.get("anonymous", "/")
    ctx.check_status(response, 302, "the root path redirects")
    ctx.check(
        response.headers.get("Location", "").endswith("/default.asp"),
        "the root path points at /default.asp",
    )

    ctx.case("urls.pages")
    for page in PAGES:
        response, _ = ctx.get("anonymous", "/" + page)
        ctx.check_status(response, 200, f"{page} is reachable")
        body = response.get_data(as_text=True)
        ctx.check("<!DOCTYPE" in body or "<html" in body, f"{page} returns HTML")

    ctx.case("urls.api_suffix")
    for path in API_SAMPLES:
        plain, plain_payload = ctx.get("anonymous", path)
        suffixed, suffixed_payload = ctx.get("anonymous", path + ".asp")
        ctx.check_status(suffixed, 200, f"{path}.asp is reachable")
        ctx.check_equal(
            suffixed_payload.get("ok") if suffixed_payload else None,
            plain_payload.get("ok") if plain_payload else None,
            f"{path}.asp and {path} agree",
        )

    ctx.case("urls.api_items")
    _, listing = ctx.get("anonymous", "/api/articles.asp")
    article_id = listing["items"][0]["id"]
    response, payload = ctx.get("anonymous", f"/api/articles/{article_id}.asp")
    ctx.check_status(response, 200, "the article detail accepts .asp")
    ctx.check_equal(payload["article"]["id"], article_id, "the detail returns the same article")
    response, payload = ctx.get("anonymous", f"/api/guestbook.asp")
    ctx.check_status(response, 200, "the guestbook list accepts .asp")
    response, payload = ctx.get("anonymous", f"/api/users/{1}.asp")
    ctx.check_status(response, 200, "the user profile accepts .asp")

    ctx.case("urls.html_redirect")
    for page, target in (
        ("index.html", "/default.asp"),
        ("article.html", "/article.asp"),
        ("admin.html", "/admin.asp"),
        ("stats.html", "/stats.asp"),
    ):
        response, _ = ctx.get("anonymous", "/" + page)
        ctx.check_status(response, 302, f"{page} redirects")
        location = response.headers.get("Location", "")
        ctx.check(
            location.endswith(target),
            f"{page} points at {target} (got {location})",
        )
    response, _ = ctx.get("anonymous", "/article.html?id=3")
    ctx.check(
        "id=3" in response.headers.get("Location", ""),
        "the redirect keeps the query string",
    )

    ctx.case("urls.upload")
    response, _ = ctx.get("anonymous", "/upload.asp")
    ctx.check_status(response, 200, "upload.asp serves the upload page")
    ctx.check(
        "upload-page" in response.get_data(as_text=True),
        "upload.asp is the upload page itself",
    )
    response, _ = ctx.get("anonymous", "/upload.html")
    ctx.check_status(response, 302, "upload.html redirects")
    ctx.check(
        response.headers.get("Location", "").endswith("/upload.asp"),
        "upload.html points at /upload.asp",
    )

    ctx.case("urls.feed")
    response, _ = ctx.get("anonymous", "/feed.asp")
    ctx.check_status(response, 200, "feed.asp works")
    ctx.check(
        response.get_data(as_text=True).startswith("<?xml"),
        "feed.asp returns RSS",
    )
    response, _ = ctx.get("anonymous", "/trackback.asp?id=1&url=http://example.org/urls")
    ctx.check_status(response, 200, "trackback.asp works")
    ctx.check(b"<response>" in response.data, "trackback.asp returns trackback XML")
    response, _ = ctx.get("anonymous", "/trackback.asp?act=list")
    ctx.check_status(response, 200, "trackback.asp?act=list serves the list page")
    ctx.check(
        "Trackbacks" in response.get_data(as_text=True),
        "trackback.asp?act=list is a page, not XML",
    )

    ctx.case("urls.no_html_pages")
    for page in (
        "index.html",
        "article.html",
        "comment.html",
        "gbook.html",
        "login.html",
        "register.html",
        "stats.html",
        "about.html",
        "user.html",
        "admin.html",
        "trackback.html",
        "upload.html",
    ):
        response, _ = ctx.get("anonymous", "/" + page)
        ctx.check_status(response, 302, f"{page} is not served directly, it redirects to .asp")

    ctx.case("urls.panel_wiring")
    # The sidebar is a static skeleton filled in by JS; a wrong id only shows up as a
    # blank panel, which API level tests cannot catch.
    page = ctx.get("anonymous", "/default.asp")[0].get_data(as_text=True)
    script = ctx.get("anonymous", "/js/app/layout.js")[0].get_data(as_text=True)
    for element_id in (
        "searchForm",
        "searchType",
        "searchSubmit",
        "panelUserTitle",
        "panelUserLinks",
        "panelCategoryList",
        "panelCalendarBody",
        "panelArticleList",
        "panelCommentList",
        "panelStatsList",
        "panelLinksBody",
    ):
        ctx.check(f'id="{element_id}"' in page, f"{element_id} appears in the page skeleton")
        # Either a JS literal ('id') or an id="..." inside the template counts as wired;
        # a plain substring match would miss prefix collisions like searchTypeOptions.
        wired = f"'{element_id}'" in script or f'id="{element_id}"' in script
        ctx.check(wired, f"layout.js has fill code for {element_id}")
    options = re.search(r'<option value="articles">', page)
    ctx.check(options is None, "the search dropdown is filled by JS (nothing hard-coded in the skeleton)")
    for value in ("articles", "comments", "guestbook", "trackbacks"):
        ctx.check(
            f"['{value}'," in script,
            f"the search dropdown offers {value}, matching doSearch in common.js",
        )
