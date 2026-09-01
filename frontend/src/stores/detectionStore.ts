import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DetectionResult } from '@/types'
import { downloadResultFile, runDetection } from '@/api/detection'

export const useDetectionStore = defineStore('detection', () => {
  const cableTypes = ref<string[]>([])
  const result = ref<DetectionResult | null>(null)
  const running = ref(false)
  const error = ref('')

  async function loadCableTypes(): Promise<void> {
    if (cableTypes.value.length) return
    const { fetchCableTypes } = await import('@/api/thresholds')
    cableTypes.value = await fetchCableTypes()
  }

  async function detect(cableType: string, length: number): Promise<DetectionResult> {
    running.value = true
    error.value = ''
    try {
      result.value = await runDetection({ cable_type: cableType, length })
      return result.value
    } catch (e) {
      const msg = (e as { message?: string }).message ?? String(e)
      error.value = msg
      throw e
    } finally {
      running.value = false
    }
  }

  async function download(kind: 'pdf' | 'elabel'): Promise<void> {
    if (!result.value) return
    await downloadResultFile(result.value.id, kind)
  }

  return { cableTypes, result, running, error, loadCableTypes, detect, download }
})
