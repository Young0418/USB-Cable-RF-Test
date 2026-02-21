# 1. 导入需要的库：socket是实现电脑内部TCP通信的库，random生成模拟S参数，time暂时没用
import socket
import random
import time

# 2. 定义生成模拟S参数的函数：gen_s_data = generate S data（生成S11/S21数据）
# num=1001是默认测试点数，和真实矢网的测试点数一致，不用改
def gen_s_data(num=1001):
    # 生成S11数据：-25到-5之间的随机数（贴合真实线缆的反射系数，数值越小反射越好），保留2位小数
    s11 = [round(random.uniform(-25, -5), 2) for _ in range(num)]
    # 生成S21数据：-6到0之间的随机数（贴合真实线缆的传输系数，越接近0传输越好），保留2位小数
    s11 = [round(random.uniform(-25, -5), 2) for _ in range(num)]
    s21 = [round(random.uniform(-6, 0), 2) for _ in range(num)]
    # 返回生成的S11/S21数据，供后续指令调用
    return s11, s21

# 3. 初始化TCP通信的socket对象，相当于创建一个“仪器的通信接口”
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 4. 解决端口被占用的问题：每次重启服务器不用等端口释放，新手必加，不用改
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 5. 绑定本地IP+固定端口5025：相当于给“虚拟仪器”分配一个固定的“通信地址”，硬件代码直接连这个地址
s.bind(("127.0.0.1", 5025))
# 6. 让虚拟仪器进入“等待连接状态”：相当于矢网开机后等待电脑连接
s.listen(1)
# 7. 打印启动提示：告诉你虚拟仪器启动成功，硬件代码该用哪个VISA地址
print(f"虚拟矢网启动成功！固定VISA地址：TCPIP0::127.0.0.1::5025::SOCKET")

# 8. 无限循环：让虚拟仪器一直处于工作状态，不会连接一次就关闭
while True:
    # 9. 接收硬件代码的连接请求：conn是通信通道，addr是硬件代码的地址，不用改
    conn, addr = s.accept()
    print(f"硬件代码已连接：{addr}")
    # 10. 内层循环：处理硬件代码发送的所有SCPI指令
    while True:
        # 11. 读取硬件代码发送的指令：解码成字符串，去掉首尾空格/换行
        data = conn.recv(1024).decode().strip()
        # 12. 如果没收到指令（比如硬件代码关闭连接），就退出内层循环
        if not data: break
        # 13. 指令判断：模拟仪器响应SCPI指令，核心部分！
        if data == "*IDN?":  # 如果收到“查询仪器型号”指令
            # 返回模拟的思仪3674型号，和真实仪器的返回格式一致
            conn.send(b"SiYi,3674,Virtual,1.0\r\n")
        elif "CALC:DATA? S11" in data:  # 如果收到“读取S11数据”指令
            s11, _ = gen_s_data()  # 调用生成S参数的函数，取S11
            # 把S11数据转成字符串，用逗号分隔（和真实仪器的返回格式一致），发给硬件代码
            conn.send((",".join(map(str, s11)) + "\r\n").encode())
        elif "CALC:DATA? S21" in data:  # 如果收到“读取S21数据”指令
            _, s21 = gen_s_data()  # 调用生成S参数的函数，取S21
            conn.send((",".join(map(str, s21)) + "\r\n").encode())
        else:  # 收到其他指令（比如设置频率、点数），直接返回“OK”，不用处理
            conn.send(b"OK\r\n")
    # 14. 硬件代码关闭连接后，关闭通信通道
    conn.close()