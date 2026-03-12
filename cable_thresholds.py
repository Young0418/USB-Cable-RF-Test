# cable_thresholds.py

# 频率相关阈值配置（用于逐点判断）
# 每个线缆包含三个列表：freqs（频率点，单位Hz）、S11_th（对应阈值，单位dB）、S21_th
FREQ_THRESHOLDS = {
    "RG316": {
        "freqs": [1e9, 2e9, 3e9],
        "S11": [-20.0, -21.0, -22.0],
        "S21": [-1.0, -1.5, -2.0]
    },
    "RG58": {
        "freqs": [1e9, 2e9, 3e9],
        "S11": [-18.0, -19.0, -20.0],
        "S21": [-2.0, -2.5, -3.0]
    },
    "半刚电缆": {
        "freqs": [1e9, 2e9, 3e9],
        "S11": [-25.0, -26.0, -27.0],
        "S21": [-0.5, -1.0, -1.5]
    }
}

# 均值相关阈值（用于生成 message 中的“性能良好/合格”描述）
MEAN_THRESHOLDS = {
    "RG316": {
        "s11_mean_good": -20,
        "s21_mean_good": -3,
        "s11_mean_pass": -15,
        "s21_mean_pass": -5
    },
    "RG58": {
        "s11_mean_good": -18,
        "s21_mean_good": -3.5,
        "s11_mean_pass": -12,
        "s21_mean_pass": -6
    },
    "半刚电缆": {
        "s11_mean_good": -22,
        "s21_mean_good": -2.5,
        "s11_mean_pass": -16,
        "s21_mean_pass": -4.5
    }
}

# 默认均值阈值（当线缆类型未定义时使用）
DEFAULT_MEAN = {
    "s11_mean_good": -15,
    "s21_mean_good": -5,
    "s11_mean_pass": -10,
    "s21_mean_pass": -8
}