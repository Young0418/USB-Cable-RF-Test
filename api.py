from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from controller import run
import uvicorn

app = FastAPI(title="USB线缆检测API")

class AnalyzeRequest(BaseModel):
    cable_type: str
    length:float=1.0 #线缆长度：单位：米

class AnalyzeResponse(BaseModel):
    device_info: dict
    cable_type: str
    qualified: bool
    message: str
    s11_qualified: bool
    s21_qualified: bool
    s11_data: list
    s21_data: list
    analysis_detail: dict

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        result = run(request.cable_type,request.length)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)