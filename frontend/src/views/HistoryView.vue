<template>
  <div>
    <el-card shadow="never" class="mb">
      <div class="toolbar">
        <span class="count">共 {{ store.records.length }} 条记录</span>
        <el-button size="small" @click="store.load()">刷新</el-button>
        <el-button size="small" type="danger" plain :disabled="!store.records.length" @click="onClear">
          清空历史
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="store.loading" :data="store.records" border stripe>
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="cable_type" label="线缆类型" width="140" />
        <el-table-column prop="length" label="长度 (m)" width="100" />
        <el-table-column label="判定" width="100">
          <template #default="{ row }">
            <el-tag :type="row.qualified ? 'success' : 'danger'">
              {{ row.qualified ? '合格' : '不合格' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="结论" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button size="small" plain @click="downloadPdf(row)">PDF</el-button>
            <el-button size="small" plain type="success" @click="downloadElabel(row)">标签</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { HistoryRecord } from '@/types'
import { downloadResultFile } from '@/api/detection'
import { useHistoryStore } from '@/stores/historyStore'
import { onMounted } from 'vue'

const store = useHistoryStore()

onMounted(() => store.load(50))

async function downloadPdf(row: HistoryRecord): Promise<void> {
  try {
    await downloadResultFile(row.id, 'pdf')
  } catch {
    ElMessage.error('该结果已过期，请重新检测')
  }
}

async function downloadElabel(row: HistoryRecord): Promise<void> {
  try {
    await downloadResultFile(row.id, 'elabel')
  } catch {
    ElMessage.error('该结果已过期，请重新检测')
  }
}

async function onClear(): Promise<void> {
  try {
    await ElMessageBox.confirm('确定清空全部历史记录？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await store.clear()
  ElMessage.success('历史已清空')
}
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.count {
  color: #909399;
}
</style>
