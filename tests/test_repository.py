from datetime import datetime
from pathlib import Path

import pytest

from bplog import db, repository


@pytest.fixture
def fresh_db(tmp_path: Path) -> Path:
    p = tmp_path / "bp.db"
    db.initialize(p)
    return p


def test_upsert_user_inserts_then_returns_same_id(fresh_db: Path):
    bd = datetime(1970, 1, 1)
    uid1 = repository.upsert_user(fresh_db, "Alice", bd)
    uid2 = repository.upsert_user(fresh_db, "Alice", bd)
    assert uid1 == uid2


def test_add_and_list_readings_round_trip(fresh_db: Path):
    uid = repository.upsert_user(fresh_db, "Alice", datetime(1970, 1, 1))
    t = datetime(2026, 5, 13, 9, 30, 0)
    rid = repository.add_reading(fresh_db, uid, 120, 80, 65, t, standing=True)
    assert rid > 0

    rows = repository.list_readings(fresh_db)
    assert len(rows) == 1
    r = rows[0]
    assert r.systolic == 120
    assert r.diastolic == 80
    assert r.pulse == 65
    assert r.standing is True
    assert r.reading_time == t


def test_update_reading(fresh_db: Path):
    uid = repository.upsert_user(fresh_db, "Alice", datetime(1970, 1, 1))
    rid = repository.add_reading(fresh_db, uid, 120, 80, 65, datetime(2026, 5, 13, 9, 0), False)
    repository.update_reading(
        fresh_db, rid, 125, 82, 70, datetime(2026, 5, 13, 10, 0), True
    )
    r = repository.get_reading(fresh_db, rid)
    assert r is not None
    assert (r.systolic, r.diastolic, r.pulse, r.standing) == (125, 82, 70, True)


def test_delete_reading(fresh_db: Path):
    uid = repository.upsert_user(fresh_db, "Alice", datetime(1970, 1, 1))
    rid = repository.add_reading(fresh_db, uid, 120, 80, 65, datetime(2026, 5, 13, 9, 0), False)
    assert repository.delete_reading(fresh_db, rid) == 1
    assert repository.list_readings(fresh_db) == []


def test_list_sorted_desc(fresh_db: Path):
    uid = repository.upsert_user(fresh_db, "Alice", datetime(1970, 1, 1))
    repository.add_reading(fresh_db, uid, 110, 70, 60, datetime(2026, 5, 13, 8, 0), False)
    repository.add_reading(fresh_db, uid, 120, 80, 65, datetime(2026, 5, 13, 9, 0), False)
    rows = repository.list_readings(fresh_db)
    assert rows[0].reading_time > rows[1].reading_time


def test_get_primary_user_when_empty(fresh_db: Path):
    assert repository.get_primary_user(fresh_db) is None
