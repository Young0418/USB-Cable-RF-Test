"""历史记录端点：列表 / 单条 / 清空。"""
from fastapi import APIRouter, HTTPException, Query

from backend.schemas.history import HistoryList
from backend.services.history_service import history_service

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryList)
def list_history(limit: int = Query(10, ge=1, le=50)) -> HistoryList:
    return HistoryList(records=history_service.recent(limit))


@router.get("/{record_id}")
def get_history(record_id: str) -> dict:
    record = history_service.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.delete("")
def clear_history() -> dict:
    cleared = history_service.clear()
    return {"cleared": cleared}
