<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ThresholdConfig } from '@/types'

const props = defineProps<{
  freqs: number[] // Hz
  s11: number[] // dB
  s21: number[] // dB
  thresholds: ThresholdConfig
}>()

const option = computed(() => {
  const ghz = (x: number) => (x / 1e9).toFixed(3)
  // 阈值曲线按实测频率插值（随频率变化，非固定直线）
  const thrS11 = props.thresholds?.freqs?.length
    ? props.freqs.map((f) => interp(f, props.thresholds.freqs, props.thresholds.S11))
    : []
  const thrS21 = props.thresholds?.freqs?.length
    ? props.freqs.map((f) => interp(f, props.thresholds.freqs, props.thresholds.S21))
    : []

  const x = props.freqs.map(ghz)
  return {
    textStyle: { fontSize: 19 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['S11 实测', 'S21 实测', 'S11 阈值', 'S21 阈值'] },
    grid: { left: 60, right: 20, top: 40, bottom: 45 },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 8 }],
    xAxis: { type: 'category', data: x, name: '频率 (GHz)', nameLocation: 'middle', nameGap: 30 },
    yAxis: { type: 'value', name: 'dB' },
    series: [
      {
        name: 'S11 实测',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#5470c6' },
        itemStyle: { color: '#5470c6' },
        data: props.s11,
      },
      {
        name: 'S21 实测',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#91cc75' },
        itemStyle: { color: '#91cc75' },
        data: props.s21,
      },
      {
        name: 'S11 阈值',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 1.2, type: 'dashed', color: '#5470c6', opacity: 0.6 },
        data: thrS11,
      },
      {
        name: 'S21 阈值',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 1.2, type: 'dashed', color: '#91cc75', opacity: 0.6 },
        data: thrS21,
      },
    ],
  }
})

function interp(x: number, xs: number[], ys: number[]): number {
  if (x <= xs[0]) return ys[0]
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1]
  for (let i = 1; i < xs.length; i++) {
    if (x <= xs[i]) {
      const t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
      return ys[i - 1] + t * (ys[i] - ys[i - 1])
    }
  }
  return ys[ys.length - 1]
}
</script>

<style scoped>
.chart {
  height: 320px;
  width: 100%;
}
</style>
