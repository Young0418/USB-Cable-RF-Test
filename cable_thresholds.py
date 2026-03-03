# cable_thresholds.py.py

# 键严格对应需要支持的三种线缆：RG316、RG58、半刚电缆
CABLE_THRESHOLDS = {
    "RG316": {
        # 全点判定阈值（用于 qualified 字段）
        "s11_all_threshold": -20,
        "s21_all_threshold": -3,
        # 均值判定阈值（用于 status 描述）
        "s11_mean_good": -20,
        "s21_mean_good": -3,
        "s11_mean_pass": -15,
        "s21_mean_pass": -5
    },
    "RG58": {
        "s11_all_threshold": -18,
        "s21_all_threshold": -3.5,
        "s11_mean_good": -18,
        "s21_mean_good": -3.5,
        "s11_mean_pass": -12,
        "s21_mean_pass": -6
    },
    "半刚电缆": {
        "s11_all_threshold": -22,
        "s21_all_threshold": -2.5,
        "s11_mean_good": -22,
        "s21_mean_good": -2.5,
        "s11_mean_pass": -16,
        "s21_mean_pass": -4.5
    }
}

# 默认阈值（防止传入未知线缆类型时程序崩溃）
DEFAULT_THRESHOLD = {
    "s11_all_threshold": -15,
    "s21_all_threshold": -5,
    "s11_mean_good": -15,
    "s21_mean_good": -5,
    "s11_mean_pass": -10,
    "s21_mean_pass": -8
}
