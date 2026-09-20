"""Helpers ported from ``class/functions.asp``.

Kept close to the original implementation (including the slightly odd regexes)
because the rendered HTML must stay byte compatible with the ASP version.
"""

from __future__ import annotations

import datetime as dt
import re
import secrets
from typing import Any, Iterable, Sequence

import lang

TAB = "\t"


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------


def html_encode(value: Any) -> str:
    """``func.HTMLEncode``: escape and turn newlines into ``<br />``."""
    if value is None:
        return ""
    text_value = str(value)
    text_value = text_value.replace("&", "&amp;")
    text_value = text_value.replace(">", "&gt;")
    text_value = text_value.replace("<", "&lt;")
    text_value = text_value.replace(TAB, "&nbsp;&nbsp;")
    text_value = text_value.replace('"', "&quot;")
    text_value = text_value.replace("'", "&#39;")
    text_value = text_value.replace("\n", "<br />")
    return text_value


def html_encode_lite(value: Any) -> str:
    """``func.HTMLEncodeLite``: escape only, used inside form fields."""
    if value is None:
        return ""
    text_value = str(value)
    text_value = text_value.replace("&", "&amp;")
    text_value = text_value.replace(">", "&gt;")
    text_value = text_value.replace("<", "&lt;")
    text_value = text_value.replace('"', "&quot;")
    text_value = text_value.replace("'", "&#39;")
    return text_value


def url_encode(value: Any) -> str:
    """``func.URLEncode``: escape a URL for use inside an attribute."""
    if value is None:
        return ""
    text_value = str(value)
    text_value = re.sub(r"&amp;", "&", text_value, flags=re.IGNORECASE)
    text_value = text_value.replace("&", "&amp;")
    text_value = text_value.replace(">", "&gt;")
    text_value = text_value.replace("<", "&lt;")
    text_value = text_value.replace('"', "&quot;")
    text_value = text_value.replace("'", "&#39;")
    text_value = text_value.replace("[", "&#91;")
    text_value = text_value.replace("]", "&#93;")
    return text_value


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------


def length_w(value: Any) -> int:
    """Double byte aware length used by the original for limits."""
    if value is None:
        return 0
    total = 0
    for char in str(value):
        total += 2 if ord(char) > 255 else 1
    return total


def cut_string(value: Any, output_len: int) -> str:
    """``func.cutString``: shorten a string, appending ``...``."""
    if value is None:
        return ""
    text_value = str(value)
    total = 0
    for index, char in enumerate(text_value):
        total += 2 if ord(char) > 255 else 1
        if total >= output_len:
            return text_value[:index] + "..."
    return text_value


def trim_text(value: Any) -> str:
    if value is None:
        return ""
    text_value = re.sub(r"(^\s*|\s*$)", "", str(value))
    text_value = re.sub(r"(\r*\n){3,}", "\n\n", text_value)
    text_value = text_value.replace("\r", "")
    return text_value


def string_to_regexp(value: Any) -> str:
    """Escape a literal string for use inside a regular expression."""
    if value is None:
        return ""
    text_value = str(value)
    for char in "\\^$*+?.|[](){}":
        text_value = text_value.replace(char, "\\" + char)
    return text_value


def highlight(html: str, keywords: Sequence[str]) -> str:
    """``func.highlight``: wrap keywords in ``span.highlight``, tags untouched."""
    if not html or not keywords:
        return html or ""
    usable = [string_to_regexp(word) for word in keywords if length_w(word) >= 3]
    if not usable:
        return html
    keyword_re = re.compile("(" + "|".join(usable) + ")", re.IGNORECASE)
    span = re.compile(r"(>|^)(.*?)(<|$)", re.IGNORECASE | re.MULTILINE)

    last = 0
    while True:
        match = span.search(html, last)
        if not match:
            break
        replacement = (
            match.group(1)
            + keyword_re.sub(r'<span class="highlight">\1</span>', match.group(2))
            + match.group(3)
        )
        html = html[: match.start()] + replacement + html[match.end():]
        last = match.start() + len(replacement)
    return html


def trim_html(value: Any) -> str:
    if value is None:
        return ""
    text_value = re.sub(r"<[^<>]+>", "", str(value))
    return re.sub(r" +", " ", text_value)


def trim_ubb(value: Any) -> str:
    """``func.trimUBB``: strip UBB markup for excerpts."""
    if value is None:
        return ""
    text_value = str(value)
    text_value = re.sub(r"\[quote([^\[\]]+|)\](\n*)(\s*)", '"', text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"(\s*)(\n*)\[/quote\]", '"', text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"\[code\](\n*)(\s*)", '"', text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"(\s*)(\n*)\[/code\]", '"', text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"\[hr\]", "\n------\n", text_value)
    text_value = re.sub(
        r"\[(/|)(b|i|u|s|sup|sub|url[^\]]*|align[^\]]*|size[^\]]*|color[^\]]*"
        r"|font[^\]]*|list[^\]]*|email[^\]]*|img[^\]]*|swf[^\]]*|wmp[^\]]*"
        r"|qt[^\]]*|rm[^\]]*)\]",
        "",
        text_value,
        flags=re.IGNORECASE,
    )
    text_value = text_value.replace("[*]", "*")
    return re.sub(r" +", " ", text_value)


def clean_html(value: Any) -> str:
    """``func.cleanHTML``: neutralise script and iframe tags."""
    if value is None:
        return ""
    text_value = str(value)
    text_value = re.sub(r"<script([^<>]+)>", r"&lt;script\1&gt;", text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"</script>", "&lt;/script&gt;", text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"<iframe(/| /|)>", r"&lt;iframe\1&gt;", text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"</iframe>", "&lt;/iframe&gt;", text_value,
                        flags=re.IGNORECASE)
    return re.sub(r"<br(/| /|)>", "<br/>", text_value, flags=re.IGNORECASE)


CLOSE_HTML_TAGS = ("p", "div", "span", "table", "ul", "font", "b", "u", "i",
                   "h1", "h2", "h3", "h4", "h5", "h6")
CLOSE_UBB_TAGS = ("code", "quote", "list", "color", "align", "font", "size", "b")


def close_html(value: Any) -> str:
    """Append the closing tags the author forgot."""
    text_value = "" if value is None else str(value)
    for tag in CLOSE_HTML_TAGS:
        opened = len(re.findall(rf"<{tag}( [^<>]+|)>", text_value, re.IGNORECASE))
        closed = len(re.findall(rf"</{tag}>", text_value, re.IGNORECASE))
        text_value += f"</{tag}>" * max(opened - closed, 0)
    return text_value


def close_ubb(value: Any) -> str:
    """``func.closeUBB``: close unclosed UBB blocks before rendering."""
    text_value = "" if value is None else str(value)
    for tag in CLOSE_UBB_TAGS:
        opened = len(re.findall(rf"\[{tag}(=[^\[\]]+|)\]", text_value,
                                re.IGNORECASE))
        closed = len(re.findall(rf"\[/{tag}\]", text_value, re.IGNORECASE))
        text_value += f"[/{tag}]" * max(opened - closed, 0)
    return text_value


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def check_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def check_str(value: Any) -> str:
    """Legacy SQL escaping. The port uses bound parameters; kept for parity."""
    if value is None:
        return ""
    text_value = str(value).replace("'", "''").replace("\r", "")
    return re.sub(r"(wh)(ere)", r"$1'+'$2", text_value, flags=re.IGNORECASE)


def check_url(value: Any) -> str:
    if value is None:
        return ""
    text_value = str(value)
    text_value = re.sub(r"document\.cookie", "document cookie", text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"document\.write", "document write", text_value,
                        flags=re.IGNORECASE)
    text_value = re.sub(r"javascript:", "javascript ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"jscript:", "jscript ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"vbscript:", "vbscript ", text_value, flags=re.IGNORECASE)
    return re.sub(r"<|>", " ", text_value, flags=re.IGNORECASE)


def check_username(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if length_w(value) < 3 or len(value) > 24:
        return False
    return re.search(r"[^\w\u3400-\u4DBF\u4E00-\u9FAF]", value, re.UNICODE) is None


def check_password(value: Any) -> bool:
    if value is None:
        return False
    text_value = str(value)
    if not 6 <= len(text_value) <= 16:
        return False
    return re.search(r"[^\x20-\x7e]", text_value) is None


def check_email(value: Any) -> bool:
    if value is None:
        return False
    text_value = str(value)
    if not 6 <= len(text_value) <= 50:
        return False
    match = re.search(r"[\w\[\]@()\.]+\.+[A-Za-z]{2,4}", text_value)
    return bool(match and match.group(0) == text_value)


def word_filter(filters: Iterable[dict], value: Any):
    """``func.wordFilter``: return the filtered text, or ``False`` when blocked."""
    if value is None:
        return False
    text_value = str(value)
    if len(text_value) < 3:
        return text_value
    for item in filters:
        pattern = item["text"] if item.get("regexp") else string_to_regexp(item["text"])
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            continue
        if int(item.get("mode") or 0) == 0:
            text_value = compiled.sub(item.get("replace") or "", text_value)
        elif compiled.search(text_value):
            return False
    return text_value


def random_str(length: int, seed: str = "abcdefghijklmnopqrstuvwxyz1234567890") -> str:
    return "".join(secrets.choice(seed) for _ in range(length))


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def parse_date_time(value: Any) -> "dt.datetime":
    """Parse the ``YYYY-MM-DD HH:MM:SS`` stamps stored in the database."""
    if isinstance(value, dt.datetime):
        return value
    text_value = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text_value, fmt)
        except ValueError:
            continue
    return dt.datetime.now()


def get_date_time_string(
    fmt: "str | None",
    when: Any = None,
    english_names: bool = False,
) -> str:
    """``func.getDateTimeString`` with the same tokens (``YY-MM-DD hh:ii:ss``)."""
    if when is None:
        moment = dt.datetime.now()
    elif isinstance(when, dt.datetime):
        moment = when
    else:
        moment = parse_date_time(when)
    if not fmt:
        fmt = "YY-MM-DD hh:ii:ss"

    # Stored stamps are naive local times, so ask the local timezone for the
    # offset the way JScript's getTimezoneOffset() would report it.
    if moment.tzinfo is None:
        offset = moment.astimezone().utcoffset()
    else:
        offset = moment.utcoffset()
    tz_minutes = 0 if offset is None else int(offset.total_seconds() // 60)
    zone = "Z" if tz_minutes == 0 else (
        ("+" if tz_minutes > 0 else "-") + f"{abs(tz_minutes) // 60:02d}"
    )

    hour12 = moment.hour - 12 if moment.hour > 12 else moment.hour
    ampm = "PM" if moment.hour > 12 else "AM"
    values = {
        "YY": str(moment.year),
        "yy": str(moment.year)[:2],
        "MM": f"{moment.month:02d}",
        "mm": str(moment.month),
        "DD": f"{moment.day:02d}",
        "dd": str(moment.day),
        "hh": f"{moment.hour:02d}",
        "HH": str(moment.hour),
        "H": str(hour12),
        "h": f"{hour12:02d}",
        "ii": f"{moment.minute:02d}",
        "II": str(moment.minute),
        "ss": f"{moment.second:02d}",
        "SS": str(moment.second),
        "A": ampm,
        "a": ampm.lower(),
        "Z": zone + "00",
        "z": zone,
    }
    for token in ("YY", "yy", "MM", "mm", "DD", "dd", "hh", "HH", "H", "h",
                  "ii", "II", "ss", "SS", "A", "a", "Z", "z"):
        fmt = re.sub(
            r"([^\\]|^)" + token,
            lambda match, v=values[token]: match.group(1) + v,
            fmt,
        )

    weekday = int(moment.weekday() + 1) % 7  # Access/JScript weeks start Sunday
    month_name = lang.text(f"month_{moment.month}")
    month_abbr = lang.text(f"month_abbr_{moment.month}")
    weekday_name = lang.text(f"weekday_{weekday}")
    weekday_abbr = lang.text(f"weekday_abbr_{weekday}")
    if english_names:
        month_name = dt.date(2000, moment.month, 1).strftime("%B")
        month_abbr = dt.date(2000, moment.month, 1).strftime("%b")
        weekday_name = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday")[weekday]
        weekday_abbr = weekday_name[:3]

    fmt = re.sub(r"([^\w]|^)M([^\w]|$)", lambda m: f"{m.group(1)}{month_name}{m.group(2)}", fmt)
    fmt = re.sub(r"([^\w]|^)m([^\w]|$)", lambda m: f"{m.group(1)}{month_abbr}{m.group(2)}", fmt)
    fmt = re.sub(r"([^\w]|^)W([^\w]|$)", lambda m: f"{m.group(1)}{weekday_name}{m.group(2)}", fmt)
    fmt = re.sub(r"([^\w]|^)w([^\w]|$)", lambda m: f"{m.group(1)}{weekday_abbr}{m.group(2)}", fmt)
    return fmt


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def generate_page_links(
    entry_count: int,
    page_size: int,
    current_page: int,
    show_pages: int,
    url_prefix: str,
    url_suffix: str = "",
) -> str:
    """``func.generatePageLinks``: identical markup, ``&amp;`` escaped URLs."""
    page_size = max(int(page_size or 1), 1)
    max_page = (int(entry_count) - 1) // page_size + 1
    output = ""
    url_prefix += "" if url_prefix == "?" else "&amp;"
    if url_suffix is None:
        url_suffix = ""

    prev_bound = current_page - show_pages // 2
    next_bound = current_page + show_pages // 2
    if prev_bound <= 0:
        prev_bound = 1
        next_bound = show_pages
    if next_bound > max_page:
        next_bound = max_page
        prev_bound = max_page - show_pages
    if prev_bound <= 0:
        prev_bound = 1

    if max_page == 1:
        return '<span class="pagelink-current"> 1 </span>'

    if prev_bound > 1:
        output += f'<a href="{url_prefix}page=1{url_suffix}"> &lt;&lt; </a> | \n'
    if current_page > 1:
        output += (
            f'<a href="{url_prefix}page={current_page - 1}{url_suffix}"> &lt; </a> | \n'
        )
    for index in range(prev_bound, next_bound + 1):
        if current_page == index:
            output += f'<span class="pagelink-current">{index}</span> | \n'
        elif index <= max_page:
            output += f'<a href="{url_prefix}page={index}{url_suffix}"> {index} </a> | \n'
    if current_page < max_page:
        output += (
            f'<a href="{url_prefix}page={current_page + 1}{url_suffix}"> &gt; </a>\n'
        )
    if next_bound < max_page:
        output += f' | <a href="{url_prefix}page={max_page}{url_suffix}"> &gt;&gt; </a>\n'
    return output
