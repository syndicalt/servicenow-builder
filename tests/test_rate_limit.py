from __future__ import annotations

import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import Any

from jedi_devproject.rate_limit import (
    MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS,
    MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS,
    MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS,
    MAX_RATE_LIMIT_KEY_BYTES,
    RATE_LIMIT_OVERFLOW_BUCKET_KEY,
    InMemoryRateLimiter,
    RateLimitDecision,
)


def test_rate_limiter_preserves_safe_bucket_keys() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, clock=lambda: 1000.0)

    assert limiter.check("127.0.0.1:/lifecycle/events").allowed is True
    assert limiter.check("127.0.0.1:/lifecycle/events").allowed is False

    assert list(limiter._requests) == ["127.0.0.1:/lifecycle/events"]


def test_rate_limiter_hashes_oversized_bucket_keys_without_storing_raw_value() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, clock=lambda: 1000.0)
    raw_key = "client_secret=secret-value-" + ("x" * (MAX_RATE_LIMIT_KEY_BYTES + 1))

    assert limiter.check(raw_key).allowed is True
    assert limiter.check(raw_key).allowed is False

    stored_key = next(iter(limiter._requests))
    assert stored_key.startswith("sha256:")
    assert len(stored_key) == 71
    assert "secret-value" not in stored_key
    assert raw_key not in limiter._requests


def test_rate_limiter_hashes_control_and_non_ascii_bucket_keys() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, clock=lambda: 1000.0)
    raw_key = "10.0.0.1:/lifecycle/events\né"

    assert limiter.check(raw_key).allowed is True
    assert limiter.check(raw_key).allowed is False

    stored_key = next(iter(limiter._requests))
    assert stored_key.startswith("sha256:")
    assert "\n" not in stored_key
    assert "é" not in stored_key
    assert raw_key not in limiter._requests


def test_rate_limiter_rejects_non_exact_string_keys_before_state_access() -> None:
    class StringSubclass(str):
        def encode(self, *_args: object, **_kwargs: object) -> bytes:
            raise AssertionError("string subclass encode should not be called")

    clock_calls = 0

    def clock() -> float:
        nonlocal clock_calls
        clock_calls += 1
        return 1000.0

    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, clock=clock)

    for key in (None, b"client-a", 123, StringSubclass("client-a")):
        try:
            limiter.check(key)  # type: ignore[arg-type]
        except ValueError as exc:
            assert str(exc) == "rate limit key must be an exact string"
        else:
            raise AssertionError(f"invalid rate-limit key was accepted: {key!r}")

    assert clock_calls == 0
    assert limiter._requests == {}


def test_rate_limiter_caps_live_bucket_count_with_overflow_bucket() -> None:
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        max_buckets=2,
        clock=lambda: 1000.0,
    )

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-b").allowed is True
    assert limiter.check("client-c").allowed is True
    assert limiter.check("client-d").allowed is False

    assert len(limiter._requests) == 2
    assert RATE_LIMIT_OVERFLOW_BUCKET_KEY in limiter._requests
    assert "client-c" not in limiter._requests
    assert "client-d" not in limiter._requests


def test_rate_limiter_prunes_expired_buckets_before_overflow() -> None:
    now = [1000.0]
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        max_buckets=2,
        clock=lambda: now[0],
    )

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-b").allowed is True
    now[0] = 1061.0
    assert limiter.check("client-c").allowed is True

    assert list(limiter._requests) == ["client-c"]
    assert RATE_LIMIT_OVERFLOW_BUCKET_KEY not in limiter._requests


def test_rate_limiter_rejects_excessive_bucket_caps() -> None:
    excessive_bucket_cap = MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS + 1

    try:
        InMemoryRateLimiter(
            max_requests=1,
            window_seconds=60,
            max_buckets=excessive_bucket_cap,
        )
    except ValueError as exc:
        assert "max_buckets must be at most" in str(exc)
    else:
        raise AssertionError("excessive rate-limit bucket cap was not rejected")


def test_rate_limiter_rejects_excessive_request_caps() -> None:
    excessive_request_cap = MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS + 1

    try:
        InMemoryRateLimiter(
            max_requests=excessive_request_cap,
            window_seconds=60,
        )
    except ValueError as exc:
        assert "max_requests must be at most" in str(exc)
    else:
        raise AssertionError("excessive rate-limit request cap was not rejected")


def test_rate_limiter_rejects_excessive_window_seconds() -> None:
    excessive_window_seconds = MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS + 1

    try:
        InMemoryRateLimiter(
            max_requests=1,
            window_seconds=excessive_window_seconds,
        )
    except ValueError as exc:
        assert "window_seconds must be at most" in str(exc)
    else:
        raise AssertionError("excessive rate-limit window was not rejected")


def test_rate_limiter_rejects_invalid_direct_numeric_controls() -> None:
    invalid_configs = [
        ({"max_requests": True, "window_seconds": 60}, "max_requests must be an integer"),
        ({"max_requests": "1", "window_seconds": 60}, "max_requests must be an integer"),
        ({"max_requests": 1, "window_seconds": True}, "window_seconds must be an integer"),
        ({"max_requests": 1, "window_seconds": "60"}, "window_seconds must be an integer"),
        (
            {"max_requests": 1, "window_seconds": 60, "max_buckets": True},
            "max_buckets must be an integer",
        ),
        (
            {"max_requests": 1, "window_seconds": 60, "max_buckets": "100"},
            "max_buckets must be an integer",
        ),
    ]

    for kwargs, expected_error in invalid_configs:
        try:
            InMemoryRateLimiter(**kwargs)  # type: ignore[arg-type]
        except ValueError as exc:
            assert str(exc) == expected_error
        else:
            raise AssertionError(f"invalid rate limiter controls were accepted: {kwargs!r}")


def test_rate_limiter_rejects_non_callable_clock_at_construction() -> None:
    for clock in (None, True, 1000.0, "1000.0"):
        try:
            InMemoryRateLimiter(
                max_requests=1,
                window_seconds=60,
                clock=clock,  # type: ignore[arg-type]
            )
        except ValueError as exc:
            assert str(exc) == "rate limit clock must be callable"
        else:
            raise AssertionError(f"invalid rate-limit clock was accepted: {clock!r}")


def test_rate_limiter_clamps_backward_clock_for_retry_after() -> None:
    times = iter([1000.0, 900.0])
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        clock=lambda: next(times),
    )

    assert limiter.check("client-a").allowed is True
    decision = limiter.check("client-a")

    assert decision.allowed is False
    assert decision.retry_after_seconds == 60


def test_rate_limiter_clamps_backward_clock_before_storing_timestamps() -> None:
    times = iter([1000.0, 900.0])
    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
        clock=lambda: next(times),
    )

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-a").allowed is True

    assert list(limiter._requests["client-a"]) == [1000.0, 1000.0]


def test_rate_limiter_rejects_invalid_clock_values_before_bucket_storage() -> None:
    invalid_values = [True, "1000.0", float("nan"), float("inf"), -1.0]

    for value in invalid_values:
        def invalid_clock(value: Any = value) -> Any:
            return value

        limiter = InMemoryRateLimiter(
            max_requests=1,
            window_seconds=60,
            clock=invalid_clock,
        )

        try:
            limiter.check("client-a")
        except ValueError as exc:
            assert str(exc) == "rate limit clock must return a finite non-negative number"
        else:
            raise AssertionError(f"invalid rate-limit clock value was accepted: {value!r}")

        assert limiter._requests == {}


class _RaceDeque(deque[float]):
    def __init__(self, *, parties: int) -> None:
        super().__init__()
        self._barrier = threading.Barrier(parties)
        self._local = threading.local()

    def __len__(self) -> int:
        calls = getattr(self._local, "len_calls", 0) + 1
        self._local.len_calls = calls
        should_wait = calls == 2
        current_length = super().__len__()
        if should_wait:
            with suppress(threading.BrokenBarrierError):
                self._barrier.wait(timeout=0.2)
        return current_length


def test_rate_limiter_serializes_concurrent_bucket_updates() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, clock=lambda: 1000.0)
    limiter._requests["client-a"] = _RaceDeque(parties=2)
    limiter._prune_expired_buckets = lambda _: None  # type: ignore[assignment,method-assign]
    start_barrier = threading.Barrier(2)

    def check() -> RateLimitDecision:
        start_barrier.wait(timeout=1.0)
        return limiter.check("client-a")

    with ThreadPoolExecutor(max_workers=2) as executor:
        decisions = list(executor.map(lambda _: check(), range(2)))

    assert [decision.allowed for decision in decisions].count(True) == 1
    assert len(limiter._requests["client-a"]) == 1
