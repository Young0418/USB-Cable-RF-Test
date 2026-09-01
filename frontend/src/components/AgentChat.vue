<template>
  <div class="agent-chat">
    <div ref="listEl" class="chat-list">
      <div v-if="!store.messages.length" class="empty">
        <p>🤖 我是测试助手，可以帮你：</p>
        <ul>
          <li>「测一下 RG316 10 米」 — 执行检测并解读结果</li>
          <li>「上一条检测什么结果」 — 查询历史记录</li>
          <li>「RG316 的合格阈值是多少」 — 查询阈值标准</li>
          <li>「支持哪些线缆类型」 — 列出可选型号</li>
        </ul>
      </div>

      <div
        v-for="(m, i) in store.messages"
        :key="i"
        class="msg"
        :class="m.role === 'user' ? 'msg-user' : m.role === 'system' ? 'msg-tool' : 'msg-assistant'"
      >
        <template v-if="m.role === 'system'">
          <div class="tool-line">
            🔧 <span>{{ toolLabel(m.tool) }}</span>
            <span v-if="m.args && toolArgsText(m.args)" class="tool-args">{{ toolArgsText(m.args) }}</span>
          </div>
        </template>
        <template v-else>
          <div class="bubble" v-html="renderMarkdown(m.content)"></div>
        </template>
      </div>

      <div v-if="store.streaming" class="msg msg-assistant">
        <div class="bubble"><span class="typing">▊</span></div>
      </div>
    </div>

    <div class="input-bar">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        placeholder="输入问题，回车发送…"
        :disabled="store.streaming"
        @keydown.enter.prevent="onSend"
      />
      <div class="actions">
        <el-button type="primary" :loading="store.streaming" :disabled="!input.trim()" @click="onSend">
          发送
        </el-button>
        <el-button :disabled="!store.messages.length" @click="onClear">清空会话</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useAiStore } from '@/stores/aiStore'

const store = useAiStore()
const input = ref('')
const listEl = ref<HTMLElement | null>(null)

// 自动滚到底部
watch(
  () => store.messages.map((m) => m.content).join('|') + String(store.streaming),
  async () => {
    await nextTick()
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  },
)

async function onSend(): Promise<void> {
  const text = input.value
  if (!text.trim() || store.streaming) return
  input.value = ''
  await store.send(text)
}

function onClear(): void {
  store.clear()
}

function toolLabel(tool?: string | null): string {
  switch (tool) {
    case 'run_detection':
      return '正在执行线缆检测…'
    case 'get_history':
      return '正在查询历史记录…'
    case 'get_thresholds':
      return '正在查询阈值标准…'
    case 'get_cable_types':
      return '正在查询线缆类型…'
    default:
      return '调用工具…'
  }
}

function toolArgsText(args?: Record<string, unknown> | null): string {
  if (!args) return ''
  const parts: string[] = []
  if (args.cable_type) parts.push(String(args.cable_type))
  if (args.length) parts.push(`${args.length}m`)
  if (args.limit) parts.push(`limit=${args.limit}`)
  return parts.length ? `(${parts.join(' · ')})` : ''
}

// 极简 markdown 渲染：粗体 / 行内代码 / 表格 / 换行
function renderMarkdown(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  const withBr = escaped.replace(/\n/g, '<br/>')
  return withBr
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}
</script>

<style scoped>
.agent-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
}
.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f2f3f5;
  border-radius: 8px;
}
.empty {
  color: #909399;
  font-size: 14px;
  line-height: 1.8;
}
.empty ul {
  padding-left: 20px;
}
.msg {
  margin-bottom: 12px;
  display: flex;
}
.msg-user {
  justify-content: flex-end;
}
.msg-user .bubble {
  background: #409eff;
  color: #fff;
}
.msg-assistant .bubble {
  background: #fff;
  color: #303133;
}
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.bubble :deep(strong) {
  font-weight: 600;
}
.bubble :deep(code) {
  background: #f0f2f5;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
.tool-line {
  font-size: 12.5px;
  color: #8c8c8c;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 6px;
  padding: 5px 10px;
}
.tool-args {
  margin-left: 8px;
  color: #d48806;
}
.typing {
  animation: blink 1s infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.input-bar {
  margin-top: 12px;
}
.actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
