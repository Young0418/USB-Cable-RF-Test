<template>
  <el-card v-if="result" class="result-card" :class="{ pass: result.qualified, fail: !result.qualified }">
    <template #header>
      <div class="card-header">
        <span>
          检测结果：{{ result.cable_type }}（{{ result.length }}m）
        </span>
        <el-tag :type="result.qualified ? 'success' : 'danger'" size="large">
          {{ result.qualified ? '✓ 合格' : '✗ 不合格' }}
        </el-tag>
      </div>
    </template>

    <el-descriptions :column="2" border size="small">
      <el-descriptions-item label="S11 判定">
        <el-tag :type="result.s11_qualified ? 'success' : 'danger'" size="small">
          {{ result.s11_qualified ? '合格' : '不合格' }}
        </el-tag>
        <span class="ms">均值 {{ result.analysis_detail.s11_mean }} dB</span>
      </el-descriptions-item>
      <el-descriptions-item label="S21 判定">
        <el-tag :type="result.s21_qualified ? 'success' : 'danger'" size="small">
          {{ result.s21_qualified ? '合格' : '不合格' }}
        </el-tag>
        <span class="ms">均值 {{ result.analysis_detail.s21_mean }} dB</span>
      </el-descriptions-item>
      <el-descriptions-item label="所用阈值长度">
        {{ result.thresholds?.length_used ?? '默认' }} m
      </el-descriptions-item>
      <el-descriptions-item label="仪器型号">
        {{ result.device_info?.model || 'N/A' }}
      </el-descriptions-item>
      <el-descriptions-item label="测试时间" :span="2">
        {{ result.device_info?.test_time || 'N/A' }}
      </el-descriptions-item>
      <el-descriptions-item label="结论" :span="2">
        {{ result.message }}
      </el-descriptions-item>
    </el-descriptions>

    <el-row class="mt" justify="end">
      <el-button type="primary" plain @click="$emit('download', 'pdf')">📄 下载 PDF 报告</el-button>
      <el-button type="success" plain @click="$emit('download', 'elabel')">🏷️ 下载 e-label 二维码</el-button>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import type { DetectionResult } from '@/types'

defineProps<{ result: DetectionResult | null }>()
defineEmits<{ (e: 'download', kind: 'pdf' | 'elabel'): void }>()
</script>

<style scoped>
.result-card {
  border-top: 3px solid #67c23a;
}
.result-card.fail {
  border-top-color: #f56c6c;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.ms {
  margin-left: 8px;
  color: #909399;
}
.mt {
  margin-top: 14px;
}
</style>
