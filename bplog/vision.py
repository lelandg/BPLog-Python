"""Vision-backed reading extraction.

Pluggable VisionBackend ABC; default ClaudeVisionBackend uses the
Anthropic SDK with claude-haiku-4-5 for cheap, structured extraction
from a photo of a BP monitor display.
"""
from __future__ import annotations

import base64
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from .models import ReadingDraft

DEFAULT_MODEL = "claude-haiku-4-5"

_PROMPT = """You are reading a photo of a digital blood-pressure monitor.

Return ONLY a JSON object with these keys:
- systolic: integer mmHg (the larger of the top two numbers)
- diastolic: integer mmHg (the smaller of the top two numbers)
- pulse: integer bpm (usually labeled PUL or with a heart icon)
- confidence: float 0.0-1.0 (your overall confidence in the read)
- notes: string (briefly explain any ambiguity, or empty string)

If any value is unreadable, set it to null. Do not include any other text.
"""


class VisionBackend(ABC):
    @abstractmethod
    def extract(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ReadingDraft: ...


class ClaudeVisionBackend(VisionBackend):
    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None, timeout: float = 30.0):
        from anthropic import Anthropic

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it in the environment before starting bplog."
            )
        self.model = model
        self._client = Anthropic(api_key=resolved_key, timeout=timeout)

    def extract(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ReadingDraft:
        b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        message = self._client.messages.create(
            model=self.model,
            max_tokens=400,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }
            ],
        )
        text_parts: list[str] = []
        for block in message.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(getattr(block, "text", ""))
        raw = "".join(text_parts).strip()
        return _parse_response(raw)


def _parse_response(raw: str) -> ReadingDraft:
    """Pull a JSON object out of the response text and map to ReadingDraft."""
    draft = ReadingDraft(raw_response=raw)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        draft.notes.append("Model response did not contain a JSON object.")
        return draft
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        draft.notes.append(f"JSON parse failed: {exc}")
        return draft

    def _int(key: str) -> Optional[int]:
        v = data.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    draft.systolic = _int("systolic")
    draft.diastolic = _int("diastolic")
    draft.pulse = _int("pulse")

    conf = data.get("confidence")
    try:
        draft.confidence = float(conf) if conf is not None else 0.0
    except (TypeError, ValueError):
        draft.confidence = 0.0

    notes = data.get("notes")
    if isinstance(notes, str) and notes.strip():
        draft.notes.append(notes.strip())
    return draft
