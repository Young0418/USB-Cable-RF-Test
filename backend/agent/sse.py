"""SSE（Server-Sent Events）序列化工具。"""
import json


def sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
