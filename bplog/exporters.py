"""Text and HTML exporters.

Output formats mirror the .NET WPF app's exports (MainWindow.xaml.cs)
so existing consumers of the exported files see no change.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Iterable, Optional

from .models import HealthRecord


def _format_row_text(r: HealthRecord) -> str:
    standing = "Standing" if r.standing else ""
    return (
        f"{r.reading_time:%m-%d-%Y} "
        f"{r.reading_time:%H:%M} "
        f"{r.systolic}/{r.diastolic} "
        f"Pulse: {r.pulse} "
        f"{standing}"
    ).rstrip()


def to_text(
    records: Iterable[HealthRecord],
    user_name: str,
    birthdate: Optional[datetime],
    now: Optional[datetime] = None,
) -> str:
    records = list(records)
    now = now or datetime.now()
    lines: list[str] = []
    if records:
        first = records[0]
        bd = birthdate or first.birthdate
        lines.append(f"Name: {first.name}  Birth Date: {bd:%Y-%m-%d}")
    else:
        lines.append(f"Name: {user_name}  Birth Date: {birthdate:%Y-%m-%d}" if birthdate else f"Name: {user_name}")
    lines.append(f"Exported on {now:%Y-%m-%d %H:%M:%S}")
    lines.append("-" * 50)
    for r in sorted(records, key=lambda x: x.reading_time):
        lines.append(_format_row_text(r))
    return "\n".join(lines) + "\n"


def to_html(
    records: Iterable[HealthRecord],
    user_name: str,
    birthdate: Optional[datetime],
    now: Optional[datetime] = None,
) -> str:
    records = list(records)
    now = now or datetime.now()
    sorted_records = sorted(records, key=lambda x: x.reading_time)

    if records:
        header_name = escape(records[0].name)
        header_bd = (birthdate or records[0].birthdate).strftime("%m-%d-%Y")
    else:
        header_name = escape(user_name)
        header_bd = birthdate.strftime("%m-%d-%Y") if birthdate else ""

    rows: list[str] = []
    for r in sorted_records:
        rows.append(
            "<tr>"
            f"<td>{r.reading_time:%m-%d-%Y}</td>"
            f"<td>{r.reading_time:%H:%M}</td>"
            f"<td>{r.systolic} / {r.diastolic}</td>"
            f"<td>{r.pulse}</td>"
            f"<td>{'X' if r.standing else ''}</td>"
            "</tr>"
        )

    return (
        "<html><body>"
        "<table border='2px' style='border-collapse:collapse; padding:5px;'>"
        "<style>th, td { padding: 5px; text-align: center}</style>"
        f"<h1>{header_name} {header_bd}</h1>"
        "<tr><th>Date</th><th>Time</th><th>Sys/Dia</th><th>Pulse</th><th>Standing</th></tr>"
        + "".join(rows)
        + "</table></body></html>"
    )


def filter_after(
    records: Iterable[HealthRecord], threshold: Optional[datetime]
) -> list[HealthRecord]:
    """Return only records strictly after `threshold` (or all records if None)."""
    if threshold is None:
        return list(records)
    return [r for r in records if r.reading_time > threshold]
