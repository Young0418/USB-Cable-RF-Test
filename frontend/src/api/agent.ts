import type { AgentEvent, SessionInfo } from '@/types'

// EventSource 不支持 POST body，因此用 fetch + ReadableStream 手写 SSE 解析。

export interface ChatOptions {
  sessionId?: string | null
  message: string
  onEvent: (event: AgentEvent) => void
  signal?: AbortSignal
}

export async function streamAgentChat(opts: ChatOptions): Promise<void> {
  const resp = await fetch('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: opts.sessionId ?? null, message: opts.message }),
    signal: opts.signal,
  })
  if (!resp.ok) {
    let detail = `请求失败（HTTP ${resp.status}）`
    try {
      const body = await resp.json()
      if (body?.detail) detail = body.detail
    } catch {
      /* 非 JSON 错误体 */
    }
    throw new Error(detail)
  }
  if (!resp.body) throw new Error('浏览器不支持流式响应')

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // 按空行切分 SSE 块
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const chunk = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const line = chunk.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      const payload = line.slice(5).trim()
      if (!payload) continue
      try {
        opts.onEvent(JSON.parse(payload) as AgentEvent)
      } catch {
        /* 忽略无法解析的事件 */
      }
    }
  }
}

export async function fetchSession(sessionId: string): Promise<SessionInfo> {
  const resp = await fetch(`/api/agent/sessions/${sessionId}`)
  if (!resp.ok) throw new Error(`会话不存在（HTTP ${resp.status}）`)
  return resp.json()
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`/api/agent/sessions/${sessionId}`, { method: 'DELETE' })
}
