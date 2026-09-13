"""Generate and comprehensively validate the shared fixture contract."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .contracts import ERROR_TYPES, SEVERITIES, validate_contract
from .paths import CONTEXT_DIR, FIXTURES_DIR, LABELS_DIR, SHARED_DIR, STANDARD_SIZE, TASKS_PATH
from .preprocessing import preprocess_image
from .privacy import scan_texts


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def prepare_shared() -> dict[str, Any]:
    generator = SHARED_DIR / "generate_fixtures.py"
    subprocess.run([sys.executable, str(generator)], check=True)
    return validate_fixtures()


def validate_fixtures() -> dict[str, Any]:
    manifest = json.loads((SHARED_DIR / "manifest.json").read_text(encoding="utf-8"))
    labels = _jsonl(LABELS_DIR / "labels.jsonl")
    contexts = _jsonl(CONTEXT_DIR / "contexts.jsonl")
    tasks = _jsonl(TASKS_PATH)
    images = sorted(FIXTURES_DIR.glob("*.png"))
    if len(images) < 20:
        raise ValueError("공통 fixture는 최소 20장이어야 합니다.")
    if not (len(images) == len(labels) == len(contexts) == manifest["fixture_count"]):
        raise ValueError("fixture, label, context와 manifest 개수가 일치하지 않습니다.")

    labels_by_id = {row["fixture_id"]: row for row in labels}
    contexts_by_id = {row["fixture_id"]: row for row in contexts}
    errors = Counter()
    severities = Counter()
    all_scan_values: list[tuple[str, str]] = []
    for image in images:
        prepared = preprocess_image(image)
        label = labels_by_id.get(image.stem)
        context = contexts_by_id.get(image.stem)
        if label is None or context is None:
            raise ValueError(f"label/context 연결이 없습니다: {image.stem}")
        if prepared.metadata_removed:
            raise ValueError(f"불필요한 이미지 metadata가 남아 있습니다: {image.name}")
        if (prepared.width, prepared.height) != STANDARD_SIZE:
            raise ValueError(f"표준 크기가 아닙니다: {image.name}")
        if not label.get("synthetic") or label.get("contains_personal_data"):
            raise ValueError(f"합성·개인정보 label이 안전하지 않습니다: {image.name}")
        unknown = set(label["expected_error_types"]) - set(ERROR_TYPES)
        if unknown or label["severity"] not in SEVERITIES:
            raise ValueError(f"taxonomy 밖의 label입니다: {image.name}")
        if not label["expected_error_types"] and label["severity"] != "none":
            raise ValueError(f"정상 화면 severity가 none이 아닙니다: {image.name}")
        errors.update(label["expected_error_types"])
        severities.update([label["severity"]])
        all_scan_values.extend((f"{image.stem}.visible_text", value) for value in label["visible_text"])
        all_scan_values.extend((f"{image.stem}.context.{key}", str(value)) for key, value in context.items())

    findings = scan_texts(all_scan_values)
    if findings:
        kinds = ", ".join(sorted({finding.kind for finding in findings}))
        raise ValueError(f"fixture에서 개인정보 또는 비밀 형태 문자열을 탐지했습니다: {kinds}")

    expected_task_count = len(images) * 2
    if len(tasks) != expected_task_count or manifest["task_count"] != expected_task_count:
        raise ValueError("각 fixture에 두 입력 조건 task가 있어야 합니다.")
    pairs: Counter[str] = Counter()
    for task in tasks:
        validate_contract("task-request", task)
        fixture_id = task["expected_output"].get("fixture_id")
        if fixture_id not in labels_by_id:
            raise ValueError(f"task의 fixture label이 없습니다: {task['task_id']}")
        condition = task["input"].get("condition")
        if condition not in {"image-only", "image-with-context"}:
            raise ValueError(f"알 수 없는 condition입니다: {task['task_id']}")
        pairs[fixture_id] += 1
        label = labels_by_id[fixture_id]
        if task["expected_output"]["error_types"] != label["expected_error_types"]:
            raise ValueError(f"task와 label 오류 유형이 다릅니다: {task['task_id']}")
    if any(count != 2 for count in pairs.values()):
        raise ValueError("fixture마다 정확히 두 condition task가 필요합니다.")

    return {
        "status": "valid",
        "fixture_count": len(images),
        "defect_count": sum(bool(row["expected_error_types"]) for row in labels),
        "normal_count": sum(not row["expected_error_types"] for row in labels),
        "task_count": len(tasks),
        "dimensions": list(STANDARD_SIZE),
        "format": "PNG",
        "privacy_findings": 0,
        "metadata_findings": 0,
        "error_type_counts": dict(sorted(errors.items())),
        "severity_counts": dict(sorted(severities.items())),
    }
