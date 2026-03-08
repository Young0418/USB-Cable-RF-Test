import subprocess
import time
import sys
import os

def run_script(name, command, wait=2):
    print(f"启动 {name}...")
    if sys.platform == "win32":
        # Windows 下新开窗口运行
        subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen(command, shell=True)
    time.sleep(wait)

if __name__ == "__main__":
    # 切换到脚本所在目录（保证相对路径正确）
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    run_script("虚拟仪器", "python virtual visa.py", 2)
    run_script("API", "python api.py", 3)
    run_script("Streamlit", "streamlit run app.py", 0)