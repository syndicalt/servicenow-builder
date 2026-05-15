from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict


class RateLimitDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: int,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> RateLimitDecision:
        now = self._clock()
        window_start = now - self._window_seconds
        requests = self._requests[key]
        while requests and requests[0] <= window_start:
            requests.popleft()
        if len(requests) >= self._max_requests:
            retry_after = max(1, int((requests[0] + self._window_seconds) - now))
            return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
        requests.append(now)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)
