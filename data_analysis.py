import pandas as pd

def analyze_s_params(hardware_dict):
    """
    输入：硬件同学返回的hardware_protocol格式字典
    输出：analysis_protocol格式字典（整合均值分析+所有点判定）
    """
    # ========== 步骤1：按硬件协议提取数据 ==========
    s11_list = hardware_dict.get("S11", [])
    s21_list = hardware_dict.get("S21", [])
    test_points = hardware_dict.get("test_points", [])
    device_info = hardware_dict.get("device_info", {})
    cable_type = device_info.get("cable_type", "未知")

    # ========== 步骤2：保留原有均值分析逻辑 ==========
    s11_mean = pd.Series(s11_list).mean() if len(s11_list) > 0 else 0.0
    s21_mean = pd.Series(s21_list).mean() if len(s21_list) > 0 else 0.0

    # ========== 步骤3：整合judge_qual的所有点判定逻辑 ==========
    S11_THRESHOLD = -20   # S11 必须小于 -20 dB
    S21_THRESHOLD = -3    # S21 必须大于 -3 dB
    s11_qualified = all(m < S11_THRESHOLD for m in s11_list) if s11_list else False
    s21_qualified = all(m > S21_THRESHOLD for m in s21_list) if s21_list else False
    overall_qualified = s11_qualified and s21_qualified

    # ========== 步骤4：保留原有状态描述逻辑 ==========
    if s11_mean < -20 and s21_mean > -3:
        status = '性能良好'
    elif s11_mean < -15 and s21_mean > -5:
        status = '合格'
    else:
        status = '不合格'
    message = f"{cable_type} - {status}（S11均值：{s11_mean:.2f}dB，S21均值：{s21_mean:.2f}dB）"

    # ========== 步骤5：按analysis_protocol格式返回 ==========
    return {
        "device_info": device_info,  # 来自硬件字典
        "qualified": overall_qualified,  # 整体合格状态（布尔值）
        "message": message,  # 整体描述
        "s11_qualified": s11_qualified,  # S11合格状态
        "s21_qualified": s21_qualified,  # S21合格状态
        "s11_data": [test_points, s11_list],  # 绘图数据
        "s21_data": [test_points, s21_list],  # 绘图数据
        "analysis_detail": {  # 分析详情（均值）
            "s11_mean": round(s11_mean, 2),
            "s21_mean": round(s21_mean, 2)
        }
    }

# 测试用：模拟硬件字典验证
if __name__ == "__main__":
    mock_hardware = {
        "S11": [-21.1, -22.2, -23.3],
        "S21": [-1.1, -2.2, -3.1],
        "device_info": {"model": "思仪3674", "cable_type": "50Ω射频同轴电缆", "test_time": "2026-02-21 10:00:00"},
        "test_points": [1,2,3]
    }
    test_result = analyze_s_params(mock_hardware)
    print(test_result["s11_qualified"],test_result["s21_qualified"])
    print("是否符合分析协议：", all(key in test_result for key in ["device_info", "qualified",
        "message","s11_qualified", "s21_qualified", "s11_data", "s21_data", "analysis_detail"]))