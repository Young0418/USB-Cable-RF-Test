import logging
import math
import os
import random
import time

try:
    import pyvisa
except ImportError:
    pyvisa = None

logger = logging.getLogger(__name__)

VISA_ADDRESS = os.getenv("VISA_ADDRESS", "TCPIP0::127.0.0.1::5025::SOCKET")
VISA_BACKEND = os.getenv("VISA_BACKEND", "@py")
USE_VIRTUAL_VISA = os.getenv("USE_VIRTUAL_VISA", "1") == "1"


def get_s_params(perform_calibration: bool = False):
    """尝试通过PyVISA获取S参数；如失败自动回退到虚拟数据"""
    if pyvisa is None or USE_VIRTUAL_VISA:
        logger.info("使用虚拟PyVISA数据 (pyvisa=%s, virtual=%s)", bool(pyvisa), USE_VIRTUAL_VISA)
        return _generate_virtual_dataset("Virtual-VNA")

    rm = None
    inst = None
    try:
        rm = pyvisa.ResourceManager(VISA_BACKEND)
        inst = rm.open_resource(VISA_ADDRESS)
        inst.timeout = 10000
        inst.write_termination = "\n"
        inst.read_termination = "\n"

        inst.write(":FORMat REAL")
        inst.write(":SENSe:SWEep:POINts 1001")

        if perform_calibration:
            _perform_calibration(inst)

        s11 = _query_sparam(inst, "S11")
        s21 = _query_sparam(inst, "S21")
        points = _build_freq_points(1e6, 3e9, len(s11))
        return {
            "S11": s11,
            "S21": s21,
            "device_info": {
                "model": inst.query("*IDN?").strip(),
                "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "test_points": points,
        }
    except Exception as exc:
        logger.warning("真实VISA获取失败，回退虚拟数据: %s", exc)
        return _generate_virtual_dataset("Fallback-Virtual", str(exc))
    finally:
        try:
            if inst:
                inst.close()
            if rm:
                rm.close()
        except Exception:
            pass


def _perform_calibration(inst):
    logger.info("执行简化校准流程")
    inst.write(":CALCulate1:PARameter:SELect S11")
    inst.write(':CALCulate1:CORRection:TYPE "Full 2 Port SOLT"')
    inst.write(":SENSe1:CORRection:COLLect:ACQuire:SHORt 1")
    inst.write(":SENSe1:CORRection:COLLect:ACQuire:OPEN 1")
    inst.write(":SENSe1:CORRection:COLLect:ACQuire:LOAD 1")
    inst.write(":SENSe1:CORRection:COLLect:ACQuire:THRU 1,2")
    inst.write(":SENSe1:CORRection:COLLect:SAVE")


def _query_sparam(inst, parameter: str):
    inst.write(f":CALCulate1:PARameter:SELect {parameter}")
    raw = inst.query(":CALCulate1:DATA? FDATA").strip().split(",")
    values = []
    for idx in range(0, len(raw), 2):
        real = float(raw[idx])
        imag = float(raw[idx + 1])
        magnitude = math.sqrt(real * real + imag * imag)
        magnitude = max(magnitude, 1e-12)
        values.append(20 * math.log10(magnitude))
    return values


def _build_freq_points(start, stop, count):
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def _generate_virtual_dataset(model: str, reason: str | None = None):
    num_points = 201
    start = 1e9
    stop = 3e9
    freqs = _build_freq_points(start, stop, num_points)
    s11 = []
    s21 = []
    for i in range(num_points):
        frac = i / (num_points - 1)
        s11_val = -25 + 5 * math.sin(frac * math.pi * 4) + random.uniform(-1.5, 1.5)
        s21_val = -1.2 - 1.5 * frac + random.uniform(-0.4, 0.4)
        s11.append(round(s11_val, 2))
        s21.append(round(s21_val, 2))
    return {
        "S11": s11,
        "S21": s21,
        "device_info": {
            "model": f"{model} ({reason or 'virtual'})",
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "test_points": freqs,
    }