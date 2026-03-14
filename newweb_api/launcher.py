import subprocess
import time
import sys
import os
import requests
import signal
import platform

# 存储子进程
processes = []

def signal_handler(sig, frame):
    """信号处理器，用于优雅关闭"""
    print("\n正在停止所有服务...")
    for process in processes:
        try:
            if process.poll() is None:  # 如果进程还在运行
                process.terminate()
                process.wait(timeout=5)
        except:
            pass
    print("所有服务已停止")
    sys.exit(0)

def test_api_connection():
    """测试API连接"""
    print("🔍 正在测试API连接...")
    max_retries = 10
    
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Web服务连接成功")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"⏳ 等待Web服务启动... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ Web服务连接失败")
                return False
    
    # 测试AI服务
    try:
        response = requests.get("http://localhost:5000/api/test-ai", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ DeepSeek AI连接成功: {result['message']}")
            else:
                print(f"❌ DeepSeek AI连接失败: {result['message']}")
        else:
            print(f"❌ AI服务测试失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ AI服务测试异常: {str(e)}")
    
    return True

def run_script(name, command, wait=2):
    """运行脚本"""
    print(f"🚀 启动 {name}...")
    try:
        if platform.system() == "Windows":
            process = subprocess.Popen(
                command, 
                shell=True, 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac
            process = subprocess.Popen(
                command, 
                shell=True,
                preexec_fn=os.setsid
            )
        
        processes.append(process)
        print(f"✅ {name} 启动成功 (PID: {process.pid})")
        time.sleep(wait)
        return process
    except Exception as e:
        print(f"❌ {name} 启动失败: {e}")
        return None

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    else:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的文件
    required_files = [
        'app.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ 所有必要文件存在")
    
    # 检查可选文件
    optional_files = ['controller.py', 'deepseek_client.py', 'virtual visa.py']
    for file_path in optional_files:
        if os.path.exists(file_path):
            print(f"✅ 可选文件存在: {file_path}")
        else:
            print(f"⚠️  可选文件缺失: {file_path} (将使用模拟数据)")
    
    return True

if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 切换到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 60)
    print("🔬 线缆智能检测系统启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请检查系统环境")
        sys.exit(1)
    
    print(f"\n📋 配置信息:")
    print(f"   API密钥: sk-c286d401dae142318838f0119342b2bd")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   操作系统: {platform.system()}")
    
    print("\n" + "=" * 60)
    
    try:
        # 启动虚拟仪器（如果存在）
        if os.path.exists("virtual visa.py"):
            virtual_visa_process = run_script(
                "虚拟仪器服务", 
                'python "virtual visa.py"', 
                3
            )
        else:
            print("⚠️  virtual visa.py 不存在，跳过虚拟仪器启动")
        
        # 启动Web应用
        web_process = run_script("Web应用服务", "python app.py", 5)
        
        if web_process is None:
            print("❌ Web应用启动失败")
            sys.exit(1)
        
        # 等待服务启动并测试连接
        print("\n⏳ 等待服务完全启动...")
        time.sleep(3)
        
        if test_api_connection():
            print("\n" + "=" * 60)
            print("🎉 系统启动完成!")
            print("=" * 60)
            print("\n📍 访问地址:")
            print("   🌐 Web界面: http://localhost:5000")
            print("   🔧 API测试: http://localhost:5000/api/test-ai")
            print("   📊 健康检查: http://localhost:5000/health")
            
            print("\n💡 使用提示:")
            print("   • 选择线缆类型后点击'开始检测'")
            print("   • 检测完成后可以询问AI分析结果")
            print("   • 点击'历史记录'查看过往检测")
            print("   • 首次使用AI功能可能需要几秒钟初始化")
            
            print("\n⚠️  注意事项:")
            print("   • 请保持网络连接以使用AI功能")
            print("   • 按 Ctrl+C 可以停止所有服务")
            print("   • 如遇问题请检查控制台日志")
            
            print("\n" + "=" * 60)
            
            # 保持运行
            try:
                while True:
                    time.sleep(1)
                    # 检查Web进程是否还在运行
                    if web_process.poll() is not None:
                        print("❌ Web服务意外停止")
                        break
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)
        else:
            print("❌ 服务启动失败")
            signal_handler(signal.SIGINT, None)
    
    except Exception as e:
        print(f"❌ 启动过程中发生错误: {e}")
        signal_handler(signal.SIGINT, None)