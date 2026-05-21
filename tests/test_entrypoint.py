import socket
from pathlib import Path

from bplog import __main__ as entry
from bplog import db
from bplog.app import create_app
from bplog.config import Paths


def test_resolve_bind_falls_back_when_preferred_unreachable():
    # 240.0.0.1 is reserved/unassigned; bind should fail and fall back.
    host = entry._resolve_bind("240.0.0.1")
    assert host == "127.0.0.1"


def test_resolve_bind_returns_preferred_when_ok():
    assert entry._resolve_bind("127.0.0.1") == "127.0.0.1"


def test_pick_port_returns_usable():
    port = entry._pick_port("127.0.0.1")
    assert 1024 < port < 65536
    # Confirm we can immediately bind to it again
    s = socket.socket()
    s.bind(("127.0.0.1", port))
    s.close()


def test_app_serves_via_make_server(tmp_path: Path):
    paths = Paths(
        db=tmp_path / "bp.db",
        settings=tmp_path / "settings.json",
        images_dir=tmp_path / "images",
    )
    paths.ensure()
    db.initialize(paths.db)
    app = create_app(paths=paths)
    with app.test_client() as c:
        assert c.get("/healthz").status_code == 200
        assert c.get("/").status_code == 200
