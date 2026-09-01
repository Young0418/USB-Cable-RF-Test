"""检测编排：串联硬件通信 + 数据分析，返回统一结果字典。"""
from .analysis import analyze_s_params
from .hardware import get_s_params


def run(cable_type, length):
    """执行一次完整检测。cable_type 为线缆类型，length 为长度（米）。"""
    try:
        # 1. 调用硬件模块，获取硬件协议字典
        hardware_dict = get_s_params()
        # 2. 调用数据分析模块，获取分析判定协议字典
        analysis_dict = analyze_s_params(hardware_dict, cable_type, length)
        analysis_dict["cable_type"] = cable_type
        return analysis_dict
    except Exception as exc:
        raise Exception(f"检测失败：{exc}") from exc
