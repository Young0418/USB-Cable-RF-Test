<template>
  <div class="cable-selector">
    <el-form inline>
      <el-form-item label="线缆类型">
        <el-select v-model="cableType" placeholder="选择线缆类型" style="width: 240px">
          <el-option v-for="t in cableTypes" :key="t" :label="t" :value="t" />
        </el-select>
      </el-form-item>
      <el-form-item label="长度 (m)">
        <el-input-number v-model="length" :min="0.5" :max="200" :step="0.5" :precision="1" style="width: 180px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="running" :disabled="!cableType" @click="onRun">
          {{ running ? '检测中…' : '开始检测' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useDetectionStore } from '@/stores/detectionStore'

const props = defineProps<{
  running?: boolean
  cableTypes?: string[]
  initialLength?: number
}>()
const emit = defineEmits<{
  (e: 'run', cableType: string, length: number): void
  (e: 'cable-types-load', types: string[]): void
}>()

const cableType = ref('')
const length = ref(props.initialLength ?? 10)

watch(
  () => props.cableTypes,
  (types) => {
    if (types?.length && !types.includes(cableType.value)) {
      cableType.value = types[0]
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (props.cableTypes?.length) return
  const store = useDetectionStore()
  await store.loadCableTypes()
  emit('cable-types-load', store.cableTypes)
  if (store.cableTypes.length) cableType.value = store.cableTypes[0]
})

function onRun(): void {
  if (!cableType.value) return
  emit('run', cableType.value, length.value)
}
</script>
