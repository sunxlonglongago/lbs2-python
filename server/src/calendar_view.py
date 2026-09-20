"""Sidebar calendar, ported from ``lbsCache.generateCalendar`` (class/cache.asp)."""

from __future__ import annotations

import calendar as _calendar
import datetime as dt
import sqlite3

import db
import lang
import utils


def generate_calendar(
    conn: sqlite3.Connection,
    year: int,
    month: int,
    *,
    today: "dt.date | None" = None,
) -> str:
    """Return the sidebar calendar markup, identical to the ASP output."""
    today = today or dt.date.today()
    current_year, current_month, current_day = today.year, today.month, today.day

    prev_month = 12 if month - 1 == 0 else month - 1
    next_month = 1 if month + 1 == 13 else month + 1
    prev_year = year - 1 if prev_month == 12 else year
    next_year = year + 1 if next_month == 1 else year

    # JScript getDay(): 0 = Sunday.
    start_weekday = (dt.date(year, month, 1).weekday() + 1) % 7

    rows = db.query_all(
        conn,
        "SELECT log_title, log_postTime, log_mode FROM blog_Article "
        "WHERE strftime('%Y', log_postTime) = ? "
        "AND strftime('%m', log_postTime) = ? "
        "ORDER BY log_postTime ASC",
        (f"{year:04d}", f"{month:02d}"),
    )
    events: dict[int, str] = {}
    for row in rows:
        moment = utils.parse_date_time(row["log_postTime"])
        title = row["log_title"] or ""
        if int(row["log_mode"] or 1) > 2:
            title = "*" * len(title)
        else:
            title = utils.html_encode_lite(title)
        events[moment.day] = events.get(moment.day, "") + f"- {title}\n"

    output = '<table cellspacing="1" width="100%" id="calendar">\n'
    output += '<tr><td colspan="7" class="calendar-top">'
    output += f'\t<a href="default.asp?date={year - 1}-{month}">&laquo;</a>\n'
    output += f'\t<a href="default.asp?date={year}-{month}">'
    output += f'<span class="calendar-year">{year}</span></a>\n'
    output += f'\t<a href="default.asp?date={year + 1}-{month}">&raquo;</a>\n'
    output += "\t&nbsp;&nbsp;\n"
    output += f'\t<a href="default.asp?date={prev_year}-{prev_month}">&laquo;</a>\n'
    output += f'\t<a href="default.asp?date={year}-{month}">'
    output += f'<span class="calendar-month">{lang.text(f"month_{month}")}</span></a>\n'
    output += f'\t<a href="default.asp?date={next_year}-{next_month}">&raquo;</a>\n'
    output += "</td></tr>\n"
    output += '<tr class="calendar-weekdays">\n'
    for index in range(7):
        output += (
            f'\t<td class="calendar-weekday-cell">'
            f'{lang.text(f"weekday_abbr_{index}")}</td>\n'
        )
    output += "</tr>\n"

    if start_weekday > 0:
        output += "<tr>\n"
    for _ in range(start_weekday):
        output += '\t<td class="calendar-day-blank"></td>\n'

    days = _calendar.monthrange(year, month)[1]
    for day in range(1, days + 1):
        weekday = (day + start_weekday) % 7
        style_class = "calendar-day"
        if weekday == 0:
            style_class = "calendar-saturday"
        if weekday == 1:
            output += "<tr>\n"
            style_class = "calendar-sunday"
        if year == current_year and month == current_month and day == current_day:
            style_class = "calendar-today"
        output += f'\t<td class="{style_class}">'
        if events.get(day):
            output += (
                f'<a href="default.asp?date={year}-{month}-{day}" class="calendar" '
                f'title="{events[day][:-1]}">{day}</a>'
            )
        else:
            output += str(day)
        output += "</td>\n"
        if weekday == 0:
            output += "</tr>\n"

    suffix_blank = 7 - (start_weekday + days) % 7
    if suffix_blank not in (0, 7):
        for _ in range(suffix_blank):
            output += '\t<td class="calendar-day-blank"></td>\n'
        output += "</tr>\n"
    output += "</table>\n"
    return output
