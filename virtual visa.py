# 1. 导入库
import socket
import random
import math
import time

# 2. 定义模拟S参数的生成函数（复数形式）
def generate_complex_s_data(num_points=1001, freq_start=1e6, freq_stop=3e9,cable_quality=""):
    """
    生成模拟的复数S11和S21数据。支持不同种类线缆
    返回格式：两个列表，每个元素是复数(实部, 虚部)
    这里用一个简单的谐振模型模拟频率响应，使数据看起来更真实。
    """
    if num_points <= 1:  # 新增：防止除零
        return [], []  # 返回空列表

    s11_list = []
    s21_list = []
    for i in range(num_points):
        # 模拟频率（等间隔）
        f = freq_start + (freq_stop - freq_start) * i / (num_points - 1)

        # 根据质量调整S11和S21的特性
        if cable_quality == "good":
            # 好线：S11 全频段都很低（<-25dB），S21 衰减很小（>-1dB）
            s11_mag = -35 + 5 * math.sin(2 * math.pi * 2.5 * i / num_points)
            s21_mag = -0.8 + 0.3 * math.cos(2 * math.pi * 1.8 * i / num_points)  # 略微下降
        elif cable_quality == "bad":
            # 坏线：在某个频点有大的反射峰，或者整体损耗很大
            # 模拟一个谐振峰
            resonance_freq = 1.8e9
            # 高斯峰，峰值 -5dB，宽度 0.2GHz
            s11_mag = -15 + 20 * math.exp(-((f - resonance_freq) / 0.2e9) ** 2)
             # S21 整体损耗大，且在谐振频率附近额外衰减
            s21_mag = -3 - 4 * (f / freq_stop) - 5 * math.exp(-((f - resonance_freq) / 0.3e9) ** 2)
        elif cable_quality == "marginal":
            # 边缘线：接近合格阈值，可能在某些频点刚好超标
            s11_mag = -20 + 4 * math.sin(2 * math.pi * 3.0 * i / num_points)  # 振幅4dB，有时高于-20
            # S21 在 -1.5dB 上下波动，部分点低于 -1.5
            s21_mag = -1.5 + 1.0 * math.cos(2 * math.pi * 2.2 * i / num_points)
        else:
            # 默认好线
            s11_mag = -35
            s21_mag = -1.0

        # 添加随机相位（保持一定随机性）
        s11_phase = 2 * math.pi * random.random()
        s21_phase = 2 * math.pi * random.random()

        real_s11 = 10 ** (s11_mag / 20) * math.cos(s11_phase)
        imag_s11 = 10 ** (s11_mag / 20) * math.sin(s11_phase)
        s11_list.append(complex(real_s11, imag_s11))

        real_s21 = 10 ** (s21_mag / 20) * math.cos(s21_phase)
        imag_s21 = 10 ** (s21_mag / 20) * math.sin(s21_phase)
        s21_list.append(complex(real_s21, imag_s21))

    return s11_list, s21_list
# 3. 初始化TCP服务器
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 5025))
s.listen(1)
print("虚拟矢网启动成功！固定VISA地址：TCPIP0::127.0.0.1::5025::SOCKET")

# 4. 仪器内部状态（模拟寄存器）
instrument_state = {
    "points": 1001,               # 默认点数
    "freq_start": 1e6,            # 起始频率
    "freq_stop": 3e9,             # 终止频率
    "format": "REAL",             # 数据返回格式：REAL（实部+虚部）或 ASCii
    "selected_parameter": "S11",
    "s11_data": None,             # 当前生成的S11复数数据
    "s21_data": None,               # 当前生成的S21复数数据
    "cable_quality": "bad",
}

# 5. 辅助函数：刷新数据（当设置改变时重新生成）
def refresh_data():
    try:  # 新增异常捕获
        s11, s21 = generate_complex_s_data(
            instrument_state["points"],
            instrument_state["freq_start"],
            instrument_state["freq_stop"],
            instrument_state["cable_quality"]
        )
        instrument_state["s11_data"] = s11
        instrument_state["s21_data"] = s21
    except Exception as e:
        print(f"刷新数据失败: {e}")  # 打印错误，方便调试
        instrument_state["s11_data"] = []  # 设置为空列表，避免后续遍历 None
        instrument_state["s21_data"] = []
# 初始生成一次数据
refresh_data()

# 6. 主循环
while True:
    conn, addr = s.accept()
    print(f"硬件代码已连接：{addr}")
    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            print(f"收到指令: {data}")

            # 处理命令（忽略大小写和前后空格）
            cmd = data.upper()

            # *IDN? 查询
            if cmd == "*IDN?":
                conn.send(b"SiYi,3674,Virtual,1.0\r\n")

            # 设置点数
            elif cmd.startswith(":SENSE:SWEEP:POINTS"):
                # 格式 :SENSE:SWEEP:POINTS 1001
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        pts = int(parts[1])
                        instrument_state["points"] = pts
                        refresh_data()  # 重新生成数据
                        conn.send(b"OK\r\n")
                    except:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            # 查询点数
            elif cmd == ":SENSE:SWEEP:POINTS?":
                conn.send(f"{instrument_state['points']}\r\n".encode())

            # 设置起始频率
            elif cmd.startswith(":SENSE:FREQUENCY:START"):
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        freq = float(parts[1])
                        instrument_state["freq_start"] = freq
                        refresh_data()
                        conn.send(b"OK\r\n")
                    except:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            # 查询起始频率
            elif cmd == ":SENSE:FREQUENCY:START?":
                conn.send(f"{instrument_state['freq_start']}\r\n".encode())

            # 设置终止频率
            elif cmd.startswith(":SENSE:FREQUENCY:STOP"):
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        freq = float(parts[1])
                        instrument_state["freq_stop"] = freq
                        refresh_data()
                        conn.send(b"OK\r\n")
                    except:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            # 查询终止频率
            elif cmd == ":SENSE:FREQUENCY:STOP?":
                conn.send(f"{instrument_state['freq_stop']}\r\n".encode())

            # 设置数据格式（这里我们只支持REAL，即实部+虚部）
            elif cmd.startswith(":FORMAT"):
                # 假设命令 :FORMAT REAL
                parts = cmd.split()
                if len(parts) == 2 and parts[1] == "REAL":
                    instrument_state["format"] = "REAL"
                    conn.send(b"OK\r\n")
                else:
                    conn.send(b"ERROR\r\n")
            # 选择测量参数
            elif cmd.startswith(":CALC") and ":PARAMETER:SELECT" in cmd:
                # 格式示例 :CALC:PAR:SELect S11
                parts = cmd.split()
                param = parts[-1]  # 最后一个部分是参数名
                if param in ["S11", "S21"]:
                    instrument_state["selected_parameter"] = param
                    conn.send(b"OK\r\n")
                else:
                    conn.send(b"ERROR\r\n")
            # 查询S11数据（返回复数格式）
            elif ":CALCULATE" in cmd and ":DATA? FDATA" in cmd:
                if instrument_state["format"] == "REAL":
                    # 根据当前选择的参数返回数据
                    data = instrument_state["s11_data"] if instrument_state["selected_parameter"] == "S11" else \
                    instrument_state["s21_data"]
                    if data is None or not isinstance(data, list):
                        conn.send(b"ERROR\r\n")
                    else:
                        data_list = []
                        for c in data:
                            data_list.append(f"{c.real:.6f}")
                            data_list.append(f"{c.imag:.6f}")
                        response = ",".join(data_list) + "\r\n"
                        conn.send(response.encode())
                else:
                    conn.send(b"ERROR\r\n")

            else:
                conn.send(b"OK\r\n")
        except Exception as e:
            print(f"处理出错: {e}")
            break
    conn.close()
    print("连接关闭")