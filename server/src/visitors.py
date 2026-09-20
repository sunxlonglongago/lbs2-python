"""Visitor records and the online counter.

Ported from ``lbsUser.recordVisitor`` / ``getBrowserCap`` (class/user.asp) and
the ``Application`` counters in ``_common.asp``.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any

import db
import utils

ONLINE_WINDOW = 60.0

_lock = threading.Lock()
_state: dict[str, Any] = {
    "online": 1,
    "counter": 1,
    "key": "",
    "updated": 0.0,
    "started": False,
}

# Ordered exactly like the ASP if-chain: later matches overwrite earlier ones.
BROWSER_MATCHES = (
    ("mozilla", "Mozilla"),
    ("icab", "iCab"),
    ("lynx", "Lynx"),
    ("links", "Links"),
    ("elinks", "ELinks"),
    ("jbrowser", "JBrowser"),
    ("konqueror", "Konqueror"),
    ("wget", "Wget"),
)

GECKO_MATCHES = (
    ("aol", "AOL"),
    ("netscape", "Netscape"),
    ("firefox", "FireFox"),
    ("chimera", "Chimera"),
    ("camino", "Camino"),
    ("galeon", "Galeon"),
    ("k-meleon", "K-Meleon"),
)

BOT_MATCHES = (
    ("grub", "Grub"),
    ("googlebot", "GoogleBot"),
    ("msnbot", "MSN Bot"),
    ("slurp", "Yahoo! Slurp"),
)

IE_MATCHES = (
    ("msn", "MSN"),
    ("aol", "AOL"),
    ("webtv", "WebTV"),
    ("myie2", "MyIE2"),
    ("maxthon", "Maxthon"),
    ("gosurf", "GoSurf"),
    ("netcaptor", "NetCaptor"),
    ("sleipnir", "Sleipnir"),
    ("avant browser", "AvantBrowser"),
    ("greenbrowser", "GreenBrowser"),
    ("slimbrowser", "SlimBrowser"),
)

APPLE_MATCHES = (
    ("omniweb", "OmniWeb"),
    ("safari", "Safari"),
)

OS_MATCHES = (
    ("windows ce", "Windows CE"),
    ("windows 95", "Windows 95"),
    ("win98", "Windows 98"),
    ("windows 98", "Windows 98"),
    ("windows 2000", "Windows 2000"),
    ("windows xp", "Windows XP"),
    ("windows nt 5.0", "Windows 2000"),
    ("windows nt 5.1", "Windows XP"),
    ("windows nt 5.2", "Windows 2003"),
    ("windows nt", "Windows NT"),
    ("windows", "Windows"),
    ("x11", "Unix"),
    ("unix", "Unix"),
    ("sunos", "SUN OS"),
    ("sun os", "SUN OS"),
    ("powerpc", "PowerPC"),
    ("ppc", "PowerPC"),
    ("macintosh", "Mac"),
    ("mac osx", "MacOSX"),
    ("freebsd", "FreeBSD"),
    ("linux", "Linux"),
    ("palmsource", "PalmOS"),
    ("palmos", "PalmOS"),
    ("wap ", "WAP"),
)


def browser_cap(user_agent: str) -> dict[str, str]:
    """Port of ``getBrowserCap``; unknown agents report ``Unkown``."""
    info = {"name": "Unkown", "os": "Unkown"}
    value = (user_agent or "").lower().strip().replace("\n", "")
    if len(value) < 10:
        return info

    for needle, name in BROWSER_MATCHES:
        if needle in value:
            info["name"] = name

    if "gecko" in value:
        info["name"] = "Mozilla"
        for needle, name in GECKO_MATCHES:
            if needle in value:
                info["name"] = name
        info["name"] += "[Gecko]"

    if "bot" in value or "crawl" in value:
        info["name"] = ""
        for needle, name in BOT_MATCHES:
            if needle in value:
                info["name"] = name
        info["name"] += "[Bot/Crawler]"

    if "ask jeeves" in value or "teoma" in value:
        info["name"] = "Ask Jeeves/Teoma"

    if "msie" in value:
        index = value.find("msie")
        stop = value.find(";", index)
        version = value[index + 5: stop if stop > -1 else index + 9].strip()
        info["name"] = "IE"
        for needle, name in IE_MATCHES:
            if needle in value:
                info["name"] = name
        info["name"] += f"[IE {version}]"

    if "opera" in value:
        index = value.find("opera")
        info["name"] = "Opera " + value[index + 6: index + 9]

    if "applewebkit" in value:
        info["name"] = ""
        for needle, name in APPLE_MATCHES:
            if needle in value:
                info["name"] = name
        info["name"] += "[AppleWebKit]"

    for needle, name in OS_MATCHES:
        if needle in value:
            info["os"] = name
    return info


def record_visit(
    conn: sqlite3.Connection,
    *,
    ip: str,
    user_agent: str,
    referer: str,
    target: str,
    max_records: int,
) -> None:
    """Store a visitor row, reusing the oldest slot once the ring is full."""
    cap = browser_cap(user_agent)
    values = {
        "vr_ip": (ip or "")[:15],
        "vr_os": (cap["os"] or "")[:20],
        "vr_browser": (cap["name"] or "")[:30],
        "vr_referer": (referer or "")[:250],
        "vr_target": (target or "")[:50],
        "vr_time": utils.get_date_time_string(None, None),
    }
    count = int(db.scalar(conn, "SELECT COUNT(vr_id) FROM blog_VisitorRecord") or 0)
    if max_records and count >= max_records:
        oldest = db.query_one(
            conn, "SELECT vr_id FROM blog_VisitorRecord ORDER BY vr_time ASC LIMIT 1"
        )
        if oldest is not None:
            db.update(conn, "blog_VisitorRecord", values, "vr_id = ?", (oldest["vr_id"],))
    else:
        db.insert(conn, "blog_VisitorRecord", values)
    conn.execute(
        "UPDATE blog_Settings SET set_value0 = set_value0 + 1 "
        "WHERE set_name = 'counterVisitor'"
    )
    conn.commit()


def touch_online(session) -> int:
    """Port of the online user counter kept in ASP ``Application`` scope."""
    now = time.time()
    with _lock:
        if not _state["started"]:
            _state.update(online=1, counter=1, key=utils.random_str(2),
                          updated=now, started=True)
        elif now - _state["updated"] > ONLINE_WINDOW:
            _state["online"] = _state["counter"]
            _state["counter"] = 1
            _state["key"] = utils.random_str(2)
            _state["updated"] = now
        elif session.get("online_key") != _state["key"]:
            _state["counter"] += 1
            session["online_key"] = _state["key"]
        return int(_state["online"])


def online_count() -> int:
    with _lock:
        return int(_state["online"])
