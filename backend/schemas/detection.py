"""检测相关 Pydantic 模型（替代死文件 protocol/analysis_protocol.py）。"""
from typing import Optional

from pydantic import BaseModel


class DeviceInfo(BaseModel):
    model: str = ""
    test_time: str = ""


class AnalysisDetail(BaseModel):
    s11_mean: float = 0.0
    s21_mean: float = 0.0


class ThresholdConfig(BaseModel):
    """检测时实际使用的阈值（长度已吸附）。"""
    length_used: Optional[float] = None
    freqs: list[float] = []
    S11: list[float] = []
    S21: list[float] = []


class RunDetectionRequest(BaseModel):
    cable_type: str
    length: float = 1.0


class DetectionResult(BaseModel):
    """一次检测的完整结果（含曲线数据，用于前端绘图与 PDF/标签）。"""
    id: str
    cable_type: str
    length: float
    qualified: bool
    message: str
    s11_qualified: bool
    s21_qualified: bool
    device_info: DeviceInfo
    # 曲线为「两条并行列表」：第0项=横轴(freq/distance)，第1项=纵轴(S11/S21/DTF dB)
    s11_data: list[list[float]]  # [频率(Hz)列表, S11(dB)列表]
    s21_data: list[list[float]]  # [频率(Hz)列表, S21(dB)列表]
    dtf_data: list[list[float]]  # [距离(m)列表, 反射(dB)列表]
    thresholds: ThresholdConfig
    analysis_detail: AnalysisDetail
