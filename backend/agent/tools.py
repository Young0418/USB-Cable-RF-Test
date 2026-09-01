"""智能体工具定义（DeepSeek function calling）与执行器。"""
import json

from backend.core import controller
from backend.core.thresholds import (
    DEFAULT_FREQ_THRESHOLD,
    DEFAULT_MEAN,
    FREQ_THRESHOLDS,
    MEAN_THRESHOLDS,
    SUPPORTED_LENGTHS,
    get_closest_length,
)
from backend.services.history_service import history_service

# ---- 工具 JSON Schema（DeepSeek / OpenAI function calling 标准格式）----
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_detection",
            "description": "对一根线缆执行S参数检测，返回合格判定、S11/S21均值、DTF峰值。线缆类型必须是 get_cable_types 返回的值之一。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cable_type": {"type": "string", "description": "线缆类型，如 RG316 / RG58 / 半刚电缆"},
                    "length": {"type": "number", "description": "线缆长度（米），如 10"},
                },
                "required": ["cable_type", "length"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_history",
            "description": "获取最近的历史检测记录（按时间倒序），用于回答\"上一次检测结果\"等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "返回条数，默认10，最大50"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_thresholds",
            "description": "获取指定线缆类型和长度的合格阈值（频率点、S11阈值、S21阈值、均值标准）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cable_type": {"type": "string", "description": "线缆类型，如 RG316"},
                    "length": {"type": "number", "description": "线缆长度（米），如 10"},
                },
                "required": ["cable_type", "length"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cable_types",
            "description": "获取系统支持的所有线缆类型列表。",
            "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        },
    },
]


# ---- 工具执行器 ----
def _summarize_detection(result: dict) -> dict:
    """把完整检测结果压缩为摘要，避免 1001 点数组撑爆上下文。"""
    import numpy as np

    dtf_dist, dtf_amp = result.get("dtf_data") or ([], [])
    peak = int(np.argmax(dtf_amp)) if dtf_amp else -1
    return {
        "ok": True,
        "cable_type": result["cable_type"],
        "length": result.get("length"),
        "qualified": result["qualified"],
        "message": result["message"],
        "s11_qualified": result["s11_qualified"],
        "s21_qualified": result["s21_qualified"],
        "s11_mean_db": result["analysis_detail"]["s11_mean"],
        "s21_mean_db": result["analysis_detail"]["s21_mean"],
        "dtf_peak_distance_m": round(dtf_dist[peak], 3) if peak >= 0 else None,
        "dtf_peak_db": round(dtf_amp[peak], 2) if peak >= 0 else None,
        "thresholds_length_used_m": result.get("thresholds", {}).get("length_used"),
    }


def _run_detection(args: dict) -> dict:
    try:
        cable_type = args["cable_type"]
        length = float(args.get("length", 5.0))
        result = controller.run(cable_type, length)
        return _summarize_detection(result)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _get_history(args: dict) -> dict:
    try:
        limit = min(int(args.get("limit", 10)), 50)
        records = history_service.recent(limit)
        return {
            "ok": True,
            "records": [
                {
                    "id": r["id"],
                    "cable_type": r["cable_type"],
                    "length": r.get("length"),
                    "qualified": r["qualified"],
                    "message": r["message"],
                    "timestamp": r.get("timestamp", ""),
                }
                for r in records
            ],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _get_thresholds(args: dict) -> dict:
    try:
        ct = args["cable_type"]
        ln = float(args.get("length", 5.0))
        closest = get_closest_length(ln, SUPPORTED_LENGTHS)
        ft = FREQ_THRESHOLDS.get(ct, {}).get(closest, DEFAULT_FREQ_THRESHOLD)
        return {
            "ok": True,
            "cable_type": ct,
            "length": ln,
            "closest_length": closest,
            "freqs": ft["freqs"],
            "S11": ft["S11"],
            "S21": ft["S21"],
            "mean": MEAN_THRESHOLDS.get(ct, DEFAULT_MEAN),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _get_cable_types(args: dict) -> dict:
    return {"ok": True, "cable_types": list(MEAN_THRESHOLDS.keys())}


_EXECUTORS = {
    "run_detection": _run_detection,
    "get_history": _get_history,
    "get_thresholds": _get_thresholds,
    "get_cable_types": _get_cable_types,
}


def execute_tool(name: str, args: dict) -> dict:
    executor = _EXECUTORS.get(name)
    if executor is None:
        return {"ok": False, "error": f"未知工具: {name}"}
    return executor(args)


def parse_tool_arguments(arguments: str) -> dict:
    try:
        data = json.loads(arguments or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
