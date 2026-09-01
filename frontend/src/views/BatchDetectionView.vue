<template>
  <div>
    <el-card shadow="never" class="mb">
      <div class="toolbar">
        <el-form inline>
          <el-form-item label="线缆类型">
            <el-select v-model="draftType" style="width: 220px">
              <el-option v-for="t in cableTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="长度 (m)">
            <el-input-number v-model="draftLength" :min="0.5" :max="200" :step="0.5" :precision="1" style="width: 160px" />
          </el-form-item>
          <el-form-item>
            <el-button @click="addItem">＋ 添加</el-button>
            <el-button type="primary" :loading="running" :disabled="!items.length" @click="runAll">
              {{ running ? `检测中 ${done}/${items.length}…` : '全部检测' }}
            </el-button>
            <el-button :disabled="!results.length" @click="exportCsv">导出 CSV</el-button>
            <el-button :disabled="!items.length" @click="clearItems">清空列表</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-alert
        title="批量检测为逐条执行：每换一根线缆，点击开始下一项。"
        type="info"
        show-icon
        :closable="false"
      />
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="cableType" label="线缆类型" width="160" />
        <el-table-column prop="length" label="长度 (m)" width="120" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="info">待检测</el-tag>
            <el-tag v-else-if="row.status === 'running'" type="warning">检测中…</el-tag>
            <el-tag v-else-if="row.status === 'pass'" type="success">✓ 合格</el-tag>
            <el-tag v-else-if="row.status === 'fail'" type="danger">✗ 不合格</el-tag>
            <el-tag v-else type="error">失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="S11 / S21 均值" min-width="200">
          <template #default="{ row }">
            <span v-if="row.msg">{{ row.msg }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110">
          <template #default="{ row, $index }">
            <el-button size="small" type="primary" plain :disabled="running || row.status !== 'pending'" @click="runOne($index)">
              检测
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { runDetection } from '@/api/detection'
import { fetchCableTypes } from '@/api/thresholds'

interface BatchItem {
  cableType: string
  length: number
  status: 'pending' | 'running' | 'pass' | 'fail' | 'error'
  msg: string
}

const cableTypes = ref<string[]>([])
const draftType = ref('')
const draftLength = ref(10)
const items = ref<BatchItem[]>([])
const results = ref<BatchItem[]>([])
const running = ref(false)
const done = ref(0)

onMounted(async () => {
  cableTypes.value = await fetchCableTypes()
  if (cableTypes.value.length) draftType.value = cableTypes.value[0]
})

function addItem(): void {
  if (!draftType.value) return
  items.value.push({
    cableType: draftType.value,
    length: draftLength.value,
    status: 'pending',
    msg: '',
  })
}

function clearItems(): void {
  items.value = []
  results.value = []
  done.value = 0
}

async function detectOne(item: BatchItem): Promise<void> {
  item.status = 'running'
  try {
    const r = await runDetection({ cable_type: item.cableType, length: item.length })
    item.status = r.qualified ? 'pass' : 'fail'
    item.msg = `S11 ${r.analysis_detail.s11_mean} dB / S21 ${r.analysis_detail.s21_mean} dB`
  } catch (e) {
    item.status = 'error'
    item.msg = (e as { message?: string }).message ?? String(e)
  }
}

async function runOne(index: number): Promise<void> {
  running.value = true
  try {
    await detectOne(items.value[index])
    results.value = items.value.filter((i) => i.status !== 'pending')
  } finally {
    running.value = false
  }
}

async function runAll(): Promise<void> {
  running.value = true
  done.value = 0
  try {
    for (let i = 0; i < items.value.length; i++) {
      const item = items.value[i]
      if (item.status === 'pending') await detectOne(item)
      done.value = i + 1
    }
    results.value = items.value.filter((i) => i.status !== 'pending')
    ElMessage.success('批量检测完成')
  } catch {
    ElMessage.error('批量检测中断')
  } finally {
    running.value = false
  }
}

function exportCsv(): void {
  const header = ['线缆类型', '长度(m)', '判定', 'S11/S21均值']
  const rows = results.value.map((r) => [r.cableType, r.length, r.status === 'pass' ? '合格' : '不合格', r.msg])
  const csv = '﻿' + [header, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `batch_results_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
</style>
