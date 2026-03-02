import pyvisa
import time
import random
import math

def get_s_params():
    VISA_ADDR = "TCPIP0::127.0.0.1::5025::SOCKET"
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(VISA_ADDR)
    inst.timeout = 10000
    inst.write_termination = '\n'
    inst.read_termination = '\n'

    inst.write("FORMAT REAL")
    inst.write(":SENSe:SWEep:POINts 1001")

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
    raw_s11 = inst.quary("CALC:DATA? S11").strip().split(',')
    #解析为dB值
    s11_dB = []
    for i in (0,len(raw_s11),2):
        real=float(raw_s11[i])
        imag=float(raw_s11[i+1])
        mag=math.sqrt(real*real+imag*imag) #幅度
        #避免取0对数，加极小值
        if mag<=0:
            dB=-200
        else:
            dB=20*math.log10(mag)
            s11_dB.append(dB)

    raw_s21 = inst.quary(f"CALC:DATA? S21").strip().split(',')
    s21_dB = []
    for i in (0,len(raw_s21),2):
        real=float(raw_s21[i])
        imag=float(raw_s21[i+1])
        mag=math.sqrt(real*real+imag*imag)
        if mag<=0:
            dB=-200
        else:
            dB=20*math.log10(mag)
            s21_dB.append(dB)

    inst.close()
    rm.close()

    # 1. 提取测试点列表（和S11长度一致）
    start_freq=CONFIG["测试参数"]["起始频率(Hz)"]
    stop_freq=CONFIG["测试参数"]["终止频率(Hz)"]
    num_points=CONFIG["测试参数"]["点数"]
    freq_list=[]
    if num_points >1:
        step=(stop_freq-start_freq)/(num_points-1)
        for i in range(num_points):
            freq_list.append(start_freq+i*step)
    else:
        freq_list=start_freq
    # 2. 按hardware_protocol格式组装返回字典
    return {
        "S11": s11_dB,  # 保留S11一维列表
        "S21": s21_dB,  # 保留S21一维列表
        "device_info": {  # 严格按协议：model/cable_type/test_time
            "model": CONFIG["仪器信息"],
            "cable_type": CONFIG["线缆信息"]["类型"],
            "test_time": CONFIG["测试环境"]["测试时间"]
        },
        "test_points": freq_list  # 新增：测试点列表
    }

if __name__ == "__main__":
    test_dict = get_s_params()
    print("S11点数：", len(test_dict["S11"]))
    print("是否符合硬件协议：", all(key in test_dict for key in ["S11", "S21", "device_info", "test_points"]))