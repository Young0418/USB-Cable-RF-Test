"""阈值查询端点：线缆类型列表 + 阈值表（长度吸附）。"""
from fastapi import APIRouter, Query

from backend.core.thresholds import (
    DEFAULT_FREQ_THRESHOLD,
    DEFAULT_MEAN,
    FREQ_THRESHOLDS,
    MEAN_THRESHOLDS,
    SUPPORTED_LENGTHS,
    get_closest_length,
)

router = APIRouter(prefix="/api", tags=["thresholds"])


@router.get("/cable-types")
def cable_types() -> list[str]:
    return list(MEAN_THRESHOLDS.keys())


@router.get("/thresholds")
def thresholds(
    cable_type: str = Query(...),
    length: float = Query(1.0),
) -> dict:
    closest = get_closest_length(length, SUPPORTED_LENGTHS)
    if cable_type in FREQ_THRESHOLDS and closest in FREQ_THRESHOLDS[cable_type]:
        ft = FREQ_THRESHOLDS[cable_type][closest]
        length_used = closest
    else:
        ft = DEFAULT_FREQ_THRESHOLD
        length_used = None
    return {
        "cable_type": cable_type,
        "length": length,
        "length_used": length_used,
        "supported_lengths": SUPPORTED_LENGTHS,
        "freqs": ft["freqs"],
        "S11": ft["S11"],
        "S21": ft["S21"],
        "mean": MEAN_THRESHOLDS.get(cable_type, DEFAULT_MEAN),
    }
