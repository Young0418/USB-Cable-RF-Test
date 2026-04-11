import numpy as np
from cable_thresholds import (
    FREQ_THRESHOLDS,
    MEAN_THRESHOLDS,
    DEFAULT_MEAN,
    DEFAULT_FREQ_THRESHOLD
)


def get_cable_data():
    """模拟从硬件获取数据，返回符合 hardware_protocol 格式的字典"""
    return {
        "S11": [-21.1, -22.2, -23.3, -24.4, -25.5],
        "S21": [-1.1, -2.2, -3.1, -4.2, -5.1],
        "device_info": {"model": "思仪3674", "test_time": "2026-02-21 10:00:00"},
        "test_points": [1e9, 2e9, 3e9, 4e9, 5e9]  # 单位：Hz
    }


# ===================== 【新增】DTF 计算函数（只算数据，不画图）=====================
def compute_dtf(freq, s11_db, vf=0.77):
    c = 3e8
    freq = np.array(freq)
    s11_db = np.array(s11_db)
    n = len(freq)
    if n < 2:
        return [], []

    df = freq[1] - freq[0]
    s11_linear = 10 ** (s11_db / 20)
    s11_complex = s11_linear * np.exp(1j * 0.0)
    time_domain = np.fft.ifft(s11_complex)
    distance = np.arange(n) * c / (2 * vf * n * df)
    dtf_db = 20 * np.log10(np.abs(time_domain))

    # 返回：距离数组 + 反射dB数组
    return distance.tolist(), dtf_db.tolist()


# ==================================================================================


# 核心分析函数：函数名和输出字典格式严格保持不变
def analyze_s_params(hardware_data, cable_type, length):
    """
    分析S参数，支持按不同频率点、不同线缆长度设置合格阈值
    函数名、输出字典格式与原 analysis_protocol 完全一致
    """
    s11 = hardware_data["S11"]
    s21 = hardware_data["S21"]
    test_points = hardware_data["test_points"]
    device_info = hardware_data["device_info"]

    # 按线缆类型 + 长度读取阈值
    if cable_type in FREQ_THRESHOLDS and length in FREQ_THRESHOLDS[cable_type]:
        ft = FREQ_THRESHOLDS[cable_type][length]
        freq_table = ft["freqs"]
        s11_th_table = ft["S11"]
        s21_th_table = ft["S21"]
    else:
        # 未定义时使用默认阈值
        ft = DEFAULT_FREQ_THRESHOLD
        freq_table = ft["freqs"]
        s11_th_table = ft["S11"]
        s21_th_table = ft["S21"]

    # 逐点判断合格/不合格
    s11_qualified = True
    s21_qualified = True
    for idx, freq in enumerate(test_points):
        s11_th = np.interp(freq, freq_table, s11_th_table)
        s21_th = np.interp(freq, freq_table, s21_th_table)

        # S11：值要 < 阈值才算合格（反射越小越好）
        if s11[idx] >= s11_th:
            s11_qualified = False

        # S21：值要 > 阈值才算合格（损耗越小越好）
        if s21[idx] <= s21_th:
            s21_qualified = False

    overall_qualified = s11_qualified and s21_qualified
    mean_th = MEAN_THRESHOLDS.get(cable_type, DEFAULT_MEAN)

    # 计算均值
    s11_mean = sum(s11) / len(s11) if len(s11) > 0 else 0.0
    s21_mean = sum(s21) / len(s21) if len(s21) > 0 else 0.0

    # ===================== 【新增】计算 DTF =====================
    distance, dtf_amp = compute_dtf(test_points, s11)

    # 生成状态描述
    if overall_qualified:
        if s11_mean < mean_th["s11_mean_good"] and s21_mean > mean_th["s21_mean_good"]:
            status = "性能良好"
        else:
            status = "合格"
        msg = (f"{cable_type}({length}m) {status} "
               f"(S11均值 {s11_mean:.1f}dB, S21均值 {s21_mean:.1f}dB)")
    else:
        msg = f"{cable_type}({length}m) 不合格，请检查"

    # 严格遵循 analysis_protocol 格式
    result = {
        "device_info": device_info,
        "cable_type": cable_type,
        "qualified": overall_qualified,
        "message": msg,
        "s11_qualified": s11_qualified,
        "s21_qualified": s21_qualified,
        "s11_data": [test_points, s11],
        "s21_data": [test_points, s21],
        "dtf_data": [distance, dtf_amp],  # <--- 【新增】直接返回DTF结果
        "analysis_detail": {
            "s11_mean": round(s11_mean, 2),
            "s21_mean": round(s21_mean, 2)
        }
    }
    return result


def main():
    hardware_data = get_cable_data()
    result = analyze_s_params(hardware_data, "RG316", 10)
    print("===== 分析结果 =====")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
