from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from controller import run
from deepseek_client import DeepSeekClient
import os

app = FastAPI(title="线缆检测API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化DeepSeek客户端（需要设置环境变量DEEPSEEK_API_KEY）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
deepseek_client = DeepSeekClient(DEEPSEEK_API_KEY)

class TestRequest(BaseModel):
    cable_type: str

class AIAnalysisRequest(BaseModel):
    analysis_result: dict
    user_question: str = ""

@app.post("/test")
async def run_test(request: TestRequest):
    """执行线缆检测"""
    try:
        # 模拟异步检测过程
        result = await asyncio.to_thread(run, request.cable_type)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai-analysis")
async def get_ai_analysis(request: AIAnalysisRequest):
    """获取AI分析"""
    try:
        analysis = await asyncio.to_thread(
            deepseek_client.analyze_cable_data,
            request.analysis_result,
            request.user_question
        )
        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "analysis": f"AI分析失败：{str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)