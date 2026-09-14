"""Repository paths and bounded input limits."""

from __future__ import annotations

from pathlib import Path


IMPLEMENTATION_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = IMPLEMENTATION_DIR.parents[1]
REPOSITORY_DIR = PROJECT_DIR.parents[1]
SHARED_DIR = PROJECT_DIR / "shared"
FIXTURES_DIR = SHARED_DIR / "fixtures"
LABELS_DIR = SHARED_DIR / "labels"
CONTEXT_DIR = SHARED_DIR / "context"
TASKS_PATH = SHARED_DIR / "evals" / "tasks.jsonl"

STANDARD_SIZE = (1280, 720)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_REQUEST_BYTES = 8 * 1024 * 1024
