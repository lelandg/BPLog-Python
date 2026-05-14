from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from ..images import load_image_bytes
from ..vision import ClaudeVisionBackend, VisionBackend

log = logging.getLogger("bplog.vision")

bp = Blueprint("vision", __name__)

_backend: VisionBackend | None = None


def _get_backend() -> VisionBackend:
    """Lazily instantiate the configured backend.

    Cached on the app for the process lifetime so we don't recreate
    the Anthropic client on every request.
    """
    global _backend
    if _backend is not None:
        return _backend
    settings = current_app.config["bplog_settings"]
    _backend = ClaudeVisionBackend(model=settings.vision_model)
    return _backend


@bp.post("/readings/extract")
def extract():
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "missing image"}), 400
    image_bytes = load_image_bytes(file.stream)
    try:
        draft = _get_backend().extract(image_bytes)
    except Exception as exc:  # surface the error in JSON for the JS client
        log.exception("Vision extract failed")
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500
    return jsonify(
        {
            "systolic": draft.systolic,
            "diastolic": draft.diastolic,
            "pulse": draft.pulse,
            "confidence": draft.confidence,
            "notes": draft.notes,
            "raw_response": draft.raw_response,
        }
    )
