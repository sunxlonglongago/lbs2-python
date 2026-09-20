"""Port of ``class/ubbcode.asp`` (the ``lbsUBB`` class).

The renderer runs on the server exactly like the original: the API returns
ready to display HTML, and the frontend only injects it into the DOM. That
keeps the markup identical to the ASP version.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Iterable, Sequence

import lang
import utils

DEFAULT_FLAGS = "111111"


class _Match:
    __slots__ = ("match",)

    def __init__(self, match):
        self.match = match

    def group(self, index: int) -> str:
        return self.match.group(index) or ""

    @property
    def start(self) -> int:
        return self.match.start()

    @property
    def end(self) -> int:
        return self.match.end()


def _loop_replace(
    pattern: "re.Pattern[str]",
    text: str,
    build: Callable[[re.Match], str],
) -> str:
    """Emulate JScript's ``while ((m = re.exec(str))) { str = str.replace(...) }``."""
    position = 0
    while True:
        match = pattern.search(text, position)
        if match is None:
            return text
        replacement = build(match)
        text = text[: match.start()] + replacement + text[match.end():]
        position = match.start() + len(replacement)


class UBBRenderer:
    """Renderer for UBB tagged content."""

    def __init__(
        self,
        *,
        image_folder: str = "",
        smilies_folder: str = "",
        smilies: Sequence[dict] = (),
    ) -> None:
        self.image_folder = image_folder
        self.smilies_folder = smilies_folder
        self.smilies = list(smilies)

    # -- public entry point -------------------------------------------------

    def to_html(
        self,
        text: Any,
        flags: str = DEFAULT_FLAGS,
        base_url: str = "",
        link_nofollow: bool = False,
        image_folder: "str | None" = None,
        smilies_folder: "str | None" = None,
    ) -> str:
        value = "" if text is None else str(text)
        flags = str(flags or DEFAULT_FLAGS)
        if len(flags) != 6:
            flags = "000000"
        image_folder = self.image_folder if image_folder is None else image_folder
        smilies_folder = self.smilies_folder if smilies_folder is None else smilies_folder

        basic = flags[0]
        auto_url = flags[1]
        image = flags[2]
        media = flags[3]
        smilies = flags[4]
        text_block = flags[5]

        value = re.sub(r"<br />", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"&nbsp;", "$nbsp$", value, flags=re.IGNORECASE)
        value = re.sub(r"\[separator\]", "", value, flags=re.IGNORECASE)

        if text_block == "1":
            value = self.format_quote(value, base_url)
            value = self.format_code(value)

        if auto_url == "1":
            value = self._auto_url(value, base_url, link_nofollow)

        if basic == "1":
            value = self._basic_tags(value, base_url, link_nofollow, image_folder)

        if image == "1":
            value = self._image_tags(value, base_url)
        elif image == "2":
            value = self._image_links(value, base_url, image_folder)

        if media == "1":
            value = self._media_player(value, base_url, image_folder)
        elif media == "2":
            value = self._media_links(value, base_url, image_folder)

        if smilies == "1":
            value = self._apply_smilies(value, base_url, smilies_folder)

        value = value.replace("\n", "<br />")
        value = re.sub(r"\$nbsp\$", "&nbsp;", value)
        return self.dec_ubb(value)

    # -- blocks -------------------------------------------------------------

    def enc_ubb(self, value: str) -> str:
        return value.replace("[", "$[$").replace("]", "$]$")

    def dec_ubb(self, value: str) -> str:
        return value.replace("$[$", "[").replace("$]$", "]")

    def format_quote(self, value: str, base_url: str = "") -> str:
        value = re.sub(r"\[quote\]", "[quote=]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[quote=", "[quote=", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/quote\]", "[/quote]", value, flags=re.IGNORECASE)
        value = re.sub(r"\n*\[quote=", "[quote=", value, flags=re.IGNORECASE)
        value = re.sub(r"\n*\[/quote\]", "[/quote]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[quote=([^]]*)]\n*", r"[quote=\1]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/quote\]\n*", "[/quote]", value, flags=re.IGNORECASE)

        while "[quote=" in value and "[/quote]" in value:
            result = ""
            start = value.find("[quote=") + 7
            end = value.find("]", start)
            author = ""
            if start > 6 and end > 0:
                author = value[start:end]
            start = start + len(author) + 1
            end = value.find("[/quote]", start)
            if end <= start:
                end = start
            if end > start:
                quoted = value[start:end]
                author_text = author.replace('"', "")
                title = lang.text("quote_from") if len(author_text) > 1 else lang.text("quote")
                result = (
                    f'<div class="quote"><div class="quote-title">{title} '
                    f"<u>{author_text}</u></div>"
                    f'<div class="quote-content">{self.to_html(quoted, "102201", base_url)}'
                    "</div></div>"
                )
            start = value.find("[quote=")
            end = value.find("[/quote]", start) + 8
            if end <= start + 7:
                end = start + len(author) + 8
            source = value[start:end]
            if result:
                value = value.replace(source, result)
            else:
                value = value.replace(source, source.replace("[", "&#91;"))
        return re.sub(r"quote\=\]", "quote]", value, flags=re.IGNORECASE)

    def format_code(self, value: str) -> str:
        value = re.sub(r"\[code\]", "[code]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/code\]", "[/code]", value, flags=re.IGNORECASE)
        value = re.sub(r"\n\[code\]", "[code]", value, flags=re.IGNORECASE)
        value = re.sub(r"\n\[/code\]", "[/code]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[code\]\n", "[code]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/code\]\n", "[/code]", value, flags=re.IGNORECASE)

        while "[code]" in value and "[/code]" in value:
            result = ""
            start = value.find("[code]") + 6
            end = value.find("[/code]", start)
            if end <= start:
                end = start
            if end > start:
                body = value[start:end]
                body = re.sub(r"^ +", "&nbsp;", body, flags=re.MULTILINE)
                body = body.replace("://", "&#58;//")
                result = f'<div class="code">{self.enc_ubb(body)}</div>'
            start = value.find("[code]")
            end = value.find("[/code]", start) + 7
            if end <= start + 6:
                end = start + 7
            source = value[start:end]
            if result:
                value = value.replace(source, result)
            else:
                value = value.replace(source, source.replace("[", "&#91;"))
        return value

    def format_list(self, value: str) -> str:
        value = re.sub(r"\[list\]", "[list=]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[list=", "[list=", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/list\]", "[/list]", value, flags=re.IGNORECASE)
        value = re.sub(r"\n*\[list=", "[list=", value, flags=re.IGNORECASE)
        value = re.sub(r"\n*\[/list\]", "[/list]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[list=([^]]*)]\n*", r"[list=\1]", value, flags=re.IGNORECASE)
        value = re.sub(r"\[/list\]\n*", "[/list]", value, flags=re.IGNORECASE)

        while "[list=" in value and "[/list]" in value:
            result = ""
            start = value.find("[list=") + 6
            end = value.find("]", start)
            style = ""
            if start > 6 and end > 0:
                style = value[start:end]
            start = start + len(style) + 1
            end = value.find("[/list]", start)
            if end <= start:
                end = start
            if end > start:
                body = value[start:end]
                style_attr = ""
                if style:
                    cleaned = re.sub(r"[^a-zA-Z\-]", "", style)
                    style_attr = f' style="list-style-type:{cleaned}"'
                body = re.sub(r"^\[\*\](.*)(\n|)", r"<li>\1</li>", body,
                              flags=re.IGNORECASE | re.MULTILINE)
                result = f'<ul class="ubb-list" {style_attr}>{body}</ul>'
            start = value.find("[list=")
            end = value.find("[/list]", start) + 7
            if end <= start + 6:
                end = start + len(style) + 7
            source = value[start:end]
            if result:
                value = value.replace(source, result)
            else:
                value = value.replace(source, source.replace("[", "&#91;"))
        return re.sub(r"list\=\]", "list]", value, flags=re.IGNORECASE)

    # -- tag families -------------------------------------------------------

    def _auto_url(self, value: str, base_url: str, link_nofollow: bool) -> str:
        pattern = re.compile(
            r"([^=\]][\s]*?|^)(http|https|rstp|ftp|mms|ed2k)://(.*?)"
            r"(\>|\<|\&quot\;|\&gt\;|\&lt\;|\)|\(|$| )",
            re.IGNORECASE | re.MULTILINE,
        )
        ref = ' ref="nofollow"' if link_nofollow else ""

        def build(match: re.Match) -> str:
            url = utils.url_encode(
                match.group(2) + "://" + utils.check_url(match.group(3))
            )
            return (
                f'{match.group(1)}<a href="{url}" title="{url}" '
                f'target="_blank"{ref}>{url}</a>{match.group(4)}'
            )

        return _loop_replace(pattern, value, build)

    def _basic_tags(
        self, value: str, base_url: str, link_nofollow: bool, image_folder: str
    ) -> str:
        ref = ' ref="nofollow"' if link_nofollow else ""

        url_named = re.compile(r"\[url=([^<>]*?)\](.*?)\[/url\]", re.IGNORECASE)

        def build_named(match: re.Match) -> str:
            url = utils.check_url(match.group(1))
            if "://" not in url:
                url = base_url + url
            url = utils.url_encode(url)
            return (
                f'<a href="{url}" title="{url}" target="_blank"{ref}>'
                f"{match.group(2)}</a>"
            )

        value = _loop_replace(url_named, value, build_named)

        url_plain = re.compile(r"\[url\]([^<>]*?)\[/url\]", re.IGNORECASE)

        def build_plain(match: re.Match) -> str:
            url = utils.check_url(match.group(1))
            if "://" not in url:
                url = base_url + url
            url = utils.url_encode(url)
            return f'<a href="{url}" title="{url}" target="_blank"{ref}>{url}</a>'

        value = _loop_replace(url_plain, value, build_plain)

        file_tag = re.compile(r"\[file=([^<>]*?)\]([^<>]*?)\[/file\]", re.IGNORECASE)

        def build_file(match: re.Match) -> str:
            url = utils.check_url(match.group(1))
            if "://" not in url:
                url = base_url + url
            url = utils.url_encode(url)
            return (
                f'<a href="{url}" title="{url}" target="_blank">'
                f'<img src="{base_url}{image_folder}/icon_file.gif" border="0" /> '
                f"{match.group(2)}</a>"
            )

        value = _loop_replace(file_tag, value, build_file)

        value = re.sub(r"\[align=(\w{4,6})\]([^\r]*?)\[/align\]", r'<div align="\1">\2</div>',
                       value, flags=re.IGNORECASE)
        value = re.sub(r"\[color=([\w\#]{3,10})\]([^\r]*?)\[/color\]",
                       r'<span style="color:\1">\2</span>', value, flags=re.IGNORECASE)
        value = re.sub(r"\[size=(\d{1,2})\]([^\r]*?)\[/size\]",
                       r'<span style="font-size:\1pt">\2</span>', value,
                       flags=re.IGNORECASE)
        value = re.sub(
            r"\[font=([ \w\u3400-\u4DBF\u4E00-\u9FAF]{2,18})\]([^\r]*?)\[/font\]",
            r'<span style="font-family:\1">\2</span>', value, flags=re.IGNORECASE)
        value = re.sub(r"\[i\]([^\r]*?)\[/i\]", r"<i>\1</i>", value, flags=re.IGNORECASE)
        value = re.sub(r"\[b\]([^\r]*?)\[/b\]", r"<b>\1</b>", value, flags=re.IGNORECASE)
        value = re.sub(r"\[u\]([^\r]*?)\[/u\]", r"<u>\1</u>", value, flags=re.IGNORECASE)
        value = re.sub(r"\[s\]([^\r]*?)\[/s\]", r"<s>\1</s>", value, flags=re.IGNORECASE)
        value = re.sub(r"\[sup\]([^\r]*?)\[/sup\]", r"<sup>\1</sup>", value,
                       flags=re.IGNORECASE)
        value = re.sub(r"\[sub\]([^\r]*?)\[/sub\]", r"<sub>\1</sub>", value,
                       flags=re.IGNORECASE)
        value = re.sub(r"\[hr\]", "<hr>", value, flags=re.IGNORECASE)
        return self.format_list(value)

    def _image_tags(self, value: str, base_url: str) -> str:
        tag = re.compile(r"\[img\]([^<>]*?)\[/img\]", re.IGNORECASE)

        def build(match: re.Match) -> str:
            url = self._image_url(match.group(1), base_url)
            return (
                '<div style="width: 100%;overflow-x : auto;">'
                f'<a href="{url}" target="_blank"><img src="{url}" alt="{url}" /></a>'
                "</div>"
            )

        value = _loop_replace(tag, value, build)

        aligned = re.compile(r"\[img=(left|right|center)\]([^<>]*?)\[/img\]", re.IGNORECASE)

        def build_aligned(match: re.Match) -> str:
            align = match.group(1)
            url = self._image_url(match.group(2), base_url)
            if align == "center":
                return (
                    f'<center><a href="{url}" target="_blank">'
                    f'<img src="{url}" alt="{url}" /></a></center>'
                )
            return (
                f'<a href="{url}" target="_blank"><img src="{url}" alt="{url}" '
                f'style="float: {align};" /></a>'
            )

        value = _loop_replace(aligned, value, build_aligned)

        sized = re.compile(
            r"\[img=(\d*|),(\d*|)(,left|,right|,center|,absmiddle|)\]([^<>]*?)\[/img\]",
            re.IGNORECASE,
        )

        def build_sized(match: re.Match) -> str:
            width = match.group(1)
            height = match.group(2)
            align = match.group(3)[1:]
            url = self._image_url(match.group(4), base_url)
            if align == "center":
                return (
                    f'<center><a href="{url}" target="_blank"><img src="{url}" '
                    f'width="{width}" height="{height}" alt="{url}" /></a></center>'
                )
            return (
                f'<a href="{url}" target="_blank"><img src="{url}" width="{width}" '
                f'height="{height}" style="float: {align};" alt="{url}" /></a>'
            )

        return _loop_replace(sized, value, build_sized)

    def _image_links(self, value: str, base_url: str, image_folder: str) -> str:
        pattern = re.compile(r"\[img([^\]]*)\]([^<>]*?)\[/img\]", re.IGNORECASE)

        def build(match: re.Match) -> str:
            url = self._image_url(match.group(2), base_url)
            return (
                f'<a href="{url}" target="_blank">'
                f'<img src="{image_folder}/icon_image.gif" alt="Image" /> {url}</a>'
            )

        return _loop_replace(pattern, value, build)

    def _media_player(self, value: str, base_url: str, image_folder: str) -> str:
        pattern = re.compile(
            r"\[(swf|wmp|rm|qt)(=\d*?|)(,\d*?|)\]([^<>]*?)\[/(swf|wmp|rm|qt)\]",
            re.IGNORECASE,
        )

        def build(match: re.Match) -> str:
            object_id = "obj" + utils.random_str(4)
            kind = match.group(1)
            width = match.group(2)[1:] or "400"
            height = match.group(3)[1:] or "300"
            url = utils.check_url(match.group(4))
            if "://" not in url:
                url = base_url + url
            url = utils.url_encode(url)
            return (
                f'<div class="ubb-obj-div"><input id="bShow{object_id}" '
                f'type="hidden" value="-1" />'
                f"<a href=\"javascript:ubbShowObj('{kind}','{object_id}','{url}','"
                f"{width}','{height}');\">"
                f'<img src="{base_url}{image_folder}/icon_media.gif" alt="Media" /> '
                f'<b>{lang.text("show_media")}</b></a>'
                f'<div id="{object_id}"><a href="{url}" target="_blank">{url}</a>'
                "</div></div>"
            )

        return _loop_replace(pattern, value, build)

    def _media_links(self, value: str, base_url: str, image_folder: str) -> str:
        pattern = re.compile(
            r"\[(swf|wmp|rm|qt)([^\]]*)\]([^<>]*?)\[/(swf|wmp|rm|qt)\]",
            re.IGNORECASE,
        )

        def build(match: re.Match) -> str:
            url = self._image_url(match.group(3), base_url)
            return (
                f'<a href="{url}" target="_blank">'
                f'<img src="{image_folder}/icon_media.gif" alt="Media" /> {url}</a>'
            )

        return _loop_replace(pattern, value, build)

    def _apply_smilies(self, value: str, base_url: str, smilies_folder: str) -> str:
        for smiley in self.smilies:
            code = smiley.get("code") or ""
            image = smiley.get("image") or ""
            if not code:
                continue
            placeholder = f"_{code[:1]}_{code[1:]}_"
            replacement = (
                f'<img src="{base_url}{smilies_folder}/{image}" border="0" '
                f'alt="{placeholder}" />'
            )
            while code in value:
                value = value.replace(code, replacement, 1)
            while placeholder in value:
                value = value.replace(placeholder, code, 1)
        return value

    def _image_url(self, raw: str, base_url: str) -> str:
        url = utils.check_url(raw)
        if "://" not in url:
            url = base_url + url
        return utils.url_encode(url)


def render(
    text: Any,
    flags: str = DEFAULT_FLAGS,
    *,
    image_folder: str = "",
    smilies_folder: str = "",
    smilies: Sequence[dict] = (),
    base_url: str = "",
    link_nofollow: bool = False,
) -> str:
    """One shot helper mirroring ``ubb.toHTML(...)`` usage in the ASP sources."""
    renderer = UBBRenderer(
        image_folder=image_folder,
        smilies_folder=smilies_folder,
        smilies=smilies,
    )
    return renderer.to_html(text, flags, base_url, link_nofollow)
