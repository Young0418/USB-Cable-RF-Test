import pyvisa
import time
import random
import math
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hardware.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
TIMEOUT = 10000
POINTS = 1001
FREQ_START = 1e6
FREQ_STOP = 3e9
VISA_ADDR = "TCPIP0::127.0.0.1::5025::SOCKET"
MAX_RETRIES = 3
RETRY_SELAY = 2 #秒

def get_s_params(perform_calibration=False):
    for attempt in range(MAX_RETRIES):
        inst=None
        rm=None
        try:
            logger.info(f"尝试连接仪器 (第 {attempt + 1}/{MAX_RETRIES} 次)")
            rm = pyvisa.ResourceManager('@py')
            inst = rm.open_resource(VISA_ADDR)
            inst.timeout = TIMEOUT
            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.query("FORMAT REAL")
            inst.query(":SENSe:SWEep:POINts {POINTS}")
            # ===== 校准流程（现在不执行，只留注释）=====
            if perform_calibration:
                logger.info("开始执行 SOLT 校准")
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
                logger.info("校准完成")
            model = inst.query("*IDN?").strip()
            logger.info(f"仪器型号: {model}")

            inst.query(":CALCulate1:PARameter:SELect S11")
            raw_s11 = inst.query(":CALCulate1:DATA? FDATA").strip().split(',')
            if len(raw_s11)%2!= 0:
                raise ValueError(f"S11 数据长度异常:{len(raw_s11)}")
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
                logger.debug(f"S11 点数: {len(s11_dB)}")

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
            logger.debug(f"S21 点数: {len(s21_dB)}")
            # 生成频率列表
            if POINTS > 1:
                step = (FREQ_STOP - FREQ_START) / (POINTS - 1)
                freq_list = [FREQ_START + i * step for i in range(POINTS)]
            else:
                freq_list = [FREQ_START]
            #按hardware_protocol格式组装返回字典

            result= {
                "S11": s11_dB,  # 保留S11一维列表
                "S21": s21_dB,  # 保留S21一维列表
                "device_info": {  # 严格按协议：model/cable_type/test_time
                    "model": model,
                    "test_time": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "test_points": freq_list  # 新增：测试点列表
            }
            logger.info("数据获取成功")
            return result
        except pyvisa.Error as e:
            logger.error(f"VISA 错误:{e}")
            if attempt == MAX_RETRIES - 1:
                raise
        except (ValueError, IndexError) as e:
            logger.error(f"数据解析错误: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
        except Exception as e:
            logger.exception("未预期的异常")
            raise
        finally:
            if inst:
                try:
                    inst.close()
                except:
                    pass
            if rm:
                try:
                    rm.close()
                except:
                    pass
        if attempt < MAX_RETRIES - 1:
            logger.info(f"等待 {RETRY_DELAY} 秒后重试")
            time.sleep(RETRY_DELAY)
    # 不应该走到这里
    raise RuntimeError("所有重试均失败")



if __name__ == "__main__":
    test_dict = get_s_params(perform_calibration=False)
    print("S11点数：", len(test_dict["S11"]))
    print("是否符合硬件协议：", all(key in test_dict for key in ["S11", "S21", "device_info", "test_points"]))