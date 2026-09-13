"""Load versioned Markdown documents into traceable chunks."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .types import Chunk


def _front_matter(lines: list[str], path: Path) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"front matter가 없습니다: {path}")
    metadata: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            required = {"document_id", "title", "version"}
            missing = required - metadata.keys()
            if missing:
                raise ValueError(f"필수 metadata가 없습니다: {path} ({', '.join(sorted(missing))})")
            return metadata, index + 1
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    raise ValueError(f"front matter가 닫히지 않았습니다: {path}")


def load_document(path: Path) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata, body_start = _front_matter(lines, path)
    headings: list[str] = []
    chunks: list[Chunk] = []
    paragraph: list[str] = []
    paragraph_start = body_start + 1

    def flush(end_line: int) -> None:
        nonlocal paragraph
        text = " ".join(line.strip() for line in paragraph if line.strip())
        if not text:
            paragraph = []
            return
        heading_path = " > ".join(headings)
        full_text = f"{heading_path}\n{text}" if heading_path else text
        location = f"L{paragraph_start}-L{end_line}"
        chunks.append(
            Chunk(
                chunk_id=f"{metadata['document_id']}::{location}",
                document_id=metadata["document_id"],
                title=metadata["title"],
                location=location,
                text=full_text,
                version=metadata["version"],
            )
        )
        paragraph = []

    for zero_index, line in enumerate(lines[body_start:], start=body_start):
        line_number = zero_index + 1
        stripped = line.strip()
        if stripped.startswith("#"):
            flush(line_number - 1)
            level = len(stripped) - len(stripped.lstrip("#"))
            heading = stripped[level:].strip()
            headings[:] = headings[: max(0, level - 1)]
            headings.append(heading)
            paragraph_start = line_number + 1
        elif not stripped:
            flush(line_number - 1)
            paragraph_start = line_number + 1
        else:
            if not paragraph:
                paragraph_start = line_number
            paragraph.append(line)
    flush(len(lines))
    return chunks


def load_corpus(directory: Path) -> list[Chunk]:
    paths = sorted(directory.glob("*.md"))
    if len(paths) < 3:
        raise ValueError("공통 Markdown 문서가 3개 이상 필요합니다.")
    chunks = [chunk for path in paths for chunk in load_document(path)]
    ids = [chunk.chunk_id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("중복 chunk ID가 있습니다.")
    return chunks


def corpus_fingerprint(chunks: list[Chunk]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.chunk_id.encode())
        digest.update(chunk.version.encode())
        digest.update(chunk.text.encode())
    return digest.hexdigest()
