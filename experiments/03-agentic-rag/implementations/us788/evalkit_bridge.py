# evalkit 은 01 Agent Evaluation 프로젝트에 한 벌만 두고 여기서는 경로로 참조한다.
# (같은 코드를 실험마다 복제하지 않는다는 팀 원칙)
from __future__ import annotations

import sys
from pathlib import Path

EVALKIT_HOME = (
    Path(__file__).resolve().parents[3]
    / "01-agent-evaluation"
    / "implementations"
    / "us788"
)

if not (EVALKIT_HOME / "evalkit").is_dir():
    raise ImportError(f"evalkit 을 찾을 수 없습니다: {EVALKIT_HOME}")

if str(EVALKIT_HOME) not in sys.path:
    sys.path.insert(0, str(EVALKIT_HOME))
