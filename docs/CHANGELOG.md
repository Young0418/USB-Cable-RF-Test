# 变更日志

## 2.0.0 — 2026-09-01 项目重构

### 目录重构
- 根目录并行的 Streamlit 原型与 `newweb_api/`（Flask）合并为单一 FastAPI 后端 `backend/`
- 规范分层：`core`（纯领域）/ `schemas`（Pydantic）/ `services`（持久化+报告）/ `routers`（API）/ `agent`（AI）
- 前端迁移至 `frontend/`（Vue 3 + Vite + TS + Pinia + ECharts + Element Plus）
- 删除死文件：`app_amended`、`protocol/*`、`newweb_api/*`、`VueWithChange.zip`、`.streamlit/`

### 智能体模块（全新）
- 从"单提示词调 API"升级为**带工具调用的完整 Agent**（DeepSeek function calling）
- 4 个工具：`run_detection` / `get_history` / `get_thresholds` / `get_cable_types`
- SSE 流式输出（工具状态 + 分块文本打字机效果），支持多轮会话持久化
- 工具结果摘要化，防止上下文爆炸

### 修复的 Bug
- `hardware_comm.py`：`RETRY_SELAY` 笔误 → `RETRY_DELAY`
- 虚拟矢网脚本：`cable_quality="bool"` 非法枚举 → `"good"`
- 分析模块：长度静默回退默认阈值 → 先吸附到最近档位（12m → 10m）并在结果与 UI 提示

### 环境与安全
- 新增 `.env` / `.env.example`，密钥（DeepSeek API Key）从源码移入环境变量
- `.gitignore` 排除 `.env`、`data/`、`*.log`、`node_modules/`、`dist/`、`*.tsbuildinfo`
- 使用 `git filter-repo` 重写全部 91 个提交：从历史中彻底删除含密钥文件（`.streamlit/`、`newweb_api/`、`VueWithChange.zip`），并全局替换密钥字符串，已强制推送
- ⚠️ 该 Key 曾长期暴露于公开历史，**无论历史是否已清除都必须立即在 DeepSeek 控制台轮换**，新 Key 写入本地 `.env`（gitignored）

### 保留功能（迁移）
- 单次检测：S11/S21/DTF 曲线 + 合格判定 + 阈值虚线
- PDF 检测报告（reportlab）、e-label 二维码标签（qrcode）
- 批量检测 + CSV 导出（前端逐条执行，保留操作者换线语义）
- 历史记录持久化（`data/history.json`，上限 100 条）
- 多轮 AI 对话（无次数上限）

## 1.x — 旧版本（Streamlit / Flask 原型）
见 Git 历史。
