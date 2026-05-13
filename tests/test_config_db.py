from pathlib import Path

from bplog import config, db


def test_default_paths_uses_documents_bpreadings():
    paths = config.default_paths()
    assert paths.db.name == "bloodpressure.db"
    assert paths.db.parent.name == "BPReadings"
    assert paths.settings.name == "settings.json"
    assert paths.images_dir.name == "images"


def test_ensure_creates_dirs(tmp_path: Path):
    paths = config.Paths(
        db=tmp_path / "bp" / "bloodpressure.db",
        settings=tmp_path / "cfg" / "settings.json",
        images_dir=tmp_path / "bp" / "images",
    )
    paths.ensure()
    assert paths.db.parent.is_dir()
    assert paths.settings.parent.is_dir()
    assert paths.images_dir.is_dir()


def test_initialize_creates_tables(tmp_path: Path):
    db_path = tmp_path / "bp.db"
    db.initialize(db_path)
    with db.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    names = {r["name"] for r in rows}
    assert {"Users", "Readings"} <= names


def test_initialize_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "bp.db"
    db.initialize(db_path)
    db.initialize(db_path)
    with db.connect(db_path) as conn:
        info = conn.execute("PRAGMA table_info(Readings)").fetchall()
    cols = {r["name"] for r in info}
    assert {"Id", "UserId", "Systolic", "Diastolic", "Pulse", "ReadingTime", "Position"} == cols
