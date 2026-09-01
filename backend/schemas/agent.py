"""智能体对话相关 Pydantic 模型。"""
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class AgentEvent(BaseModel):
    """SSE 事件负载。type: session/start/tool/text/done/error。"""
    type: str
    content: Optional[str] = None
    tool: Optional[str] = None
    args: Optional[dict] = None
    session_id: Optional[str] = None


class SessionMessage(BaseModel):
    role: str
    content: str


class SessionInfo(BaseModel):
    session_id: str
    messages: list[SessionMessage]
