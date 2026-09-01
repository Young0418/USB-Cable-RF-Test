# 系统架构

USB 线缆射频测试系统 —— 前后端分离架构，FastAPI 后端 + Vue 3 前端。

```
┌─────────────┐    /api (vite 代理)     ┌──────────────────────────────────┐
│  Vue 3 前端  │ ──────────────────────▶ │          FastAPI 后端            │
│  (vite :5173)│  SSE / REST / 下载      │          (:8000)                 │
└─────────────┘                         │                                  │
                                        │  routers/                        │
                                        │   ├ health / detection / history │
                                        │   ├ thresholds / agent           │
                                        │  services/                       │
                                        │   ├ history_service  (history.json)│
                                        │   ├ result_cache     (LRU)        │
                                        │   ├ pdf_report       (reportlab)  │
                                        │   └ elabel           (qrcode)     │
                                        │  agent/                           │
                                        │   ├ tools    (4 个 function)      │
                                        │   ├ session  (会话持久化)          │
                                        │   ├ agent    (工具调用循环)         │
                                        │   └ prompts  (SYSTEM_PROMPT)      │
                                        │  core/                            │
                                        │   ├ thresholds  (阈值表+长度吸附)   │
                                        │   ├ analysis    (判定 + DTF)       │
                                        │   ├ hardware    (VISA 通信)        │
                                        │   └ controller  (编排)             │
                                        └──────────────┬───────────────────┘
                                                       │ TCPIP :5025
                                               ┌───────▼────────┐
                                               │  矢量网络分析仪  │
                                               │ (思仪3674 /    │
                                               │  虚拟矢网脚本)  │
                                               └────────────────┘
                                        AI：DeepSeek function calling
                                        (openai SDK, base_url=https://api.deepseek.com/v1)
```

## 目录说明

| 目录 | 职责 |
|---|---|
| `backend/main.py` | FastAPI 应用工厂 + CORS + 路由注册 + uvicorn 入口 |
| `backend/config.py` | 环境变量配置（python-dotenv 加载根目录 `.env`） |
| `backend/core/` | 纯领域模块（零 FastAPI 依赖），可独立单测 |
| `backend/schemas/` | Pydantic 模型（替代旧 `protocol/*` 死文件） |
| `backend/services/` | 历史持久化 / 结果缓存 / PDF / e-label |
| `backend/agent/` | AI 助手（工具调用 Agent + SSE 流式） |
| `backend/routers/` | 5 组 REST + SSE 端点 |
| `scripts/` | 开发辅助：虚拟矢网服务器、启动脚本 |
| `frontend/` | Vue 3 + Vite + TS + Pinia + ECharts + Element Plus |
| `docs/` | 本文档 + API + 变更日志 |
| `data/` | 运行时数据（`history.json`、`agent_sessions.json`，gitignored） |

## 核心模块设计

### 数据流（单次检测）

```
controller.run(cable_type, length)
  └─ hardware.get_s_params()      # VISA 采集 S11/S21（1001 点）
  └─ analysis.analyze_s_params()  # 长度吸附 → 逐频点阈值判定 → DTF 逆FFT
  └─ routers/detection:run        # 写缓存 + 写历史 → 返回 DetectionResult
```

### 智能体（Agent）设计

基于 DeepSeek function calling 的工具调用循环：

```
前端 SSE  ─▶ POST /api/agent/chat
              └─ run_agent(session, message)   # async generator
                   ├─ yield session / start
                   └─ 循环（最多 AGENT_MAX_STEPS 次）:
                        ├─ 非流式模型调用（to_thread）→ 得 tool_calls
                        ├─ 有 tool_calls → 执行 execute_tool → 回灌 assistant/tool 消息
                        │                 └─ yield tool 事件
                        └─ 无 tool_calls → 分块 yield text 事件
                   └─ yield done
```

- 4 个工具：`run_detection` / `get_history` / `get_thresholds` / `get_cable_types`
- 工具结果以**摘要**返回（不塞 1001 点数组），防止上下文爆炸
- 会话消息数上限 `AGENT_SESSION_CAP=40`，超出自动裁剪
- 模型与工具执行都跑在 `asyncio.to_thread`，不阻塞事件循环
- 密钥缺失时 `/api/agent/chat` 返回 503，前端显示横幅

### 阈值长度吸附

用户输入长度（如 12m）会吸附到最近支持档位（5/10/20m → 10m），
并在结果 `thresholds.length_used` 与前端 UI 中明确提示。

## 关键修复（迁移自旧代码）

| Bug | 说明 |
|---|---|
| `RETRY_SELAY` 笔误 | → `RETRY_DELAY`，硬件重试不再报错 |
| `cable_quality="bool"` | 虚拟矢网返回非法枚举值 → `"good"` |
| 长度静默回退默认阈值 | 分析前先吸附到最近档位，避免错判 |
