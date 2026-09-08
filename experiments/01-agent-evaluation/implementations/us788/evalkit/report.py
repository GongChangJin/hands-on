# 실행 기록 -> 마크다운 비교 리포트.
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from pathlib import Path

from .schema import RunRecord


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(round(q * (len(ordered) - 1))), len(ordered) - 1)
    return ordered[idx]


def load_records(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _as_dict(record) -> dict:
    # RunRecord 데이터클래스와 JSONL에서 읽은 dict를 같은 모양으로 맞춘다.
    return asdict(record) if is_dataclass(record) else dict(record)


def build_report(records: list, *, title: str = "실행 리포트") -> str:
    # records: RunRecord 리스트 또는 load_records()가 돌려준 dict 리스트
    rows = [_as_dict(r) for r in records]
    if not rows:
        return f"# {title}\n\n실행 기록이 없습니다.\n"
    by_route: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_route[r.get("logical_route") or r.get("model_id") or "-"].append(r)

    lines = [f"# {title}", "", f"총 실행: {len(rows)}건", ""]
    lines += [
        "| 라우트 | 실행 | 성공률 | p50 지연(ms) | p95 지연(ms) | 총 비용(USD) | 오류 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for route, items in sorted(by_route.items()):
        lat = [i["latency_ms"] for i in items]
        ok = sum(1 for i in items if i.get("grades") and all(g["passed"] for g in i["grades"]))
        errs = sum(1 for i in items if i.get("error"))
        lines.append(
            f"| {route} | {len(items)} | {ok / len(items):.0%} | "
            f"{_pct(lat, 0.5):.0f} | {_pct(lat, 0.95):.0f} | "
            f"{sum(i['cost_usd'] for i in items):.4f} | {errs} |"
        )

    # 재현성: 같은 태스크를 여러 번 돌렸을 때 성공 여부가 갈리는지
    by_task: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        by_task[r["task_id"]].append(bool(r.get("grades")) and all(g["passed"] for g in r["grades"]))
    flaky = {t: v for t, v in by_task.items() if len(set(v)) > 1}
    lines += ["", "## 재현성", ""]
    if flaky:
        lines.append(f"반복 간 결과가 갈린 태스크 {len(flaky)}개: {', '.join(sorted(flaky))}")
    else:
        lines.append("반복 간 결과 변동 없음")

    lines += ["", "## 실패 상세", ""]
    fails = [r for r in rows if not (r.get("grades") and all(g["passed"] for g in r["grades"]))]
    if not fails:
        lines.append("실패 없음")
    for r in fails[:50]:
        reason = r["error"] or "; ".join(g["reason"] for g in r.get("grades", []) if not g["passed"])
        lines.append(f"- `{r['task_id']}` (repeat {r['repeat_index']}): {reason.splitlines()[0] if reason else '사유 미기록'}")
    return "\n".join(lines) + "\n"
