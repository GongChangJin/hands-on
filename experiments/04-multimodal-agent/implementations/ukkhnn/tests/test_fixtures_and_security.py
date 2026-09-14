from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from multimodal_agent.fixtures import prepare_shared, validate_fixtures
from multimodal_agent.paths import FIXTURES_DIR, LABELS_DIR, TASKS_PATH
from multimodal_agent.preprocessing import ImageSafetyError, _signature_mime, preprocess_image
from multimodal_agent.privacy import scan_texts


def test_shared_fixtures_are_complete_and_valid() -> None:
    summary = validate_fixtures()
    assert summary["fixture_count"] == 24
    assert summary["defect_count"] == 20
    assert summary["normal_count"] == 4
    assert summary["task_count"] == 48
    assert summary["privacy_findings"] == 0
    assert set(summary["error_type_counts"]) == {
        "layout_break",
        "element_clipping",
        "invalid_state",
        "error_message",
        "accessibility_issue",
    }


def test_prepare_is_byte_reproducible() -> None:
    before = (FIXTURES_DIR / "ui-error-001.png").read_bytes()
    before_tasks = TASKS_PATH.read_bytes()
    summary = prepare_shared()
    assert summary["status"] == "valid"
    assert (FIXTURES_DIR / "ui-error-001.png").read_bytes() == before
    assert TASKS_PATH.read_bytes() == before_tasks


def test_preprocessor_standardizes_to_metadata_free_png() -> None:
    prepared = preprocess_image(FIXTURES_DIR / "ui-error-001.png")
    assert (prepared.width, prepared.height) == (1280, 720)
    assert prepared.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert prepared.metadata_removed == ()
    with Image.open(io.BytesIO(prepared.png_bytes)) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert not image.info


def test_outside_fixture_is_rejected_before_decode(tmp_path: Path) -> None:
    outside = tmp_path / "ui-error-001.png"
    outside.write_bytes((FIXTURES_DIR / "ui-error-001.png").read_bytes())
    with pytest.raises(ImageSafetyError, match="fixture") as caught:
        preprocess_image(outside)
    assert caught.value.code == "outside_fixture_directory"


def test_symlink_is_rejected(tmp_path: Path) -> None:
    link = tmp_path / "linked.png"
    link.symlink_to(FIXTURES_DIR / "ui-error-001.png")
    with pytest.raises(ImageSafetyError) as caught:
        preprocess_image(link)
    assert caught.value.code == "symlink_rejected"


def test_signature_detection_does_not_trust_extension() -> None:
    with pytest.raises(ImageSafetyError) as caught:
        _signature_mime(b"not a png")
    assert caught.value.code == "invalid_signature"


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("contact demo.user" + "@" + "example.com", "email"),
        ("api_key=" + "abcdefghijklmnop", "assigned_secret"),
        ("Bearer " + "abcdefghijklmnop", "bearer_token"),
        ("010" + "-1234-5678", "phone"),
    ],
)
def test_privacy_patterns_are_detected(text: str, kind: str) -> None:
    findings = scan_texts([("test", text)])
    assert {finding.kind for finding in findings} == {kind}


def test_every_individual_label_matches_aggregate() -> None:
    rows = [
        json.loads(line)
        for line in (LABELS_DIR / "labels.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        individual = json.loads((LABELS_DIR / f"{row['fixture_id']}.json").read_text())
        assert row == individual
