"""Attachment upload rules."""

NAME = "upload"
DOC = "attachments: type, size and directory rules"

CASES = [
    ("upload.limits", "the upload limits are readable"),
    ("upload.reject_type", "a non-whitelisted extension is refused"),
    ("upload.accept", "a whitelisted image uploads and yields a UBB tag"),
    ("upload.guest", "anonymous uploads are refused"),
]

GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    b"\x02\x02D\x01\x00;"
)


def run(ctx):
    ctx.case("upload.guest")
    response, _ = ctx.post(
        "anonymous",
        "/api/upload",
        data={"File": (__import__("io").BytesIO(GIF), "tiny.gif")},
        content_type="multipart/form-data",
    )
    ctx.check_status(response, 401, "anonymous uploads are refused")

    ctx.login("admin", "Admin", "comeon")

    ctx.case("upload.limits")
    response, payload = ctx.get("admin", "/api/upload/limits")
    ctx.check_status(response, 200, "the upload limits are readable")
    ctx.check(payload["size"] > 0, "the size limit is returned")
    ctx.check("gif" in payload["types"], "gif is whitelisted")

    ctx.case("upload.reject_type")
    response, payload = ctx.post(
        "admin",
        "/api/upload",
        data={"File": (__import__("io").BytesIO(b"MZ"), "evil.exe")},
        content_type="multipart/form-data",
    )
    ctx.check_status(response, 400, "a non-whitelisted type is refused")
    ctx.check_equal((payload or {}).get("error"), "type", "error code is type")

    ctx.case("upload.accept")
    response, payload = ctx.post(
        "admin",
        "/api/upload",
        data={"File": (__import__("io").BytesIO(GIF), "tiny.gif")},
        content_type="multipart/form-data",
    )
    ctx.check_status(response, 200, "the image uploads")
    ctx.check((payload or {}).get("path", "").startswith("uploads/"), "the stored path starts with uploads/")
    ctx.check_equal((payload or {}).get("extension"), "gif", "the extension is detected")
    ctx.check("[img]" in (payload or {}).get("ubb", ""), "a UBB image tag is produced")
