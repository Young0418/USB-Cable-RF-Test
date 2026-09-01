import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ThresholdTable } from '@/types'
import { fetchCableTypes, fetchThresholds } from '@/api/thresholds'

export const useThresholdStore = defineStore('threshold', () => {
  const cableTypes = ref<string[]>([])
  const tables = ref<Record<string, ThresholdTable>>({})
  const loading = ref(false)
  const error = ref('')

  async function loadCableTypes(): Promise<void> {
    if (cableTypes.value.length) return
    cableTypes.value = await fetchCableTypes()
  }

  async function loadTable(cableType: string, length: number): Promise<ThresholdTable> {
    loading.value = true
    error.value = ''
    try {
      const t = await fetchThresholds(cableType, length)
      tables.value[`${cableType}@${length}`] = t
      return t
    } catch (e) {
      error.value = (e as { message?: string }).message ?? String(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return { cableTypes, tables, loading, error, loadCableTypes, loadTable }
})
