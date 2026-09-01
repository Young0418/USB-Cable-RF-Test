# 变更日志

## 2.1.0 — 2026-09-01 智能体上下文工程（P0）

### 新增
- **会话摘要压缩**：会话消息超上限时，最旧一轮先交给模型压成中文摘要再裁剪，不再直接丢消息（丢失关键信息）
- **死循环检测**：同一 `(tool, args)` 连续调用 3 次即中断并提示，防止工具无限重试
- **token 预算**：累计 usage 超 `AGENT_TOKEN_BUDGET` 后优雅停止（新增 `.env` 配置项）
- `get_thresholds` 工具默认只返回摘要（均值标准 + 阈值范围），完整逐频率数组需 `include_full=true`，减少 token 消耗

### 变更
- `session.trim()` 重写：始终保留 system 头（含摘要），只裁对话消息
- 对齐 DeerFlow 的 `tool_output` / `summarization` / `loop_detection` / `token_budget` 设计（见 [ROADMAP.md](ROADMAP.md) P0）

### 修复
- 结束裁剪（`trim`）不再误删刚生成的会话摘要

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
