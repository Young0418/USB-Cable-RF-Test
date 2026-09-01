import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AgentEvent } from '@/types'
import { deleteSession, streamAgentChat } from '@/api/agent'

const SESSION_KEY = 'usb_cable_ai_session_id'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  tool?: string | null
  args?: Record<string, unknown> | null
}

function loadSessionId(): string | null {
  try {
    return localStorage.getItem(SESSION_KEY)
  } catch {
    return null
  }
}

export const useAiStore = defineStore('ai', () => {
  const sessionId = ref<string | null>(loadSessionId())
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const error = ref('')

  // 当前正在追加的 assistant 消息（打字机）
  let currentText = ''
  let currentAssistant: ChatMessage | null = null

  function appendTool(event: AgentEvent): void {
    messages.value.push({
      role: 'system',
      content: '',
      tool: event.tool,
      args: event.args,
    })
  }

  function beginAssistant(): void {
    currentText = ''
    currentAssistant = { role: 'assistant', content: '' }
    messages.value.push(currentAssistant)
  }

  function appendText(piece: string): void {
    if (!currentAssistant) beginAssistant()
    currentText += piece
    currentAssistant!.content = currentText
  }

  async function send(text: string): Promise<void> {
    const trimmed = text.trim()
    if (!trimmed || streaming.value) return
    error.value = ''
    messages.value.push({ role: 'user', content: trimmed })
    streaming.value = true
    currentAssistant = null
    currentText = ''

    try {
      await streamAgentChat({
        sessionId: sessionId.value,
        message: trimmed,
        onEvent: (ev) => {
          switch (ev.type) {
            case 'session':
              sessionId.value = ev.session_id ?? null
              if (sessionId.value) localStorage.setItem(SESSION_KEY, sessionId.value)
              break
            case 'tool':
              appendTool(ev)
              break
            case 'text':
              appendText(ev.content ?? '')
              break
            case 'error':
              appendText(`\n\n⚠️ ${ev.content ?? '发生错误'}`)
              break
          }
        },
      })
    } catch (e) {
      error.value = (e as { message?: string }).message ?? String(e)
    } finally {
      streaming.value = false
      currentAssistant = null
    }
  }

  async function clear(): Promise<void> {
    if (sessionId.value) {
      try {
        await deleteSession(sessionId.value)
      } catch {
        /* 忽略清除失败 */
      }
    }
    try {
      localStorage.removeItem(SESSION_KEY)
    } catch {
      /* ignore */
    }
    sessionId.value = null
    messages.value = []
    error.value = ''
  }

  return { sessionId, messages, streaming, error, send, clear }
})
