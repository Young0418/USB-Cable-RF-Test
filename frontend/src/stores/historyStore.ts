import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { HistoryRecord } from '@/types'
import { clearHistory, fetchHistory } from '@/api/history'

export const useHistoryStore = defineStore('history', () => {
  const records = ref<HistoryRecord[]>([])
  const loading = ref(false)
  const error = ref('')

  async function load(limit = 20): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      records.value = await fetchHistory(limit)
    } catch (e) {
      error.value = (e as { message?: string }).message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  async function clear(): Promise<void> {
    await clearHistory()
    records.value = []
  }

  return { records, loading, error, load, clear }
})
