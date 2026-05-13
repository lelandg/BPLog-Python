"""Capture-image file storage keyed by reading Id.

Images live alongside the SQLite DB (e.g. ~/Documents/BPReadings/images/<id>.jpg).
We keep them out of the database so the .NET app's schema is untouched.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps

MAX_LONG_EDGE = 1568  # Claude's recommended cap; smaller than this is fine.


def _path_for(images_dir: Path, reading_id: int) -> Path:
    return images_dir / f"{reading_id}.jpg"


def _prep_image(stream: BinaryIO) -> Image.Image:
    raw = Image.open(stream)
    img = ImageOps.exif_transpose(raw) or raw
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_LONG_EDGE, MAX_LONG_EDGE))
    return img


def save_image_for_reading(
    images_dir: Path, reading_id: int, stream: BinaryIO, original_filename: str = ""
) -> Path:
    """Read, downsize, JPEG-encode, write atomically. Returns final path.

    `original_filename` is currently unused — kept in the signature so callers
    can pass it through for future format-preservation logic.
    """
    del original_filename
    images_dir.mkdir(parents=True, exist_ok=True)
    img = _prep_image(stream)
    final = _path_for(images_dir, reading_id)
    tmp = final.with_suffix(".jpg.tmp")
    img.save(tmp, format="JPEG", quality=85, optimize=True)
    tmp.replace(final)
    return final


def delete_image_for_reading(images_dir: Path, reading_id: int) -> bool:
    p = _path_for(images_dir, reading_id)
    if p.exists():
        p.unlink()
        return True
    return False


def load_image_bytes(stream: BinaryIO) -> bytes:
    """Read an uploaded stream, downsize, return JPEG bytes (for vision upload)."""
    img = _prep_image(stream)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()
