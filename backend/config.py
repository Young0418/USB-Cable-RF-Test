"""应用配置：从项目根目录 .env / 环境变量加载。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（backend/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


class Settings:
    # ---- DeepSeek AI ----
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ---- 硬件 ----
    USE_VIRTUAL_VISA: bool = _bool(os.getenv("USE_VIRTUAL_VISA"), True)
    VISA_ADDRESS: str = os.getenv("VISA_ADDRESS", "")

    # ---- 检测 ----
    DETECTION_TIMEOUT: int = int(os.getenv("DETECTION_TIMEOUT", "30"))

    # ---- 历史 ----
    HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "100"))
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))

    # ---- Agent ----
    AGENT_MAX_STEPS: int = int(os.getenv("AGENT_MAX_STEPS", "6"))
    AGENT_SESSION_CAP: int = int(os.getenv("AGENT_SESSION_CAP", "40"))


settings = Settings()
