"""Visitor list for the statistics page (source/src_stats.asp)."""

from __future__ import annotations

import sqlite3
from typing import Any

import db
import utils


def visitor_list(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = db.query_all(
        conn, "SELECT * FROM blog_VisitorRecord ORDER BY vr_time DESC"
    )
    items = []
    for row in rows:
        data = dict(row)
        items.append(
            {
                "id": int(data["vr_id"]),
                "ip": data["vr_ip"] or "",
                "browser": data["vr_browser"] or "",
                "os": data["vr_os"] or "",
                "time": data["vr_time"] or "",
                "referer": data["vr_referer"] or "",
                "referer_short": utils.cut_string(data["vr_referer"] or "", 50),
                "target": data["vr_target"] or "",
            }
        )
    return items
