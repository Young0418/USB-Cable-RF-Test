import pyvisa
import time
import random
import math

def get_s_params(perform_calibration=False):
    VISA_ADDR = "TCPIP0::127.0.0.1::5025::SOCKET"
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(VISA_ADDR)
    inst.timeout = 10000
    inst.write_termination = '\n'
    inst.read_termination = '\n'
    inst.query("FORMAT REAL")
    inst.query(":SENSe:SWEep:POINts 1001")
    # ===== 校准流程（现在不执行，只留注释）=====
    if perform_calibration:
        print("正在执行SOLT校准...")

        # 1. 确保已选择正确的测量参数
        inst.query(":CALCulate1:PARameter:SELect S11")
        inst.query(':CALCulate1:CORRection:TYPE "Full 2 Port SOLT"')
        # 2. 依次采集校准标准件
        # 3. 依次采集校准标准件
        inst.query(":SENSe1:CORRection:COLLect:ACQuire:SHORt 1")  # 端口1短路
        inst.query(":SENSe1:CORRection:COLLect:ACQuire:OPEN 1")  # 端口1开路
        inst.query(":SENSe1:CORRection:COLLect:ACQuire:LOAD 1")  # 端口1负载
        inst.query(":SENSe1:CORRection:COLLect:ACQuire:THRU 1,2")  # 直通

        # 4. 计算并保存校准数据（误差项会自动应用）
        inst.query(":SENSe1:CORRection:COLLect:SAVE")

        # 5. 可选：检查校准状态（但不用再APPLy）
        # inst.query(":CALCulate1:CORRection:STATe?")  # 应该返回 ON

        print("校准完成！")

    CONFIG={
            "仪器信息": inst.query("*IDN?").strip(),
            "测试环境": {
                "温度(℃)":25,
                "湿度(%RH)":45,
                "测试时间":time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "线缆信息": {
                "编号":"C001",
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
    inst.query(":CALCulate1:PARameter:SELect S11")
    raw_s11 = inst.query(":CALCulate1:DATA? FDATA").strip().split(',')
    #解析为dB值
    s11_dB = []
    for i in range(0,len(raw_s11),2):
        real=float(raw_s11[i])
        imag=float(raw_s11[i+1])
        mag=math.sqrt(real*real+imag*imag) #幅度
        #避免取0对数，加极小值
        if mag<=0:
            dB=-200
        else:
            dB=20*math.log10(mag)
        s11_dB.append(dB)
    inst.query(":CALCulate1:PARameter:SELect S21")
    raw_s21 = inst.query(":CALCulate1:DATA? FDATA").strip().split(',')
    s21_dB = []
    for i in range(0,len(raw_s21),2):
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
        freq_list=[start_freq]
    # 2. 按hardware_protocol格式组装返回字典
    return {
        "S11": s11_dB,  # 保留S11一维列表
        "S21": s21_dB,  # 保留S21一维列表
        "device_info": {  # 严格按协议：model/cable_type/test_time
            "model": CONFIG["仪器信息"],
            "test_time": CONFIG["测试环境"]["测试时间"]
        },
        "test_points": freq_list  # 新增：测试点列表
    }

if __name__ == "__main__":
    test_dict = get_s_params(perform_calibration=False)
    print("S11点数：", len(test_dict["S11"]))
    print("是否符合硬件协议：", all(key in test_dict for key in ["S11", "S21", "device_info", "test_points"]))