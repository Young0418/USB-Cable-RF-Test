"""历史记录 Pydantic 模型（替代死文件 protocol/hardware_protocol.py）。"""
from pydantic import BaseModel

from .detection import DetectionResult


class HistoryRecord(BaseModel):
    id: str
    timestamp: str
    cable_type: str
    length: float
    qualified: bool
    message: str
    result: DetectionResult


class HistoryList(BaseModel):
    records: list[HistoryRecord]
