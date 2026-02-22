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
- `hardware_comm.py`      硬件通信主程序（串口收发、数据读取）
- `data_analysis.py`      数据解析与处理
- `.gitignore`            Git 忽略缓存文件
- `CHANGELOG.md`          项目重要更新记录
- `README.md`             项目说明（本文件）

## 5. 协作简单规则
1. 每次改完代码：简单写一下改了哪一块
2. 重要功能更新：记在 CHANGELOG.md 里
