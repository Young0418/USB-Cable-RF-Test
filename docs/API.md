# API 文档

- 基础地址：`http://127.0.0.1:8000`（开发态前端经 vite 代理 `/api`，同源访问）
- 交互式文档：启动后访问 `http://127.0.0.1:8000/docs`（Swagger UI）

## 端点一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查（含 AI 配置、硬件可达性） |
| POST | `/api/detection/run` | 运行一次检测 |
| GET | `/api/detection/{id}/pdf` | 下载 PDF 检测报告 |
| GET | `/api/detection/{id}/elabel` | 下载 e-label 二维码 PNG |
| GET | `/api/history` | 历史记录（倒序，`?limit=`） |
| GET | `/api/history/{id}` | 单条历史记录 |
| DELETE | `/api/history` | 清空历史 |
| GET | `/api/cable-types` | 支持的线缆类型列表 |
| GET | `/api/thresholds?cable_type=&length=` | 阈值表（长度自动吸附） |
| POST | `/api/agent/chat` | AI 助手对话（**SSE 流**） |
| GET | `/api/agent/sessions/{id}` | 读取会话消息 |
| DELETE | `/api/agent/sessions/{id}` | 删除会话 |

## POST /api/detection/run

请求：

```json
{ "cable_type": "RG316", "length": 10 }
```

响应（DetectionResult，曲线为「两条并行数组」）：

```json
{
  "id": "bef34c3fb49e",
  "cable_type": "RG316",
  "length": 10.0,
  "qualified": true,
  "message": "RG316(10.0m) 性能良好 (S11均值 -34.4dB, S21均值 -0.8dB)",
  "s11_qualified": true,
  "s21_qualified": true,
  "device_info": { "model": "VIRTUAL-VNA", "test_time": "2026-09-01 20:26:09" },
  "s11_data": [[1e6, ...], [-34.4, ...]],
  "s21_data": [[1e6, ...], [-0.8, ...]],
  "dtf_data": [[0.0, ...], [-33.7, ...]],
  "thresholds": { "length_used": 10.0, "freqs": [...], "S11": [...], "S21": [...] },
  "analysis_detail": { "s11_mean": -34.4, "s21_mean": -0.8 }
}
```

错误：仪器离线返回 `502`。

## POST /api/agent/chat（SSE）

请求：

```json
{ "session_id": "可选，续接多轮对话", "message": "测一下RG316 10米" }
```

响应为 `text/event-stream`，事件序列：

```
data: {"type":"session","session_id":"..."}
data: {"type":"start"}
data: {"type":"tool","tool":"run_detection","args":{"cable_type":"RG316","length":10}}
data: {"type":"text","content":"检测完成，结果如下：…"}   ← 可能多条，前端拼装
data: {"type":"done"}
```

事件类型：

| type | 说明 |
|---|---|
| `session` | 会话 id（前端存 localStorage） |
| `start` | 开始处理 |
| `tool` | 正在调用某工具（UI 显示状态行） |
| `text` | 模型输出片段（分块，打字机效果） |
| `error` | 出错信息 |
| `done` | 结束 |

错误：`DEEPSEEK_API_KEY` 未配置返回 `503`；消息为空返回 `400`。

## 阈值查询（长度吸附）

`GET /api/thresholds?cable_type=RG316&length=12`：

```json
{
  "cable_type": "RG316",
  "length": 12,
  "length_used": 10,
  "supported_lengths": [5, 10, 20],
  "freqs": [...],
  "S11": [...],
  "S21": [...],
  "mean": { "s11_mean_good": -20, "s21_mean_good": -3, "s11_mean_pass": -15, "s21_mean_pass": -5 }
}
```
