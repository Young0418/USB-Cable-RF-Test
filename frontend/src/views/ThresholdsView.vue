<template>
  <div>
    <el-card shadow="never" class="mb">
      <el-form inline>
        <el-form-item label="线缆类型">
          <el-select v-model="cableType" placeholder="选择线缆类型" style="width: 240px" @change="onSelect">
            <el-option v-for="t in store.cableTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="长度 (m)">
          <el-select v-model="length" style="width: 160px" @change="onSelect">
            <el-option v-for="l in supportedLengths" :key="l" :label="`${l} m`" :value="l" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert
        v-if="table && table.length_used !== null && table.length_used !== length"
        :title="`长度 ${length}m 自动吸附到最近档位 ${table.length_used}m 判定`"
        type="warning"
        show-icon
        :closable="false"
      />
    </el-card>

    <el-card v-loading="store.loading" shadow="never">
      <template v-if="table">
        <el-descriptions :column="2" border size="small" class="mb">
          <el-descriptions-item label="性能良好标准">
            S11 ≤ {{ table.mean.s11_mean_good }} dB，S21 ≥ {{ table.mean.s21_mean_good }} dB
          </el-descriptions-item>
          <el-descriptions-item label="合格标准">
            S11 ≤ {{ table.mean.s11_mean_pass }} dB，S21 ≥ {{ table.mean.s21_mean_pass }} dB
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="tableRows" border stripe>
          <el-table-column prop="freq" label="频率" width="160">
            <template #default="{ row }">{{ row.freq }} GHz</template>
          </el-table-column>
          <el-table-column label="S11 阈值（≤）">
            <template #default="{ row }">{{ row.S11 }} dB</template>
          </el-table-column>
          <el-table-column label="S21 阈值（≥）">
            <template #default="{ row }">{{ row.S21 }} dB</template>
          </el-table-column>
        </el-table>
      </template>
      <el-empty v-else description="选择线缆类型与长度查看阈值标准" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useThresholdStore } from '@/stores/thresholdStore'

const store = useThresholdStore()
const cableType = ref('')
const length = ref(10)
const supportedLengths = [5, 10, 20]

const table = computed(() => store.tables[`${cableType.value}@${length.value}`] ?? null)
const tableRows = computed(() => {
  if (!table.value) return []
  return table.value.freqs.map((f, i) => ({
    freq: (f / 1e9).toFixed(2),
    S11: table.value.S11[i],
    S21: table.value.S21[i],
  }))
})

onMounted(async () => {
  await store.loadCableTypes()
  if (store.cableTypes.length) {
    cableType.value = store.cableTypes[0]
    await onSelect()
  }
})

async function onSelect(): Promise<void> {
  if (!cableType.value) return
  await store.loadTable(cableType.value, length.value)
}
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
</style>
