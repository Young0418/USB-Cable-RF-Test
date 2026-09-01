import http from './http'
import type { DetectionResult } from '@/types'

export interface RunDetectionPayload {
  cable_type: string
  length: number
}

export async function runDetection(payload: RunDetectionPayload): Promise<DetectionResult> {
  const { data } = await http.post<DetectionResult>('/detection/run', payload)
  return data
}

// 下载 PDF / e-label（blob），自动触发浏览器下载
export async function downloadResultFile(resultId: string, kind: 'pdf' | 'elabel'): Promise<void> {
  const { data, headers } = await http.get<Blob>(`/detection/${resultId}/${kind}`, {
    responseType: 'blob',
  })
  const blob = new Blob([data])
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = headers['content-disposition']?.match(/filename="?([^";]+)"?/i)?.[1] ?? `report_${resultId}.${kind === 'pdf' ? 'pdf' : 'png'}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
