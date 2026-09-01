"""智能体端点：SSE 对话流 + 会话管理。"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.agent.agent import run_agent
from backend.agent.session import get_session_store
from backend.agent.sse import sse_event
from backend.config import settings
from backend.schemas.agent import ChatRequest, SessionInfo

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """SSE 流式对话：EventSource 不支持 POST，前端用 fetch + ReadableStream 解析。"""
    if not settings.DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="DEEPSEEK_API_KEY 未配置，AI 助手不可用")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    session = get_session_store().get_or_create(req.session_id)

    async def event_stream():
        async for event in run_agent(session, req.message):
            yield sse_event(dict(event))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
def get_session(session_id: str) -> SessionInfo:
    session = get_session_store().get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return SessionInfo(
        session_id=session.id,
        messages=[{"role": m["role"], "content": str(m.get("content", ""))} for m in session.messages if m.get("content")],
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
    deleted = get_session_store().delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"deleted": session_id}
