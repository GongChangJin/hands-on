#!/usr/bin/env python3
# 단건 실행:  python run.py "질문" --route balanced
from __future__ import annotations

import argparse

import evalkit_bridge  # noqa: F401

from agent.graph import answer_question  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--route", default="balanced")
    args = ap.parse_args()
    state = answer_question(args.question, route=args.route)
    print(state.get("answer", ""))
    print("\n---")
    print("검색 시도:", state.get("attempts"))
    print("근거:", ", ".join(d.cite() for d in state.get("docs", [])) or "없음")
    print("계산:", state.get("calculations") or "없음")
    print("주입 의심:", state.get("forbidden_actions", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
