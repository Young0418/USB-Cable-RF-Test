# 更新日志

## 2026-02-20
- 上传人：杨焕莹
- 上传内容：首次上传全量代码，包含虚拟VISA通信、数据分析、硬件数据获取、主流程、页面展示、数据判定相关文件
- 上传文件清单：virtual_visa.py、data_analysis.py、data_get.py、mainfunction.py、app.py、judge_qual.py

## 2026-02-21
- 修改人：杨焕莹
### 1. 文件重命名 + 内容修改
- 原文件：data_get.py
- 新文件：hardware_comm.py
- 修改内容：
  1. 调整输出字典格式，严格贴合硬件协议（hardware_protocol）要求
  2.  保留核心VISA通信逻辑，仅修改返回数据格式

### 2. 主流程文件修改
- 修改文件：mainfunction.py
- 修改内容：
  1. 重构run函数逻辑：原调用judge_qual.py的判定函数，改为串联硬件模块（hardware_comm.get_s_params）+ 数据分析模块（data_analysis.analyze_s_params）
  2. 统一异常处理逻辑，捕获硬件通信/数据分析异常并封装错误信息
  3. 输出格式对齐分析协议（analysis_protocol），仅作为流程串联层，不新增业务逻辑

### 3. 数据分析文件优化
- 修改文件：data_analysis.py（修正原“data analysis.py”）
- 修改内容：
  1. 删除plot_s_parameters函数（页面层改用streamlit绘图）
  2. 函数入参适配硬件协议字典（hardware_comm返回格式），不再依赖嵌套字典解析
  3. 整合judge_qual.py的所有点判定逻辑（S11/S21阈值判定），替代独立判定文件
  4. 输出格式严格对齐分析协议（analysis_protocol）
  5. 保留核心均值计算逻辑（S11/S21均值）
  6. 函数名标准化为analyze_s_params，提升可读性

### 4. 新增协议定义文件
- 新增文件：hardware_protocol.py、analysis_protocol.py
- 新增目的：定义硬件数据/分析结果的标准字典格式，统一多模块数据交互规范

### 5. 页面展示文件适配
- 修改文件：app.py
- 修改内容：
  1. 设备信息展示字段调整：适配分析协议的device_info（model/cable_type/test_time），删除非协议字段（序列号/校准日期）
  2. 绘图x轴标签改为“测试点”，贴合硬件协议的test_points字段，替代原“频率”标注
  3. 保留所有UI交互逻辑（按钮/弹窗/折叠面板），仅调整数据读取字段

### 6. 冗余文件清理
- 删除文件：judge_qual.py
- 删除原因：判定逻辑已整合至data_analysis.py，保留易造成逻辑冗余，统一分析+判定至数据层
