"""开发启动：按需启动虚拟矢网 + FastAPI 后端（:8000）。

用法：
    python scripts/dev.py
"""
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def main() -> int:
    use_virtual = os.getenv("USE_VIRTUAL_VISA", "1") != "0"

    if use_virtual:
        if port_open(5025):
            print("[dev] 虚拟矢网已在运行（5025）")
        else:
            print("[dev] 启动虚拟矢网…")
            subprocess.Popen(
                [sys.executable, str(ROOT / "scripts" / "virtual_visa_server.py")],
                cwd=ROOT,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )

    if port_open(8000):
        print("[dev] 后端已在运行（8000），无需重复启动")
        return 0

    print("[dev] 启动 FastAPI 后端 http://127.0.0.1:8000")
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
