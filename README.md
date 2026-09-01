# USB 线缆射频测试系统

大创项目：基于矢量网络分析仪的 USB 线缆射频性能测试系统。
前后端分离：**FastAPI 后端 + Vue 3 前端 + DeepSeek AI 助手**。

## 功能

- 🔬 **单次检测**：S11/S21 曲线 + 阈值虚线 + DTF 故障定位 + 合格判定
- 📄 **PDF 报告 & e-label 二维码**：一键下载
- 📋 **批量检测**：逐条执行 + CSV 导出
- 🤖 **AI 助手**：DeepSeek function calling 工具调用，支持「测一下 RG316 10 米」「上一条检测结果」等自然语言操作，SSE 流式输出
- 🗂️ **历史记录**：持久化到本地文件
- 📏 **阈值标准**：6 种线缆 × 3 种长度，长度自动吸附最近档位

## 快速开始

### 环境要求
- Python 3.10+，Node.js 18+
- 无真实仪器时用内置虚拟矢网（默认开启）

### 1. 后端

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 配置环境变量（首次必做）
copy .env.example .env        # Windows
cp .env.example .env          # Linux/macOS
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 启动虚拟矢网（无真实仪器时；真实仪器则设 USE_VIRTUAL_VISA=0）
python scripts/virtual_visa_server.py

# 启动后端（:8000）
python -m uvicorn backend.main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

开发态 vite 会把 `/api` 代理到 `127.0.0.1:8000`，无需处理跨域。

## 目录结构

```
├── backend/            # FastAPI 后端
│   ├── main.py         # 应用入口
│   ├── config.py       # 环境变量配置
│   ├── core/           # 阈值 / 分析 / 硬件 / 编排（纯领域）
│   ├── schemas/        # Pydantic 模型
│   ├── services/       # 历史 / 缓存 / PDF / e-label
│   ├── agent/          # AI 助手（工具调用 + SSE）
│   └── routers/        # health / detection / history / thresholds / agent
├── scripts/            # 虚拟矢网、开发启动
├── frontend/           # Vue 3 + Vite + TS
├── docs/               # ARCHITECTURE / API / CHANGELOG
└── data/               # 运行时数据（gitignored）
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)、[docs/API.md](docs/API.md)。

## 配置说明（.env）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | DeepSeek API Key，AI 助手必需 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI 兼容端点 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `USE_VIRTUAL_VISA` | `1` | `1` 连虚拟矢网，`0` 连真实仪器 |
| `VISA_ADDRESS` | `TCPIP0::127.0.0.1::5025::SOCKET` | 仪器地址 |
| `AGENT_MAX_STEPS` | `6` | Agent 单轮最大工具调用步数 |
| `AGENT_SESSION_CAP` | `40` | 会话消息数上限 |
| `HISTORY_LIMIT` | `100` | 历史记录上限 |

## 支持线缆与长度档位

`RG316` `RG58` `半刚电缆` `RG174` `LMR-200` `RG6`，长度档位 `5 / 10 / 20 m`。
输入任意长度会吸附到最近档位判定。

## 团队

杨焕莹 / 李璟琳 / 郭宇鑫
