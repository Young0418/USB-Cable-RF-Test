# 模拟硬件数据函数（用于测试，可替换为真实硬件接口）
import numpy as np
from cable_thresholds import FREQ_THRESHOLDS, MEAN_THRESHOLDS, DEFAULT_MEAN



def get_cable_data():
    """模拟从硬件获取数据，返回符合 hardware_protocol 格式的字典"""
    return {
        "S11": [-21.1, -22.2, -23.3],
        "S21": [-1.1, -2.2, -3.1],
        "device_info": {"model": "思仪3674", "test_time": "2026-02-21 10:00:00"},
        "test_points": [1e9, 2e9, 3e9]  # 频率点（示例：1GHz, 2GHz, 3GHz）
    }


# 核心分析函数：函数名和输出字典格式严格保持不变
def analyze_s_params(hardware_data, cable_type):
    """
    分析S参数，支持按不同频率点设置不同合格阈值
    函数名、输出字典格式与原 analysis_protocol 完全一致
    """
    s11 = hardware_data["S11"]
    s21 = hardware_data["S21"]
    test_points = hardware_data["test_points"]
    device_info = hardware_data["device_info"]

    if cable_type in FREQ_THRESHOLDS:
        ft = FREQ_THRESHOLDS[cable_type]
        freq_table = ft["freqs"]  # 预设的频率点
        s11_th_table = ft["S11"]  # 对应的S11阈值
        s21_th_table = ft["S21"]  # 对应的S21阈值
    else:
        # 如果线缆类型未定义，使用默认阈值（固定值）
        freq_table = [min(test_points), max(test_points)]  # 虚拟频率范围
        s11_th_table = [-20, -20]
        s21_th_table = [-3,-3]

    # 2. 逐点判断合格/不合格
    s11_qualified = True
    s21_qualified = True
    for idx, freq in enumerate(test_points):
        # 寻找最接近的配置频率点
        s11_th = np.interp(freq, freq_table, s11_th_table)
        s21_th = np.interp(freq, freq_table, s21_th_table)
        if s11[idx] >= s11_th:
            s11_qualified = False
        if s21[idx] <= s21_th:  # 注意：要求 S21 > 阈值
            s21_qualified = False

    overall_qualified = s11_qualified and s21_qualified
    mean_th = MEAN_THRESHOLDS.get(cable_type, DEFAULT_MEAN)
    # 计算一些统计量
    s11_mean = sum(s11) / len(s11) if s11 else 0.0
    s21_mean = sum(s21) / len(s21) if s21 else 0.0

    if overall_qualified:
        if s11_mean < mean_th["s11_mean_good"] and s21_mean > mean_th["s21_mean_good"]:
            status = "性能良好"
        else:
            status = "合格"
        msg = f"{cable_type} {status} (S11均值 {s11_mean:.1f}dB, S21均值 {s21_mean:.1f}dB)"
    else:
        msg = f"{cable_type} 不合格，请检查"

    result = {
            "device_info": device_info,
            "qualified": overall_qualified,
            "message": msg,
            "s11_qualified": s11_qualified,
            "s21_qualified": s21_qualified,
            "s11_data": [test_points, s11],  # 直接传递绘图数据
            "s21_data": [test_points, s21],
            "analysis_detail": {
                "s11_mean": round(s11_mean, 2),
                "s21_mean": round(s21_mean, 2)
            }
        }
    return result

# 主函数（用于测试）
def main():
    # 1. 获取硬件数据
    hardware_data = get_cable_data()

    # 2. 调用分析函数，传入硬件数据和线缆类型
    result = analyze_s_params(hardware_data, "RG316")

    # 3. 打印结果（格式与原代码完全一致）
    print("===== 分析结果 =====")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
