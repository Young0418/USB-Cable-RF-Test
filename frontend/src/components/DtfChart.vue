<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  distance: number[] // m
  amp: number[] // dB
  cableLength?: number
}>()

const option = computed(() => {
  const maxDist = props.distance.length ? props.distance[props.distance.length - 1] : 0
  const markLine = props.cableLength && props.cableLength <= maxDist
    ? [{ xAxis: props.cableLength, label: { formatter: `线缆端 ${props.cableLength}m`, position: 'insideEndTop' } }]
    : []
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v.toFixed(2)} dB` },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    dataZoom: [{ type: 'inside' }],
    xAxis: { type: 'value', name: '距离 (m)' },
    yAxis: { type: 'value', name: '反射 (dB)' },
    series: [
      {
        name: 'DTF',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#8c564b' },
        areaStyle: { color: 'rgba(140,86,75,0.15)' },
        data: props.distance.map((d, i) => [d, props.amp[i]]),
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#e02020', type: 'dashed' },
          label: { color: '#e02020' },
          data: markLine,
        },
      },
    ],
  }
})
</script>

<style scoped>
.chart {
  height: 260px;
  width: 100%;
}
</style>
