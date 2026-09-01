"""智能体模块：基于 DeepSeek function calling 的工具调用 Agent。"""
from openai import OpenAI

from backend.config import settings

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """获取（或懒创建）OpenAI 兼容客户端。未配置密钥时抛 RuntimeError。"""
    global _client
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置，AI 助手不可用")
    if _client is None:
        _client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)
    return _client


def reset_client() -> None:
    global _client
    _client = None
