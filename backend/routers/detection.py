"""检测相关端点：运行检测、下载 PDF 报告 / e-label 二维码。"""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.core import controller
from backend.schemas.detection import DetectionResult, RunDetectionRequest
from backend.services.elabel import generate_elabel
from backend.services.history_service import history_service
from backend.services.pdf_report import generate_pdf_report
from backend.services.result_cache import result_cache

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/run", response_model=DetectionResult)
def run_detection(req: RunDetectionRequest) -> DetectionResult:
    """执行一次完整检测。仪器离线时返回 502。"""
    try:
        result = controller.run(req.cable_type, req.length)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    result_id = uuid.uuid4().hex[:12]
    result["id"] = result_id
    try:
        det = DetectionResult.model_validate(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"结果格式错误: {exc}")

    # 写入缓存（PDF/e-label 复用，避免重复测量）+ 历史
    result_cache.set(result_id, result)
    history_service.add(
        {
            "id": result_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cable_type": result["cable_type"],
            "length": result["length"],
            "qualified": result["qualified"],
            "message": result["message"],
            "result": result,
        }
    )
    return det


def _cached_result(result_id: str) -> dict:
    result = result_cache.get(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在或已过期（缓存上限内）")
    return result


@router.get("/{result_id}/pdf")
def get_pdf(result_id: str) -> Response:
    result = _cached_result(result_id)
    data = generate_pdf_report(result)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{result_id}.pdf"'},
    )


@router.get("/{result_id}/elabel")
def get_elabel(result_id: str) -> Response:
    result = _cached_result(result_id)
    data = generate_elabel(result)
    return Response(
        content=data,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="elabel_{result_id}.png"'},
    )
