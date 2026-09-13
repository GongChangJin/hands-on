"""Bounded image validation, integrity checks, and metadata-free normalization."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .paths import FIXTURES_DIR, LABELS_DIR, MAX_IMAGE_BYTES, MAX_PIXELS, STANDARD_SIZE
from .types import PreparedImage


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURES = (b"\xff\xd8\xff",)


class ImageSafetyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _allowed_path(path: Path) -> Path:
    if path.is_symlink():
        raise ImageSafetyError("symlink_rejected", "symlink 이미지는 허용하지 않습니다.")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ImageSafetyError("file_not_found", f"이미지를 찾을 수 없습니다: {path}") from exc
    try:
        resolved.relative_to(FIXTURES_DIR.resolve(strict=True))
    except ValueError as exc:
        raise ImageSafetyError(
            "outside_fixture_directory",
            f"허용된 fixture 디렉터리 밖의 이미지는 거부합니다: {path}",
        ) from exc
    return resolved


def _signature_mime(raw: bytes) -> str:
    if raw.startswith(PNG_SIGNATURE):
        return "image/png"
    if any(raw.startswith(signature) for signature in JPEG_SIGNATURES):
        return "image/jpeg"
    raise ImageSafetyError("invalid_signature", "지원되는 PNG/JPEG file signature가 아닙니다.")


def load_label(fixture_id: str) -> dict[str, Any]:
    path = LABELS_DIR / f"{fixture_id}.json"
    if not path.is_file():
        raise ImageSafetyError("missing_label", f"고정 라벨이 없습니다: {fixture_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def preprocess_image(path: Path) -> PreparedImage:
    resolved = _allowed_path(path)
    source_size = resolved.stat().st_size
    if source_size <= 0 or source_size > MAX_IMAGE_BYTES:
        raise ImageSafetyError(
            "image_size_limit",
            f"이미지 크기는 1~{MAX_IMAGE_BYTES} bytes 범위여야 합니다.",
        )
    raw = resolved.read_bytes()
    signature_mime = _signature_mime(raw)
    digest = sha256_bytes(raw)
    label = load_label(resolved.stem)
    if digest != label.get("sha256"):
        raise ImageSafetyError("integrity_mismatch", "이미지 SHA-256이 고정 라벨과 다릅니다.")
    if signature_mime != label.get("mime_type"):
        raise ImageSafetyError("mime_mismatch", "file signature MIME과 라벨 MIME이 다릅니다.")

    try:
        with Image.open(io.BytesIO(raw)) as source:
            source.verify()
        with Image.open(io.BytesIO(raw)) as source:
            detected_format = source.format
            width, height = source.size
            metadata_keys = tuple(sorted(str(key) for key in source.info))
            if source.getexif():
                metadata_keys = tuple(sorted(set(metadata_keys) | {"exif"}))
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageSafetyError("decode_failed", "이미지를 안전하게 해석할 수 없습니다.") from exc

    if detected_format != label.get("format"):
        raise ImageSafetyError("format_mismatch", "실제 이미지 format과 라벨 format이 다릅니다.")
    if width * height > MAX_PIXELS:
        raise ImageSafetyError("pixel_limit", f"이미지는 {MAX_PIXELS} pixels를 넘을 수 없습니다.")
    if (width, height) != (label.get("width"), label.get("height")):
        raise ImageSafetyError("dimension_mismatch", "이미지 크기가 고정 라벨과 다릅니다.")

    if image.size != STANDARD_SIZE:
        image.thumbnail(STANDARD_SIZE, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", STANDARD_SIZE, "#FFFFFF")
        offset = ((STANDARD_SIZE[0] - image.width) // 2, (STANDARD_SIZE[1] - image.height) // 2)
        canvas.paste(image, offset)
        image = canvas

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False)
    normalized = output.getvalue()
    if not normalized.startswith(PNG_SIGNATURE):
        raise ImageSafetyError("normalization_failed", "정규화된 PNG signature가 잘못되었습니다.")
    relative = resolved.relative_to(FIXTURES_DIR.parent).as_posix()
    return PreparedImage(
        source_path=resolved,
        relative_path=f"shared/{relative}",
        png_bytes=normalized,
        sha256=digest,
        width=STANDARD_SIZE[0],
        height=STANDARD_SIZE[1],
        source_bytes=source_size,
        metadata_removed=metadata_keys,
        label=label,
    )
