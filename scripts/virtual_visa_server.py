"""虚拟矢网服务器（迁移自根目录 "virtual visa.py"）。

修复：默认线缆质量 `cable_quality="bool"`（字符串 bug）-> "good"。
支持命令行指定质量：python scripts/virtual_visa_server.py bad  （good/bad/marginal）

监听 127.0.0.1:5025，模拟思仪3674 的 SCPI 指令，供无硬件时开发调试。
"""
import socket
import random
import math
import os
import sys

# 线缆质量可从命令行或环境变量指定，默认 "good"
CABLE_QUALITY = os.getenv("VIRTUAL_CABLE_QUALITY", "good")
if len(sys.argv) > 1 and sys.argv[1] in ("good", "bad", "marginal"):
    CABLE_QUALITY = sys.argv[1]


def generate_complex_s_data(num_points=1001, freq_start=1e6, freq_stop=3e9, cable_quality=CABLE_QUALITY):
    """生成模拟的复数 S11/S21 数据，支持不同线缆质量。返回 (s11_list, s21_list)。"""
    if num_points <= 1:
        return [], []

    s11_list = []
    s21_list = []
    for i in range(num_points):
        f = freq_start + (freq_stop - freq_start) * i / (num_points - 1)

        if cable_quality == "good":
            # 好线：S11 全频段都很低（<-25dB），S21 衰减很小（>-1dB）
            s11_mag = -35 + 5 * math.sin(2 * math.pi * 2.5 * i / num_points)
            s21_mag = -0.8 + 0.3 * math.cos(2 * math.pi * 1.8 * i / num_points)
        elif cable_quality == "bad":
            # 坏线：在某个频点有大的反射峰，或者整体损耗很大
            resonance_freq = 1.8e9
            s11_mag = -20 + 15 * math.exp(-((f - resonance_freq) / 0.3e9) ** 2)  # 峰值 -5 dB
            s21_mag = -3 - 4 * (f / freq_stop) - 3 * math.exp(-((f - resonance_freq) / 0.3e9) ** 2)
        elif cable_quality == "marginal":
            # 边缘线：接近合格阈值，可能在某些频点刚好超标
            s11_mag = -20 + 4 * math.sin(2 * math.pi * 3.0 * i / num_points)
            s21_mag = -1.5 + 1.0 * math.cos(2 * math.pi * 2.2 * i / num_points)
        else:
            s11_mag = -35
            s21_mag = -1.0

        s11_phase = 2 * math.pi * random.random()
        s21_phase = 2 * math.pi * random.random()

        real_s11 = 10 ** (s11_mag / 20) * math.cos(s11_phase)
        imag_s11 = 10 ** (s11_mag / 20) * math.sin(s11_phase)
        s11_list.append(complex(real_s11, imag_s11))

        real_s21 = 10 ** (s21_mag / 20) * math.cos(s21_phase)
        imag_s21 = 10 ** (s21_mag / 20) * math.sin(s21_phase)
        s21_list.append(complex(real_s21, imag_s21))

    return s11_list, s21_list


# 初始化 TCP 服务器
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 5025))
s.listen(1)
print("虚拟矢网启动成功！固定VISA地址：TCPIP0::127.0.0.1::5025::SOCKET")
print(f"线缆质量模式：{CABLE_QUALITY}")

# 仪器内部状态
instrument_state = {
    "points": 1001,
    "freq_start": 1e6,
    "freq_stop": 3e9,
    "format": "REAL",
    "selected_parameter": "S11",
    "s11_data": None,
    "s21_data": None,
    "cable_quality": CABLE_QUALITY,
}


def refresh_data():
    """根据当前设置重新生成数据。"""
    try:
        s11, s21 = generate_complex_s_data(
            instrument_state["points"],
            instrument_state["freq_start"],
            instrument_state["freq_stop"],
            instrument_state["cable_quality"],
        )
        instrument_state["s11_data"] = s11
        instrument_state["s21_data"] = s21
    except Exception as exc:
        print(f"刷新数据失败: {exc}")
        instrument_state["s11_data"] = []
        instrument_state["s21_data"] = []


refresh_data()

# 主循环
while True:
    conn, addr = s.accept()
    print(f"硬件代码已连接：{addr}")
    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            print(f"收到指令: {data}")
            cmd = data.upper()

            if cmd == "*IDN?":
                conn.send(b"SiYi,3674,Virtual,1.0\r\n")

            elif cmd.startswith(":SENSE:SWEEP:POINTS"):
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        pts = int(parts[1])
                        instrument_state["points"] = pts
                        refresh_data()
                        conn.send(b"OK\r\n")
                    except ValueError:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            elif cmd == ":SENSE:SWEEP:POINTS?":
                conn.send(f"{instrument_state['points']}\r\n".encode())

            elif cmd.startswith(":SENSE:FREQUENCY:START"):
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        freq = float(parts[1])
                        instrument_state["freq_start"] = freq
                        refresh_data()
                        conn.send(b"OK\r\n")
                    except ValueError:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            elif cmd == ":SENSE:FREQUENCY:START?":
                conn.send(f"{instrument_state['freq_start']}\r\n".encode())

            elif cmd.startswith(":SENSE:FREQUENCY:STOP"):
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        freq = float(parts[1])
                        instrument_state["freq_stop"] = freq
                        refresh_data()
                        conn.send(b"OK\r\n")
                    except ValueError:
                        conn.send(b"ERROR\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            elif cmd == ":SENSE:FREQUENCY:STOP?":
                conn.send(f"{instrument_state['freq_stop']}\r\n".encode())

            elif cmd.startswith(":FORMAT"):
                parts = cmd.split()
                if len(parts) == 2 and parts[1] == "REAL":
                    instrument_state["format"] = "REAL"
                    conn.send(b"OK\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            elif cmd.startswith(":CALC") and ":PARAMETER:SELECT" in cmd:
                parts = cmd.split()
                param = parts[-1]
                if param in ["S11", "S21"]:
                    instrument_state["selected_parameter"] = param
                    conn.send(b"OK\r\n")
                else:
                    conn.send(b"ERROR\r\n")

            elif ":CALCULATE" in cmd and ":DATA? FDATA" in cmd:
                if instrument_state["format"] == "REAL":
                    data = (
                        instrument_state["s11_data"]
                        if instrument_state["selected_parameter"] == "S11"
                        else instrument_state["s21_data"]
                    )
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
        except Exception as exc:
            print(f"处理出错: {exc}")
            break
    conn.close()
    print("连接关闭")
