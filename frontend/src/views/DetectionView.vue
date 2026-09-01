<template>
  <div>
    <el-card shadow="never" class="mb">
      <CableSelector :running="store.running" :cable-types="store.cableTypes" @run="onRun" />
      <el-alert
        v-if="store.error"
        :title="store.error"
        type="error"
        show-icon
        :closable="false"
        class="mt"
      />
    </el-card>

    <template v-if="store.result">
      <ResultCard :result="store.result" @download="store.download" class="mb" />

      <el-card shadow="never" class="mb">
        <template #header><span>S 参数曲线（实测 + 阈值虚线）</span></template>
        <SParameterChart
          :freqs="store.result.s11_data[0]"
          :s11="store.result.s11_data[1]"
          :s21="store.result.s21_data[1]"
          :thresholds="store.result.thresholds"
        />
      </el-card>

      <el-card shadow="never">
        <template #header><span>DTF 故障定位曲线</span></template>
        <DtfChart
          :distance="store.result.dtf_data[0]"
          :amp="store.result.dtf_data[1]"
          :cable-length="store.result.length"
        />
      </el-card>
    </template>

    <el-empty v-else-if="!store.running" description="选择线缆类型与长度后开始检测" />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import CableSelector from '@/components/CableSelector.vue'
import ResultCard from '@/components/ResultCard.vue'
import SParameterChart from '@/components/SParameterChart.vue'
import DtfChart from '@/components/DtfChart.vue'
import { useDetectionStore } from '@/stores/detectionStore'

const store = useDetectionStore()

onMounted(() => store.loadCableTypes())

async function onRun(cableType: string, length: number): Promise<void> {
  await store.detect(cableType, length)
}
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.mt {
  margin-top: 12px;
}
</style>
