"""Repository paths and fixed experiment limits."""

from __future__ import annotations

from pathlib import Path


IMPLEMENTATION_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = IMPLEMENTATION_DIR.parents[1]
SHARED_DIR = PROJECT_DIR / "shared"
REPOSITORY_DIR = PROJECT_DIR.parents[1]
CONTRACTS_DIR = REPOSITORY_DIR / "common" / "contracts"

QUESTION_PATH = SHARED_DIR / "research-question.json"
STRATEGIES_PATH = SHARED_DIR / "search-strategies.json"
FILTERS_PATH = SHARED_DIR / "filters.json"
TASKS_PATH = SHARED_DIR / "evals" / "tasks.jsonl"
SCHEMAS_DIR = SHARED_DIR / "schemas"

MINIMUM_VERIFIED_PAPERS = 10
MAXIMUM_ANALYZED_PAPERS = 18
MAX_EVIDENCE_QUOTE_CHARS = 500
MAX_ABSTRACT_CACHE_CHARS = 600
PHOENIX_PROJECT_NAME = "05-research-agent"
