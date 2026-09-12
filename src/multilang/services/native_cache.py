"""Bounded cache for immutable language, lexical, ranking and audio versions."""

from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from threading import RLock
from time import monotonic


class VersionedCache:
    def __init__(
        self,
        *,
        max_entries: int = 512,
        ttl_seconds: float = 300,
        clock: Callable[[], float] = monotonic,
    ):
        if max_entries < 1 or ttl_seconds <= 0:
            raise ValueError("cache bounds must be positive")
        self.max_entries, self.ttl_seconds, self.clock = max_entries, ttl_seconds, clock
        self._entries: OrderedDict[tuple[str, str, str], tuple[float, object]] = OrderedDict()
        self._lock = RLock()

    def get(self, namespace: str, version: str, key: str):
        lookup = (namespace, version, key)
        with self._lock:
            stored = self._entries.get(lookup)
            if stored is None:
                return None
            expires, value = stored
            if self.clock() >= expires:
                del self._entries[lookup]
                return None
            self._entries.move_to_end(lookup)
            return deepcopy(value)

    def put(self, namespace: str, version: str, key: str, value: object) -> None:
        if not namespace or not version or not key:
            raise ValueError("cache requires namespace, version and key")
        with self._lock:
            lookup = (namespace, version, key)
            self._entries[lookup] = (self.clock() + self.ttl_seconds, deepcopy(value))
            self._entries.move_to_end(lookup)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def invalidate(self, namespace: str, key: str | None = None) -> None:
        with self._lock:
            for lookup in tuple(self._entries):
                if lookup[0] == namespace and (key is None or lookup[2] == key):
                    del self._entries[lookup]
