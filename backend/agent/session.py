"""智能体会话：内存存储 + 可选 JSON 持久化，消息数上限。"""
import json
import threading
import time
import uuid
from pathlib import Path

from backend.agent.prompts import SYSTEM_PROMPT
from backend.config import settings


class AgentSession:
    def __init__(self, session_id: str | None = None) -> None:
        self.id = session_id or uuid.uuid4().hex
        self.created_at = time.time()
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, content: str | None, tool_calls: list | None = None) -> None:
        msg: dict = {"role": "assistant"}
        if content is not None:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self.messages.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )

    def trim(self, cap: int) -> None:
        """超出上限时裁掉最旧的非 system 消息。"""
        cap = max(4, cap)  # 至少要给模型留点对话空间
        if len(self.messages) <= cap:
            return
        overflow = len(self.messages) - cap
        # 保留 system 与最后 cap-1 条
        self.messages = [self.messages[0]] + self.messages[1 + overflow:]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": time.time(),
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSession":
        s = cls(session_id=data.get("id"))
        s.created_at = data.get("created_at", s.created_at)
        s.messages = data.get("messages", s.messages) or [{"role": "system", "content": SYSTEM_PROMPT}]
        if not s.messages or s.messages[0].get("role") != "system":
            s.messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        return s


class AgentSessionStore:
    """内存 dict + 可选 JSON 持久化（data/agent_sessions.json）。"""

    def __init__(self, persist_path: Path | None = None) -> None:
        self._sessions: dict[str, AgentSession] = {}
        self._lock = threading.Lock()
        self._persist_path = persist_path
        self._load()

    # ---- 持久化 ----
    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for item in raw:
                s = AgentSession.from_dict(item)
                self._sessions[s.id] = s
        except Exception:
            pass

    def _save(self) -> None:
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._persist_path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps([s.to_dict() for s in self._sessions.values()], ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self._persist_path)
        except Exception:
            pass

    # ---- 会话操作 ----
    def get(self, session_id: str) -> AgentSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> AgentSession:
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]
            s = AgentSession(session_id=session_id)
            self._sessions[s.id] = s
            self._save()
            return s

    def delete(self, session_id: str) -> bool:
        with self._lock:
            existed = self._sessions.pop(session_id, None) is not None
            if existed:
                self._save()
            return existed

    def list_info(self, limit: int = 50) -> list[dict]:
        with self._lock:
            items = sorted(
                self._sessions.values(), key=lambda s: s.to_dict()["updated_at"], reverse=True
            )
            return [
                {
                    "id": s.id,
                    "created_at": s.created_at,
                    "updated_at": s.to_dict()["updated_at"],
                    "message_count": len(s.messages),
                }
                for s in items[:limit]
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


_session_store: AgentSessionStore | None = None


def get_session_store() -> AgentSessionStore:
    global _session_store
    if _session_store is None:
        _session_store = AgentSessionStore(persist_path=settings.DATA_DIR / "agent_sessions.json")
    return _session_store
