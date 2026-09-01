"""结果缓存：{result_id: 结果字典}，供 PDF/e-label 复用，避免重复测量。"""
import threading
from collections import OrderedDict


class ResultCache:
    def __init__(self, capacity: int = 100):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._capacity = capacity
        self._lock = threading.Lock()

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > self._capacity:
                self._cache.popitem(last=False)

    def get(self, key: str) -> dict | None:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]


result_cache = ResultCache()
