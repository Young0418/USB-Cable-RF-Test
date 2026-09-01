"""FastAPI 应用入口：应用工厂 + CORS + 路由注册 + uvicorn 启动。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import agent, detection, health, history, thresholds

API_PREFIX = "/api"
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="USB Cable RF Test API",
        description="USB 线缆射频测试系统：S 参数检测、阈值判定、PDF/二维码报告、AI 智能助手。",
        version="2.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 各 router 已自带 /api 前缀，这里不再叠加
    app.include_router(health.router)
    app.include_router(detection.router)
    app.include_router(history.router)
    app.include_router(thresholds.router)
    app.include_router(agent.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
