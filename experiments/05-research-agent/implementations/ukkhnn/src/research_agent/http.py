"""Bounded HTTP client with explicit retries and failure classification."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from .types import RunStats, WorkflowFailure


USER_AGENT = "GongChangJin-Research-Agent/0.1 (+https://github.com/GongChangJin/hands-on)"
RETRY_STATUS = {429, 500, 502, 503, 504}


def classify_status(status: int) -> str:
    if status in (401, 403):
        return "authentication"
    if status == 429:
        return "rate_limit"
    if status >= 500:
        return "server_error"
    return "http_error"


class ResilientClient:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 20.0,
        maximum_attempts: int = 5,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        stats: RunStats | None = None,
        minimum_intervals: dict[str, float] | None = None,
    ) -> None:
        live_client = client is None
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml"},
        )
        self.maximum_attempts = maximum_attempts
        self.backoff_seconds = backoff_seconds
        self.sleep = sleep
        self.stats = stats or RunStats()
        self.minimum_intervals = minimum_intervals if minimum_intervals is not None else ({"semantic_scholar": 1.0} if live_client else {})
        self._last_request_started: dict[str, float] = {}

    def close(self) -> None:
        self.client.close()

    def request(
        self,
        source: str,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        interval = max(0.0, float(self.minimum_intervals.get(source, 0.0)))
        previous = self._last_request_started.get(source)
        now = time.monotonic()
        if previous is not None and now - previous < interval:
            self.sleep(interval - (now - previous))
        self._last_request_started[source] = time.monotonic()
        last_failure: WorkflowFailure | None = None
        for attempt in range(self.maximum_attempts):
            started = time.perf_counter()
            try:
                response = self.client.request(method, url, params=params, headers=headers)
            except httpx.TimeoutException as exc:
                failure = WorkflowFailure("timeout", f"{source} request timed out", retryable=True)
                last_failure = failure
                self.stats.request(source, (time.perf_counter() - started) * 1000)
                if attempt + 1 == self.maximum_attempts:
                    raise failure from exc
            except httpx.RequestError as exc:
                failure = WorkflowFailure("connection", f"{source} connection failed", retryable=True)
                last_failure = failure
                self.stats.request(source, (time.perf_counter() - started) * 1000)
                if attempt + 1 == self.maximum_attempts:
                    raise failure from exc
            else:
                self.stats.request(source, (time.perf_counter() - started) * 1000)
                if response.status_code < 400:
                    return response
                kind = classify_status(response.status_code)
                retryable = response.status_code in RETRY_STATUS
                failure = WorkflowFailure(
                    kind,
                    f"{source} returned HTTP {response.status_code}",
                    retryable=retryable,
                )
                last_failure = failure
                if not retryable or attempt + 1 == self.maximum_attempts:
                    raise failure
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = min(float(retry_after), 5.0)
                else:
                    delay = self.backoff_seconds * (2**attempt)
                self.sleep(delay)
                continue
            self.sleep(self.backoff_seconds * (2**attempt))
        assert last_failure is not None
        raise last_failure
