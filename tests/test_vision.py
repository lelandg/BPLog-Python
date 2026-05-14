import io
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from bplog import vision
from bplog.images import extract_exif_datetime, load_image_bytes


def _png_bytes():
    img = Image.new("RGB", (60, 40), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_load_image_bytes_returns_jpeg():
    data = load_image_bytes(_png_bytes())
    assert data[:3] == b"\xff\xd8\xff"  # JPEG magic


def _jpeg_with_exif(dt_str: str) -> io.BytesIO:
    img = Image.new("RGB", (60, 40), color="white")
    exif = img.getexif()
    exif[36867] = dt_str  # DateTimeOriginal
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    buf.seek(0)
    return buf


def test_extract_exif_datetime_rounds_down():
    dt = extract_exif_datetime(_jpeg_with_exif("2026:05:14 16:00:29"))
    assert dt == datetime(2026, 5, 14, 16, 0)


def test_extract_exif_datetime_rounds_up():
    dt = extract_exif_datetime(_jpeg_with_exif("2026:05:14 16:00:30"))
    assert dt == datetime(2026, 5, 14, 16, 1)


def test_extract_exif_datetime_missing():
    assert extract_exif_datetime(_png_bytes()) is None


def test_parse_response_ok():
    raw = '{"systolic": 120, "diastolic": 80, "pulse": 65, "confidence": 0.92, "notes": ""}'
    d = vision._parse_response(raw)
    assert d.systolic == 120
    assert d.diastolic == 80
    assert d.pulse == 65
    assert d.confidence == pytest.approx(0.92)


def test_parse_response_with_surrounding_text():
    raw = 'Here is the read:\n{"systolic": 130, "diastolic": 85, "pulse": 72, "confidence": 0.5, "notes": "blurry"}\nDone.'
    d = vision._parse_response(raw)
    assert d.systolic == 130
    assert "blurry" in d.notes


def test_parse_response_handles_nulls():
    raw = '{"systolic": null, "diastolic": 80, "pulse": null, "confidence": 0.1, "notes": "occluded"}'
    d = vision._parse_response(raw)
    assert d.systolic is None
    assert d.diastolic == 80
    assert d.pulse is None
    assert "occluded" in d.notes


def test_parse_response_garbage_returns_empty_draft():
    d = vision._parse_response("nope, not json")
    assert d.systolic is None and d.diastolic is None and d.pulse is None
    assert d.notes  # has an explanatory note


def test_claude_backend_calls_api_with_image(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [
        MagicMock(type="text", text='{"systolic": 118, "diastolic": 78, "pulse": 60, "confidence": 0.9, "notes": ""}')
    ]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic", return_value=fake_client):
        backend = vision.ClaudeVisionBackend()
    draft = backend.extract(b"fake-jpeg-bytes")

    assert draft.systolic == 118
    assert draft.diastolic == 78
    assert draft.pulse == 60
    fake_client.messages.create.assert_called_once()
    kwargs = fake_client.messages.create.call_args.kwargs
    assert kwargs["model"] == vision.DEFAULT_MODEL
    blocks = kwargs["messages"][0]["content"]
    assert any(b.get("type") == "image" for b in blocks)
