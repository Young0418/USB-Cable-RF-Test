"""硬件通信：通过 VISA 与矢量网络分析仪（思仪3674）通信，获取复数 S 参数。

迁移自 hardware_comm.py。修复：RETRY_SELAY 笔误 -> RETRY_DELAY。
地址可通过环境变量配置（USE_VIRTUAL_VISA / VISA_ADDRESS）。
"""
import logging
import math
import os
import time

import pyvisa

logger = logging.getLogger(__name__)

TIMEOUT = 10000
POINTS = 1001
FREQ_START = 1e6
FREQ_STOP = 3e9

# 仪器地址：默认连接本地虚拟矢网；USE_VIRTUAL_VISA=0 时连接真实仪器
USE_VIRTUAL_VISA = os.getenv("USE_VIRTUAL_VISA", "1") != "0"
DEFAULT_VISA_ADDR = "TCPIP0::127.0.0.1::5025::SOCKET" if USE_VIRTUAL_VISA else "TCPIP0::192.168.0.10::5025::SOCKET"
VISA_ADDR = os.getenv("VISA_ADDRESS", DEFAULT_VISA_ADDR)

MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def _to_db(mag):
    """幅度转 dB，避免取 0 对数。"""
    if mag <= 0:
        return -200.0
    return 20 * math.log10(mag)


def _parse_fdata(raw):
    """解析仪器返回的复数串为 dB 列表（每对实部/虚部为一个复数）。"""
    parts = raw.strip().split(',')
    if len(parts) % 2 != 0:
        raise ValueError(f"S 参数数据长度异常: {len(parts)}")
    db_list = []
    for i in range(0, len(parts), 2):
        real = float(parts[i])
        imag = float(parts[i + 1])
        db_list.append(_to_db(math.sqrt(real * real + imag * imag)))
    return db_list


def get_s_params(perform_calibration=False):
    """连接仪器并采集 S11/S21 数据，返回 hardware_protocol 格式字典。"""
    last_error = None
    for attempt in range(MAX_RETRIES):
        inst = None
        rm = None
        try:
            logger.info("尝试连接仪器 (第 %d/%d 次)", attempt + 1, MAX_RETRIES)
            rm = pyvisa.ResourceManager('@py')
            inst = rm.open_resource(VISA_ADDR)
            inst.timeout = TIMEOUT
            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.query("FORMAT REAL")
            inst.query(f":SENSe:SWEep:POINts {POINTS}")

            # ===== 校准流程（当前不执行，保留注释）=====
            if perform_calibration:
                logger.info("开始执行 SOLT 校准")
                inst.query(":CALCulate1:PARameter:SELect S11")
                inst.query(':CALCulate1:CORRection:TYPE "Full 2 Port SOLT"')
                inst.query(":SENSe1:CORRection:COLLect:ACQuire:SHORt 1")  # 端口1短路
                inst.query(":SENSe1:CORRection:COLLect:ACQuire:OPEN 1")   # 端口1开路
                inst.query(":SENSe1:CORRection:COLLect:ACQuire:LOAD 1")   # 端口1负载
                inst.query(":SENSe1:CORRection:COLLect:ACQuire:THRU 1,2") # 直通
                inst.query(":SENSe1:CORRection:COLLect:SAVE")
                logger.info("校准完成")

            model = inst.query("*IDN?").strip()
            logger.info("仪器型号: %s", model)

            inst.query(":CALCulate1:PARameter:SELect S11")
            s11_dB = _parse_fdata(inst.query(":CALCulate1:DATA? FDATA"))
            inst.query(":CALCulate1:PARameter:SELect S21")
            s21_dB = _parse_fdata(inst.query(":CALCulate1:DATA? FDATA"))

            # 生成频率列表
            if POINTS > 1:
                step = (FREQ_STOP - FREQ_START) / (POINTS - 1)
                freq_list = [FREQ_START + i * step for i in range(POINTS)]
            else:
                freq_list = [FREQ_START]

            logger.info("数据获取成功")
            return {
                "S11": s11_dB,
                "S21": s21_dB,
                "device_info": {
                    "model": model,
                    "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "test_points": freq_list,
            }
        except pyvisa.Error as exc:
            last_error = exc
            logger.error("VISA 错误: %s", exc)
        except (ValueError, IndexError) as exc:
            last_error = exc
            logger.error("数据解析错误: %s", exc)
        except Exception as exc:
            last_error = exc
            logger.exception("未预期的异常")
            raise
        finally:
            if inst:
                try:
                    inst.close()
                except Exception:
                    pass
            if rm:
                try:
                    rm.close()
                except Exception:
                    pass
        if attempt < MAX_RETRIES - 1:
            logger.info("等待 %d 秒后重试", RETRY_DELAY)
            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"所有重试均失败：无法连接仪器 {VISA_ADDR} ({last_error})")


if __name__ == "__main__":
    test_dict = get_s_params(perform_calibration=False)
    print("S11点数：", len(test_dict["S11"]))
