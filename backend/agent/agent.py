"""智能体运行循环：DeepSeek function calling 工具调用 + 分块文本输出。

事件流（yield dict）：
    session → start → (tool | text)* → done   （出错则 error → done）

上下文工程（P0）：
    - 摘要压缩：会话超上限时，最旧一轮先交给模型压成摘要再裁，避免丢关键信息
    - 死循环检测：同一 (tool, args) 连续调用过多次即中断
    - token 预算：累计 usage 超预算优雅停止
"""
import asyncio
import json

from backend.agent import get_openai_client
from backend.agent.session import AgentSession
from backend.agent.tools import TOOLS, execute_tool, parse_tool_arguments
from backend.config import settings

# 同一 (tool, args) 连续出现达到该次数即判定死循环
LOOP_REPEAT = 3

SUMMARIZE_PROMPT = """请把下面这段多轮对话压缩成一段中文摘要（200字以内），保留：
- 用户反复关心的线缆类型/长度
- 已执行的检测结论（合格与否、关键数值，如 S11/S21 均值、DTF 峰值）
- 仍未解决的疑问
只输出摘要正文，不要任何解释或前缀。"""


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
    usage = resp.usage
    return {
        "content": message.content,
        "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in (message.tool_calls or [])
        ],
        "finish_reason": resp.choices[0].finish_reason,
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
        },
    }


def _summarize_messages(messages: list[dict]) -> str:
    """把最旧一轮对话交给模型压成摘要（to_thread 里执行）。"""
    transcript = json.dumps(
        [
            {k: m.get(k) for k in ("role", "content", "tool_calls", "tool_call_id") if k in m}
            for m in messages
        ],
        ensure_ascii=False,
    )
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SUMMARIZE_PROMPT},
            {"role": "user", "content": transcript[:4000]},
        ],
        temperature=0.2,
        max_tokens=400,
        stream=False,
    )
    return (resp.choices[0].message.content or "").strip()


async def run_agent(session: AgentSession, user_text: str):
    """异步生成器：产出 AgentEvent 字典序列。"""
    session.add_user(user_text)

    yield {"type": "session", "session_id": session.id}
    yield {"type": "start"}

    try:
        # 预检：密钥是否配置
        get_openai_client()
    except Exception as exc:
        yield {"type": "error", "content": f"AI 服务未配置：{exc}"}
        yield {"type": "done"}
        return

    # 会话超上限：先压缩最旧一轮为摘要，压缩失败才硬裁剪
    overflow = session.overflow_messages(settings.AGENT_SESSION_CAP)
    if overflow is not None:
        try:
            summary = await asyncio.to_thread(_summarize_messages, overflow)
            session.compress(settings.AGENT_SESSION_CAP, summary)
        except Exception:
            session.trim(settings.AGENT_SESSION_CAP)
    else:
        session.trim(settings.AGENT_SESSION_CAP)

    total_tokens = 0
    last_sig: str | None = None
    repeat_count = 0

    for step in range(settings.AGENT_MAX_STEPS):
        try:
            result = await asyncio.to_thread(
                _run_model_call, list(session.messages)
            )
        except Exception as exc:
            yield {"type": "error", "content": f"模型调用失败：{exc}"}
            yield {"type": "done"}
            return

        # ---- token 预算 ----
        total_tokens += result["usage"]["total_tokens"]
        if settings.AGENT_TOKEN_BUDGET and total_tokens > settings.AGENT_TOKEN_BUDGET:
            yield {
                "type": "error",
                "content": f"已用 token 达 {total_tokens}，超过预算 {settings.AGENT_TOKEN_BUDGET}，提前停止。",
            }
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
            sig = f"{name}:{json.dumps(args, sort_keys=True, ensure_ascii=False)}"

            # ---- 死循环检测：同一 (tool, args) 连续重复即中断 ----
            if sig == last_sig:
                repeat_count += 1
            else:
                last_sig, repeat_count = sig, 1
            if repeat_count >= LOOP_REPEAT:
                yield {
                    "type": "error",
                    "content": f"检测到重复工具调用（{name} 连续 {LOOP_REPEAT} 次参数相同），已停止。",
                }
                yield {"type": "done"}
                return

            yield {"type": "tool", "tool": name, "args": args}
            # 工具执行放线程池，避免阻塞事件循环
            tool_result = await asyncio.to_thread(execute_tool, name, args)
            content = json.dumps(tool_result, ensure_ascii=False)
            session.add_tool_result(tc["id"], content)
    else:
        yield {"type": "error", "content": f"已达到最大步骤数（{settings.AGENT_MAX_STEPS}），已停止。"}

    session.trim(settings.AGENT_SESSION_CAP)
    yield {"type": "done"}
