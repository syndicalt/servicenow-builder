"""Bounded, deterministic in-memory caching for retrieval results.

Entries are stored and served as deep copies so callers can never mutate cached
state, and the cache is LRU-bounded so it cannot grow without limit. See
``jedi_devproject.rag`` for the retrieval caching policy, including why live
public-web retrievals are never cached.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

_ResultT = TypeVar("_ResultT", bound=BaseModel)

DEFAULT_MAX_ENTRIES = 256


@dataclass(frozen=True)
class RetrievalCacheStats:
    """Point-in-time cache counters for retrieval observability."""

    hits: int
    misses: int
    size: int
    max_size: int

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class RetrievalCache(Generic[_ResultT]):
    """Bounded LRU cache mapping deterministic keys to retrieval result lists."""

    def __init__(self, *, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._max_entries = max_entries
        self._entries: OrderedDict[str, list[_ResultT]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> list[_ResultT] | None:
        entry = self._entries.get(key)
        if entry is None:
            self._misses += 1
            return None
        self._entries.move_to_end(key)
        self._hits += 1
        return [result.model_copy(deep=True) for result in entry]

    def put(self, key: str, results: Sequence[_ResultT]) -> None:
        self._entries[key] = [result.model_copy(deep=True) for result in results]
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def stats(self) -> RetrievalCacheStats:
        return RetrievalCacheStats(
            hits=self._hits,
            misses=self._misses,
            size=len(self._entries),
            max_size=self._max_entries,
        )
