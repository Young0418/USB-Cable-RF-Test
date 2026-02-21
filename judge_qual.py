# judge_qual.py
# 判定函数：根据 S11 和 S21 参数判断线缆是否合格

def judge(cable_dict):
    """
    传入 cable_dict（由 data_get.get_cable_data() 返回），
    返回一个字典，包含合格状态、详细信息等。
    假设 cable_dict 结构为：
    {
        'device_info': {'model':..., 'serial':..., 'cal_date':...},
        's_parameters': {
            'S11': [频率列表, 幅值列表],
            'S21': [频率列表, 幅值列表],
            ...
        }
    }
    """
    # 获取 S 参数数据
    s_params = cable_dict.get('s_parameters', {})
    s11 = s_params.get('S11', [[], []])
    s21 = s_params.get('S21', [[], []])

    # 提取幅值（假设第二个列表是幅值，单位 dB）
    s11_mag = s11[1] if len(s11) > 1 else []
    s21_mag = s21[1] if len(s21) > 1 else []

    # 合格阈值（可根据需要修改）
    S11_THRESHOLD = -20   # S11 必须小于 -20 dB
    S21_THRESHOLD = -3    # S21 必须大于 -3 dB

    # 判断
    s11_qualified = all(m < S11_THRESHOLD for m in s11_mag) if s11_mag else False
    s21_qualified = all(m > S21_THRESHOLD for m in s21_mag) if s21_mag else False
    overall_qualified = s11_qualified and s21_qualified

    # 返回结果字典
    result = {
        'device_info': cable_dict.get('device_info', {}),
        's11_data': s11,
        's21_data': s21,
        's11_qualified': s11_qualified,
        's21_qualified': s21_qualified,
        'qualified': overall_qualified,
        'message': '合格' if overall_qualified else '不合格'
    }
    return result