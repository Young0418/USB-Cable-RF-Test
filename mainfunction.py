# mainfunction.py
# 核心作用：串联硬件+数据分析，返回analysis_protocol格式字典
from hardware_comm import get_s_params
from data_analysis import analyze_s_params

def run():
    try:
        # 1. 调用硬件同学的函数，获取硬件协议字典
        hardware_dict = get_s_params()
        # 2. 调用数据分析同学的函数，获取分析判定协议字典
        analysis_dict = analyze_s_params(hardware_dict)
        # 3. 直接返回（已符合页面要求的analysis_protocol格式）
        return analysis_dict
    except Exception as e:
        raise Exception(f"检测失败：{str(e)}")

if __name__ == "__main__":
    test_result = run()
    print("整体合格状态：", test_result["qualified"])
    print("S11均值：", test_result["analysis_detail"]["s11_mean"])