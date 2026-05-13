from datetime import datetime

from bplog import exporters
from bplog.models import HealthRecord


def _record(t: datetime, sys: int = 120, dia: int = 80, pulse: int = 65, standing: bool = False) -> HealthRecord:
    return HealthRecord(
        id=1,
        user_id=1,
        name="Alice",
        birthdate=datetime(1970, 1, 1),
        systolic=sys,
        diastolic=dia,
        pulse=pulse,
        reading_time=t,
        standing=standing,
    )


def test_text_header_and_rows():
    r1 = _record(datetime(2026, 5, 13, 9, 30), standing=True)
    r2 = _record(datetime(2026, 5, 13, 14, 0))
    out = exporters.to_text([r1, r2], "Alice", datetime(1970, 1, 1), now=datetime(2026, 5, 13, 20, 0, 0))
    assert "Name: Alice  Birth Date: 1970-01-01" in out
    assert "Exported on 2026-05-13 20:00:00" in out
    assert "05-13-2026 09:30 120/80 Pulse: 65 Standing" in out
    assert "05-13-2026 14:00 120/80 Pulse: 65" in out


def test_text_rows_sorted_ascending():
    early = _record(datetime(2026, 5, 13, 8, 0))
    late = _record(datetime(2026, 5, 13, 18, 0))
    out = exporters.to_text([late, early], "Alice", datetime(1970, 1, 1), now=datetime(2026, 5, 13, 20, 0))
    early_idx = out.index("08:00")
    late_idx = out.index("18:00")
    assert early_idx < late_idx


def test_html_contains_expected_structure():
    r = _record(datetime(2026, 5, 13, 9, 30), standing=True)
    out = exporters.to_html([r], "Alice", datetime(1970, 1, 1))
    assert "<h1>Alice 01-01-1970</h1>" in out
    assert "<th>Sys/Dia</th>" in out
    assert "<td>120 / 80</td>" in out
    assert "<td>X</td>" in out
    assert "<td>05-13-2026</td>" in out


def test_html_escapes_name():
    r = _record(datetime(2026, 5, 13, 9, 30))
    r.name = "<script>alert(1)</script>"
    out = exporters.to_html([r], r.name, datetime(1970, 1, 1))
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_filter_after_strict():
    r1 = _record(datetime(2026, 5, 13, 8, 0))
    r2 = _record(datetime(2026, 5, 13, 9, 0))
    r3 = _record(datetime(2026, 5, 13, 10, 0))
    threshold = datetime(2026, 5, 13, 9, 0)
    kept = exporters.filter_after([r1, r2, r3], threshold)
    assert kept == [r3]


def test_filter_after_none_returns_all():
    r1 = _record(datetime(2026, 5, 13, 8, 0))
    assert exporters.filter_after([r1], None) == [r1]
