# data_analysis_amended.py
import pandas as pd
from cable_thresholds import CABLE_THRESHOLDS, DEFAULT_THRESHOLD

def analyze_s_params(hardware_dict, cable_type):
    """
    严格遵循要求：
    - 输入：硬件协议字典 + 线缆类型（双入参）
    - 阈值：从 cable_thresholds.py.py 动态获取
    - 输出：完全符合 analysis_protocol 格式的字典
    """
    # 步骤1：按硬件协议提取数据
    s11_list = hardware_dict.get("S11", [])
    s21_list = hardware_dict.get("S21", [])
    test_points = hardware_dict.get("test_points", [])
    device_info = hardware_dict.get("device_info", {})

    # 步骤2：获取当前线缆的阈值
    final_cable_type = cable_type or "未知线缆"
    thresholds = CABLE_THRESHOLDS.get(final_cable_type, DEFAULT_THRESHOLD)

    # 步骤3：计算均值
    s11_mean = pd.Series(s11_list).mean() if len(s11_list) > 0 else 0.0
    s21_mean = pd.Series(s21_list).mean() if len(s21_list) > 0 else 0.0

    # 步骤4：所有点判定
    s11_qualified = all(m < thresholds["s11_all_threshold"] for m in s11_list) if s11_list else False
    s21_qualified = all(m > thresholds["s21_all_threshold"] for m in s21_list) if s21_list else False
    overall_qualified = s11_qualified and s21_qualified

    # 步骤5：状态描述
    if s11_mean < thresholds["s11_mean_good"] and s21_mean > thresholds["s21_mean_good"]:
        status = '性能良好'
    elif s11_mean < thresholds["s11_mean_pass"] and s21_mean > thresholds["s21_mean_pass"]:
        status = '合格'
    else:
        status = '不合格'
    message = f"{final_cable_type} - {status}（S11均值：{s11_mean:.2f}dB，S21均值：{s21_mean:.2f}dB）"

    # 步骤6：严格按 analysis_protocol 格式返回
    return {
        "device_info": device_info,
        "cable_type": final_cable_type,
        "qualified": overall_qualified,
        "message": message,
        "s11_qualified": s11_qualified,
        "s21_qualified": s21_qualified,
        "s11_data": [test_points, s11_list],
        "s21_data": [test_points, s21_list],
        "analysis_detail": {
            "s11_mean": round(s11_mean, 2),
            "s21_mean": round(s21_mean, 2)
        }
    }

# 模拟硬件数据函数（用于测试，可替换为真实硬件接口）
def get_cable_data():
    """模拟从硬件获取数据，返回符合 hardware_protocol 格式的字典"""
    return {
        "S11": [-21.1, -22.2, -23.3],
        "S21": [-1.1, -2.2, -3.1],
        "device_info": {"model": "思仪3674", "test_time": "2026-02-21 10:00:00"},
        "test_points": [1, 2, 3]
    }

# 主函数（用于测试）
def main():
    # 1. 获取硬件数据
    hardware_data = get_cable_data()

    # 2. 调用分析函数，传入硬件数据和线缆类型
    result = analyze_s_params(hardware_data, "RG316")

    # 3. 打印结果
    print("===== 分析结果 =====")
    for k, v in result.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
