# timeout / 모델 장애 / 낮은 confidence 에 대한 강등·승격 체인.
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, Sequence

# 어떤 라우트가 실패했을 때 다음으로 시도할 순서
DEFAULT_CHAIN: dict[str, Sequence[str]] = {
    "small": ("balanced", "frontier"),
    "balanced": ("frontier", "small"),
    "frontier": ("balanced",),
    "local": ("small", "balanced"),
}


class FallbackError(RuntimeError):
    def __init__(self, attempts: list[tuple[str, str]]):
        self.attempts = attempts
        super().__init__("모든 라우트 실패: " + ", ".join(f"{r}({e})" for r, e in attempts))


def with_fallback(
    call: Callable[[str], object],
    route: str,
    *,
    timeout_s: float = 30.0,
    chain: dict[str, Sequence[str]] | None = None,
):
    # call(route) 를 순서대로 시도하고, 성공한 (결과, 실제 사용 라우트, 시도 기록) 을 돌려준다.
    order = [route, *(chain or DEFAULT_CHAIN).get(route, ())]
    attempts: list[tuple[str, str]] = []
    for candidate in order:
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(call, candidate).result(timeout=timeout_s), candidate, attempts
        except FutureTimeout:
            attempts.append((candidate, f"timeout>{timeout_s}s"))
        except Exception as e:
            attempts.append((candidate, type(e).__name__))
    raise FallbackError(attempts)
