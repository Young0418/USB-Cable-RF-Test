"""健康检查：应用状态 + AI 配置 + 硬件可达性。"""
import socket

from fastapi import APIRouter

from backend.config import settings

router = APIRouter(prefix="/api", tags=["health"])


def _hardware_status() -> dict:
    if settings.USE_VIRTUAL_VISA:
        # 轻量探测虚拟矢网端口（127.0.0.1:5025），超时 0.5s
        try:
            with socket.create_connection(("127.0.0.1", 5025), timeout=0.5):
                return {"mode": "virtual", "reachable": True, "address": "127.0.0.1:5025"}
        except OSError:
            return {"mode": "virtual", "reachable": False, "address": "127.0.0.1:5025"}
    return {"mode": "real", "reachable": "unknown", "address": settings.VISA_ADDRESS}


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "USB Cable RF Test",
        "ai": {
            "configured": bool(settings.DEEPSEEK_API_KEY),
            "model": settings.DEEPSEEK_MODEL,
            "base_url": settings.DEEPSEEK_BASE_URL,
        },
        "hardware": _hardware_status(),
        "version": "2.0",
    }
