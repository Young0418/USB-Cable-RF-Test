# 数据分析同学必须返回的分析判定字典格式（页面同学只能用这个格式）
analysis_protocol = {
    "device_info": {},  # 来自硬件字典的device_info（必填）
    "qualified": False,  # 整体合格状态（布尔值，必填）
    "message": "",  # 整体描述（文本，必填）
    "s11_qualified": False,  # S11合格状态（布尔值，必填）
    "s21_qualified": False,  # S21合格状态（布尔值，必填）
    "s11_data": [[], []],  # 绘图数据：[测试点列表, S11幅值列表]（必填）
    "s21_data": [[], []],  # 绘图数据：[测试点列表, S21幅值列表]（必填）
    "analysis_detail": {  # 分析详情（可选，比如均值）
        "s11_mean": 0.0,
        "s21_mean": 0.0
    }
}