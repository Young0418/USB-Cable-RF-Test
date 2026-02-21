import pyvisa
import time
import random

def get_s_params():
    VISA_ADDR = "TCPIP0::127.0.0.1::5025::SOCKET"
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(VISA_ADDR)
    inst.timeout = 10000
    inst.write_termination = '\n'
    inst.read_termination = '\n'

    CONFIG={
        "仪器信息": inst.query("*IDN?").strip(),
        "测试环境": {
            "温度(℃)":25,
            "湿度(%RH)":45,
            "测试时间":time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "线缆信息": {
            "编号":"C001",
            "类型":"50Ω射频同轴电缆",
            "接头类型":"USB-A-SMA",
            "适用场景":"实验室常规射频测试",
            "长度(m)":round(random.uniform(1, 5), 2)
        },
        "测试参数": {
            "起始频率(Hz)":1e6,
            "终止频率(Hz)":3e9,
            "点数":1001
        },
    }

    hardware_data = {
        "配置参数":CONFIG,
        "S参数": {
            "S11": list(map(float, inst.query("CALC:DATA? S11").strip().split(','))),
            "S21": list(map(float, inst.query("CALC:DATA? S21").strip().split(',')))
        }
    }

    inst.close()
    rm.close()

    # 1. 提取测试点列表（和S11长度一致）
    test_points = list(range(1, len(hardware_data["S参数"]["S11"])+1))
    # 2. 按hardware_protocol格式组装返回字典
    return {
        "S11": hardware_data["S参数"]["S11"],  # 保留S11一维列表
        "S21": hardware_data["S参数"]["S21"],  # 保留S21一维列表
        "device_info": {  # 严格按协议：model/cable_type/test_time
            "model": hardware_data["配置参数"]["仪器信息"],
            "cable_type": hardware_data["配置参数"]["线缆信息"]["类型"],
            "test_time": hardware_data["配置参数"]["测试环境"]["测试时间"]
        },
        "test_points": test_points  # 新增：测试点列表
    }

if __name__ == "__main__":
    test_dict = get_s_params()
    print("S11点数：", len(test_dict["S11"]))
    print("是否符合硬件协议：", all(key in test_dict for key in ["S11", "S21", "device_info", "test_points"]))