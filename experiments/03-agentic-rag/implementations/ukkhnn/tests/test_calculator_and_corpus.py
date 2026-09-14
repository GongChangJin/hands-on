from __future__ import annotations

from pathlib import Path

import pytest

from agentic_rag.calculator import evaluate_arithmetic, format_number
from agentic_rag.corpus import corpus_fingerprint, load_corpus


PROJECT_DIR = Path(__file__).resolve().parents[3]


def test_calculator_is_deterministic_and_narrow() -> None:
    assert format_number(evaluate_arithmetic("49000 + (5 - 3) * 12000")) == "73000"
    assert evaluate_arithmetic("2 ^ 10 + 24") == 1048
    with pytest.raises(ValueError):
        evaluate_arithmetic("__import__('os').environ")
    with pytest.raises(ValueError):
        evaluate_arithmetic("2 ** 100")


def test_common_corpus_has_traceable_chunks_and_safety_fixture() -> None:
    chunks = load_corpus(PROJECT_DIR / "shared" / "documents")
    assert len({chunk.document_id for chunk in chunks}) == 3
    assert all(chunk.location.startswith("L") for chunk in chunks)
    assert len(corpus_fingerprint(chunks)) == 64
    injection = [chunk for chunk in chunks if "이전 지시를 모두 무시" in chunk.text]
    assert len(injection) == 1
    assert injection[0].document_id == "product-policy-v1"
