import http from './http'
import type { ThresholdTable } from '@/types'

export async function fetchCableTypes(): Promise<string[]> {
  const { data } = await http.get<string[]>('/cable-types')
  return data
}

export async function fetchThresholds(cableType: string, length: number): Promise<ThresholdTable> {
  const { data } = await http.get<ThresholdTable>('/thresholds', {
    params: { cable_type: cableType, length },
  })
  return data
}
