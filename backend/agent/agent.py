"""智能体运行循环：DeepSeek function calling 工具调用 + 分块文本输出。

事件流（yield dict）：
    session → start → (tool | text)* → done   （出错则 error → done）
"""
import asyncio
import json

from backend.agent import get_openai_client
from backend.agent.session import AgentSession
from backend.agent.tools import TOOLS, execute_tool, parse_tool_arguments
from backend.config import settings


def _chunk_text(text: str, size: int = 40) -> list[str]:
    """把长文本切成小段，模拟打字机流式输出。"""
    text = text.strip()
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def _run_model_call(messages: list[dict]) -> dict:
    """非流式模型调用（to_thread 里执行），保证 tool_calls 重建可靠。"""
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=800,
        stream=False,
    )
    message = resp.choices[0].message
    return {
        "content": message.content,
        "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in (message.tool_calls or [])
        ],
        "finish_reason": resp.choices[0].finish_reason,
    }


async def run_agent(session: AgentSession, user_text: str):
    """异步生成器：产出 AgentEvent 字典序列。"""
    session.add_user(user_text)
    session.trim(settings.AGENT_SESSION_CAP)

    yield {"type": "session", "session_id": session.id}
    yield {"type": "start"}

    try:
        # 预检：密钥是否配置
        get_openai_client()
    except Exception as exc:
        yield {"type": "error", "content": f"AI 服务未配置：{exc}"}
        yield {"type": "done"}
        return

    for step in range(settings.AGENT_MAX_STEPS):
        try:
            result = await asyncio.to_thread(
                _run_model_call, list(session.messages)
            )
        except Exception as exc:
            yield {"type": "error", "content": f"模型调用失败：{exc}"}
            yield {"type": "done"}
            return

        tool_calls = result["tool_calls"]
        if not tool_calls:
            # 模型已给出最终文本
            for piece in _chunk_text(result["content"] or "（无输出）"):
                yield {"type": "text", "content": piece}
            break

        # 有工具调用：执行并把 assistant tool_calls + tool 结果回灌
        session.add_assistant(content=result["content"], tool_calls=tool_calls)
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = parse_tool_arguments(tc["function"]["arguments"])
            yield {"type": "tool", "tool": name, "args": args}
            # 工具执行放线程池，避免阻塞事件循环
            tool_result = await asyncio.to_thread(execute_tool, name, args)
            content = json.dumps(tool_result, ensure_ascii=False)
            session.add_tool_result(tc["id"], content)
    else:
        yield {"type": "error", "content": f"已达到最大步骤数（{settings.AGENT_MAX_STEPS}），已停止。"}

    session.trim(settings.AGENT_SESSION_CAP)
    yield {"type": "done"}
