# USB 线缆射频测试系统 — 技术演进路线图

> 对标对象：DeerFlow 2.1.0（字节开源 super agent harness，本地仓库 `D:\deer-flow`）
> 目标：以本 USB 项目为主，**按设计迁移** DeerFlow 的成熟组件（非整包抄），逐步把"单 Agent + JSON 存储"升级为"多 Agent + 记忆 + 技能 + 定时 + 多渠道"。
> 文档：架构见 [ARCHITECTURE.md](ARCHITECTURE.md)，API 见 [API.md](API.md)，变更见 [CHANGELOG.md](CHANGELOG.md)。

---

## 一、现状与技术差距

| 能力维度 | USB 项目现状 | DeerFlow 对标 | 差距 |
|---|---|---|---|
| Agent 编排 | [agent.py](backend/agent/agent.py) 单 Agent 顺序循环，`AGENT_MAX_STEPS=6` | `agents/lead_agent` 多 Agent、子任务并行 | 无并行/子任务 |
| 工具 | [tools.py](backend/agent/tools.py) 4 个硬编码工具 | `skills/` + `tool_search` 技能体系，可热插拔 | 加工具要改代码 |
| 记忆 | [session.py](backend/agent/session.py) 仅会话内 40 条，硬裁剪 | `memory` 跨会话 Markdown 事实存储（#4279 增量事实） | 无长期记忆 |
| 上下文工程 | `trim(cap)` 一刀切裁剪 | `summarization` / `tool_output` 截断 / `loop_detection` / `token_budget` | 缺摘要压缩与截断 |
| 工具输出 | `get_thresholds` 把整组频率+阈值数组塞给模型 | `tool_output.max_chars` 限流 | 浪费 token |
| 搜索 | 无 | `community/*`（Serper/Tavily/Jina/InfoQuest） | 无法联网 |
| 定时 | 无 | `backend/app/scheduler` + `scheduled_tasks` | 无自动检测 |
| 渠道 | 仅 Web 前端 | `channels/`（微信/企微/飞书/Telegram/Slack） | 无法在 IM 里问 |
| 持久化 | [history_service.py](backend/services/history_service.py) JSON 上限 100 | `persistence` ORM + 迁移 + checkpoint | 不可查询/统计 |
| 模型 | 硬编码 DeepSeek（[config.py](backend/config.py)） | `models/factory.py` + `credential_loader` 多 Provider | 锁死一家 |
| 可观测 | 无 | Langfuse / LangSmith 追踪 | 调试靠 print |
| 鉴权 | 无 | `authz` 可插拔授权 | 共享裸奔 |
| 配置 | `.env` 平铺 | `config.yaml` + `config_version` + 升级脚本 | 配置无结构 |

---

## 二、迁移原则

1. **按设计迁移，不整包抄**：吸收 DeerFlow 的抽象与流程（记忆事实格式、技能包结构、调度器租约模型），代码按 USB 项目规模精简重写，不引入 LangGraph/Next.js 等重依赖。
2. **渐进可用**：每一阶段独立可交付、可演示，不打断现有检测主流程。
3. **保守基础设施**：能 SQLite/文件解决的不用 Postgres/K8s；优先内网/实验室场景。

---

## 三、路线图（按价值/成本排序）

### P0 — Agent 质量加固（0.5–1 天，纯代码、不动架构）

**现状痛点**：40 条消息直接丢最旧消息；`get_thresholds` 把整组数组喂给模型；同一工具可能被反复调用。

| # | 迁移来源 | 要做的事 | 涉及文件 |
|---|---|---|---|
| 1 | DeerFlow `tool_output.max_chars` | `get_thresholds` 返回改为**摘要**（closest_length + 各频段均值 + mean 标准），完整数组仅在必要时才返回 | [tools.py](backend/agent/tools.py) |
| 2 | DeerFlow `summarization` | `trim()` 改为：超上限时**先把最旧一轮对话交给模型压缩成摘要**再裁，保留 system + 摘要 + 最近消息 | [session.py](backend/agent/session.py) |
| 3 | DeerFlow `loop_detection` | 记录最近 3 次工具调用，检测到同一 `(tool,args)` 重复即中断并提示 | [agent.py](backend/agent/agent.py) |
| 4 | DeerFlow `token_budget` | 每次模型调用后统计 `usage`，累计超预算时优雅停止 | [agent.py](backend/agent/agent.py) |

**验收**：同样问题 token 消耗下降 30%+；超长对话不再丢失关键信息；`get_thresholds` 不再回传 1001 点。

---

### P1 — 长期记忆（1–2 天）

**迁移来源**：DeerFlow `memory`（agent-scoped Markdown 事实存储，#4279「增量 agent-scoped 事实」）。

**设计**：
- 新增 `backend/agent/memory.py`：`FactMemory` 管理 `data/memory/` 下按主题拆分的 Markdown 事实文件（如 `常用线缆.md`、`检测结论.md`、`用户偏好.md`）。
- 事实条目：`- [时间] 主题: 摘要` 追加式写入；与现检测无关的历史只保留主题+结论，不存原始曲线。
- 注入方式：每次 Agent 会话开始时把相关事实拼进 `SYSTEM_PROMPT`；会话中检测完成时自动沉淀一条事实（「RG316 10m 合格，S11均值 -34dB」）。
- 暴露为工具 `remember_fact(topic, content)`，模型可主动调用。

**验收**：新会话能引用跨会话事实；`data/memory/` 出现可读的 Markdown 文件。

---

### P2 — 联网搜索工具 + 多 Agent 并行（2–4 天）

**迁移来源**：DeerFlow `community/*` 搜索提供方 + `agents/lead_agent` 子任务并行。

1. **搜索工具** `web_search(query)`：接入 Serper/Tavily（DeerFlow 里同名 Provider 的实现可参考，都是单 HTTP 调用），结果摘要化。让 Agent 能回答「这类线缆一般会怎么排查」。
2. **子 Agent 并行**：`run_agent` 扩展为可对「无相互依赖的分析任务」并行（用 `asyncio.gather` 起 2–3 个子 Agent 线程）：
   - 例：「检测 RG316 10m」→ 同时发起 `run_detection`（硬件）+ `get_history`（趋势）+ `web_search`（同类问题）。
   - 保持现 SSE 事件流不变，前端加一个「并行任务」状态行。

**验收**：一句话触发「检测 + 历史趋势 + 联网调研」三路并行，SSE 里依次出现 3 个 `tool` 事件。

---

### P3 — 定时任务（1–2 天）

**迁移来源**：DeerFlow `backend/app/scheduler/service.py`（租约式调度，防多 worker 重复执行）。

**设计**：
- 新增 `backend/services/scheduler.py`：内置 `asyncio` 任务循环，读 `data/scheduled_tasks.json`（任务 = 线缆类型 + 长度 + cron/间隔 + 动作：检测/报告）。
- 动作执行后写入历史，可选自动生成 PDF 报告归档。
- 预留 Webhook/SSE 推送位（与 P4 渠道共用）。

**验收**：配置一条「每 30 分钟测一次 RG316 10m」，日志与历史能看到周期记录。

---

### P4 — IM 渠道（2–3 天，可选但推荐）

**迁移来源**：DeerFlow `channels/`（wecom/feishu/wechat 的 `poll/ack` 轮询模型最易移植，无需 Webhook 公网回调）。

**设计**：
- 新增 `backend/channels/`：实现一个**企微/飞书机器人**，命令映射到检测 API + Agent。
- 消息循环：拉取未读 → 解析「测 RG316 10m」「上一条结果」→ 调 `run_agent`/`detection/run` → 文本回推。
- 与 Web 前端共用同一套 backend 服务，不重复实现逻辑。

**验收**：在企微/飞书群里 @机器人 能触发检测并收到结果文本。

---

### P5 — 技能化（2–3 天，远期）

**迁移来源**：DeerFlow `skills/`（SKILL.md 打包 + `tool_search` 运行时发现）。

**设计**：
- 把 4 个工具按 SKILL.md 结构重新组织：`skills/custom/*/SKILL.md`（元数据 + 描述 + 参数 Schema）+ 同名 Python 执行器。
- Agent 启动/搜索时按需加载技能（`skill_search` 工具扫描 `skills/custom/`），新增检测项 = 加一个目录，**不改 `tools.py`**。
- 复用 DeerFlow `skills/public` 里与检测相关的轻量技能思路（data-analysis / chart-visualization 可启发报告生成）。

**验收**：新增一个「衰减测试」技能目录后，Agent 无需重启即可发现并调用。

---

### P6 — 工程化加固（按需，1–2 天/项）

| # | 迁移来源 | 内容 | 触发条件 |
|---|---|---|---|
| 1 | `models/factory.py` + `credential_loader` | Provider 抽象：`LLMProvider` 接口 + 工厂，支持 DeepSeek/Ollama(本地免费) 切换 | 想省 API 费用 |
| 2 | DeerFlow Langfuse 集成 | 每次 agent 调用埋点（token、耗时、工具轨迹） | 调试复杂 Agent 行为 |
| 3 | `persistence` | `history.json` → SQLite（保留现有 API），支持按类型/时间统计 | 数据量/统计需求上来 |
| 4 | `authz` | 简单登录 + 操作权限 | 部署到共享服务器 |
| 5 | DeerFlow `config.yaml` | `.env` → 分层 `config.yaml` + schema 校验 | 配置项超过 15 个时 |

---

## 四、推荐执行顺序（最小可演示路径）

```
P0（0.5–1 天）→ P1 记忆（1–2 天）→ P2 搜索+并行（2–4 天）→ P3 定时（1–2 天）
                                      ↘ P4 渠道（2–3 天，演示加分）
P5 技能化 / P6 加固：有余力再做
```

按这个顺序，两周内即可从「单 Agent 问答」演进到「检测 + 趋势 + 联网 + 定时 + 多渠道」的完整演示，且每一阶段都独立可用、不回退主流程。

---

## 五、风险与边界

- **不引入重依赖**：全程只用 `asyncio` + 标准库 + 现有 FastAPI，不引 LangGraph/Next.js/Postgres（除非 P6 明确需要）。
- **硬件不可用降级**：所有新增能力（搜索、定时、渠道）都必须与仪器离线时的 502 降级逻辑共存。
- **成本控制**：搜索与多模型会带来 token/API 开销，P0 的 token_budget 是前置项，先做。
- **密钥安全**：新增 Serper/Tavily 等 Key 一律进 `.env`（gitignored），禁止硬编码（沿用已完成的密钥清理纪律）。
