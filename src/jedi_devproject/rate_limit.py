from __future__ import annotations

import hashlib
import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

MAX_RATE_LIMIT_KEY_BYTES = 256
MAX_RATE_LIMIT_BUCKETS = 10_000
MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS = 10_000
MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS = 24 * 60 * 60
MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS = 100_000
RATE_LIMIT_OVERFLOW_BUCKET_KEY = "rate-limit-overflow"


class RateLimitDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    allowed: bool
    retry_after_seconds: int


def is_valid_rate_limit_decision(decision: object) -> bool:
    return (
        isinstance(decision, RateLimitDecision)
        and type(decision.allowed) is bool
        and type(decision.retry_after_seconds) is int
        and decision.retry_after_seconds >= 0
    )


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: int,
        max_buckets: int = MAX_RATE_LIMIT_BUCKETS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        _validate_rate_limit_integer(max_requests, name="max_requests")
        _validate_rate_limit_integer(window_seconds, name="window_seconds")
        _validate_rate_limit_integer(max_buckets, name="max_buckets")
        _validate_rate_limit_clock(clock)
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if max_requests > MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS:
            raise ValueError(f"max_requests must be at most {MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS}")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        if window_seconds > MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS:
            raise ValueError(
                f"window_seconds must be at most {MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS}"
            )
        if max_buckets < 1:
            raise ValueError("max_buckets must be at least 1")
        if max_buckets > MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS:
            raise ValueError(f"max_buckets must be at most {MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS}")
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._max_buckets = max_buckets
        self._clock = clock
        self._last_now: float | None = None
        self._lock = threading.Lock()
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> RateLimitDecision:
        _validate_rate_limit_key(key)
        with self._lock:
            bucket_key = _rate_limit_bucket_key(key)
            now = self._now()
            window_start = now - self._window_seconds
            self._prune_expired_buckets(window_start)
            if bucket_key not in self._requests and len(self._requests) >= self._max_buckets:
                bucket_key = RATE_LIMIT_OVERFLOW_BUCKET_KEY
                if bucket_key not in self._requests and len(self._requests) >= self._max_buckets:
                    oldest_bucket_key = next(iter(self._requests))
                    del self._requests[oldest_bucket_key]
            requests = self._requests[bucket_key]
            while requests and requests[0] <= window_start:
                requests.popleft()
            if len(requests) >= self._max_requests:
                retry_after = max(1, int((requests[0] + self._window_seconds) - now))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
            requests.append(now)
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def _now(self) -> float:
        now = self._clock()
        _validate_rate_limit_clock_value(now)
        if self._last_now is not None and now < self._last_now:
            return self._last_now
        self._last_now = now
        return now

    def _prune_expired_buckets(self, window_start: float) -> None:
        expired_bucket_keys: list[str] = []
        for bucket_key, requests in self._requests.items():
            while requests and requests[0] <= window_start:
                requests.popleft()
            if not requests:
                expired_bucket_keys.append(bucket_key)
        for bucket_key in expired_bucket_keys:
            del self._requests[bucket_key]


def _validate_rate_limit_integer(value: object, *, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def _validate_rate_limit_key(key: object) -> None:
    if type(key) is not str:
        raise ValueError("rate limit key must be an exact string")


def _validate_rate_limit_clock_value(value: object) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise ValueError("rate limit clock must return a finite non-negative number")


def _validate_rate_limit_clock(clock: object) -> None:
    if not callable(clock):
        raise ValueError("rate limit clock must be callable")


def _rate_limit_bucket_key(key: str) -> str:
    try:
        encoded_key = key.encode("ascii")
    except UnicodeEncodeError:
        return _hashed_rate_limit_key(key)
    if len(encoded_key) > MAX_RATE_LIMIT_KEY_BYTES:
        return _hashed_rate_limit_key(key)
    if any(character.isspace() or ord(character) < 33 or ord(character) > 126 for character in key):
        return _hashed_rate_limit_key(key)
    return key


def _hashed_rate_limit_key(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8", errors="surrogatepass")).hexdigest()
    return f"sha256:{digest}"
