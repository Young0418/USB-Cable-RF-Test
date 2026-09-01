import http from './http'
import type { HistoryRecord } from '@/types'

export async function fetchHistory(limit = 20): Promise<HistoryRecord[]> {
  const { data } = await http.get<{ records: HistoryRecord[] }>('/history', { params: { limit } })
  return data.records
}

export async function clearHistory(): Promise<number> {
  const { data } = await http.delete<{ cleared: number }>('/history')
  return data.cleared
}
