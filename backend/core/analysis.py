"""S 参数数据分析：阈值判定 + DTF 故障定位（迁移自 data_analysis_amended.py）。

修复：分析前先将长度吸附到最近受支持档位（如 12m → 10m），避免静默退回默认阈值。
"""
import numpy as np

from .thresholds import (
    FREQ_THRESHOLDS,
    MEAN_THRESHOLDS,
    DEFAULT_MEAN,
    DEFAULT_FREQ_THRESHOLD,
    SUPPORTED_LENGTHS,
    get_closest_length,
)


def compute_dtf(freq, s11_db, vf=0.77):
    """逆 FFT 计算故障定位（距离-反射曲线），只算数据不画图。"""
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

    return distance.tolist(), dtf_db.tolist()


def analyze_s_params(hardware_data, cable_type, length):
    """分析 S 参数，按线缆类型 + 最近长度档位逐频率点判定合格，并计算 DTF。

    hardware_data 需包含: S11, S21, test_points, device_info
    返回统一结果字典（analysis_protocol 扩展版，含 thresholds）。
    """
    s11 = hardware_data["S11"]
    s21 = hardware_data["S21"]
    test_points = hardware_data["test_points"]
    device_info = hardware_data["device_info"]

    # 长度吸附到最近档位后读取阈值（12m -> 10m）
    closest_len = get_closest_length(length, SUPPORTED_LENGTHS)
    if cable_type in FREQ_THRESHOLDS and closest_len in FREQ_THRESHOLDS[cable_type]:
        ft = FREQ_THRESHOLDS[cable_type][closest_len]
    else:
        closest_len = None
        ft = DEFAULT_FREQ_THRESHOLD
    freq_table = ft["freqs"]
    s11_th_table = ft["S11"]
    s21_th_table = ft["S21"]

    # 逐点判断合格/不合格
    s11_qualified = True
    s21_qualified = True
    for idx, freq in enumerate(test_points):
        s11_th = float(np.interp(freq, freq_table, s11_th_table))
        s21_th = float(np.interp(freq, freq_table, s21_th_table))

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

    # 计算 DTF
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

    return {
        "device_info": device_info,
        "cable_type": cable_type,
        "length": length,
        "qualified": overall_qualified,
        "message": msg,
        "s11_qualified": s11_qualified,
        "s21_qualified": s21_qualified,
        "s11_data": [test_points, s11],
        "s21_data": [test_points, s21],
        "dtf_data": [distance, dtf_amp],
        "thresholds": {
            "length_used": closest_len,
            "freqs": freq_table,
            "S11": s11_th_table,
            "S21": s21_th_table,
        },
        "analysis_detail": {
            "s11_mean": round(s11_mean, 2),
            "s21_mean": round(s21_mean, 2),
        },
    }
