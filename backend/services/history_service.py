"""历史记录持久化：data/history.json（线程安全 + 原子写）。"""
import json
import threading
from pathlib import Path

from backend.config import settings


class HistoryService:
    def __init__(self, path: Path | None = None, limit: int | None = None):
        self._path = path or (settings.DATA_DIR / "history.json")
        self._limit = limit or settings.HISTORY_LIMIT
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list:
        if not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _persist(self, records: list) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        tmp.replace(self._path)

    def recent(self, n: int = 10) -> list:
        with self._lock:
            return self._load()[:n]

    def add(self, record: dict) -> dict:
        with self._lock:
            records = self._load()
            records.insert(0, record)
            records = records[: self._limit]
            self._persist(records)
        return record

    def get(self, record_id: str) -> dict | None:
        with self._lock:
            for r in self._load():
                if r.get("id") == record_id:
                    return r
        return None

    def clear(self) -> int:
        with self._lock:
            n = len(self._load())
            self._persist([])
        return n


history_service = HistoryService()
