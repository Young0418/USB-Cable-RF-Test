# Cable-RF-Test
线缆性能测试系统

## 1. 项目简介
本项目用于线缆的射频信号采集、通信控制与数据解析，
通过 Python 实现硬件通信、数据读取与简单测试逻辑，完成大创项目的硬件通信模块开发。

## 2. 团队分工（3人）
- **杨焕莹**：硬件通信代码开发、Python 串口通信、Git 仓库维护
- **李璟琳**：数据处理与分析
- -**郭宇鑫**：测试逻辑与结果整理

## 3. 技术与环境
- 语言：Python 3.9+
- 主要库：pyvisa,matplotlib,pandas,streamlit
- 开发工具：PyCharm
- 版本管理：GitHub

## 4. 主要文件说明
.
├── hardware/ # 硬件通信模块
│ ├── virtual_visa.py # 虚拟仪器（无硬件时模拟）
│ └── hardware_comm.py # 真实仪器通信
├── analysis/ # 数据分析模块
│ ├── cable_thresholds.py # 线缆阈值配置
│ └── data_analysis_amended.py # 核心分析函数
├── gui/ # 前端界面
│ └── app.py # Streamlit应用
├── api.py/ # API服务（FastAPI）
├── docs/ # 文档
├── CHANGELOG.md # 更新日志
└── README.md

## 5. 功能特点
- 支持多种线缆类型（RG316、RG58、半刚电缆等），阈值可配置。
- 硬件控制：通过SCPI指令与思仪3674通信，获取复数S参数并转换为dB。
- 智能分析：根据线缆类型动态阈值，判断合格/不合格，计算统计量。
- AI增强：调用DeepSeek API生成自然语言分析建议。
- 可视化界面：基于Streamlit，实时显示曲线、结果和AI报告。
## 6.使用说明
1. 配置线缆阈值：编辑 `cable_thresholds.py` 添加或修改线缆参数。
2. 启动虚拟仪器（无真实仪器时）：`python hardware/virtual_visa.py`
3. 启动API服务：`python api.py`
4. 启动前端：`streamlit run app.py`
5. 在浏览器中打开 `http://localhost:8501`，选择线缆类型并开始检测。
