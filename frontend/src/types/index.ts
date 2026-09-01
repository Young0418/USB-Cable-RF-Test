// 与后端 Pydantic schema 对应的 TypeScript 类型

export interface DeviceInfo {
  model: string
  test_time: string
}

export interface AnalysisDetail {
  s11_mean: number
  s21_mean: number
}

export interface ThresholdConfig {
  length_used: number | null
  freqs: number[]
  S11: number[]
  S21: number[]
}

export interface DetectionResult {
  id: string
  cable_type: string
  length: number
  qualified: boolean
  message: string
  s11_qualified: boolean
  s21_qualified: boolean
  device_info: DeviceInfo
  // 曲线为「两条并行数组」：第0项=横轴(freq/distance)，第1项=纵轴(dB)
  s11_data: number[][]
  s21_data: number[][]
  dtf_data: number[][]
  thresholds: ThresholdConfig
  analysis_detail: AnalysisDetail
}

export interface HistoryRecord {
  id: string
  timestamp: string
  cable_type: string
  length: number
  qualified: boolean
  message: string
  result: DetectionResult
}

export interface ThresholdTable {
  cable_type: string
  length: number
  length_used: number | null
  supported_lengths: number[]
  freqs: number[]
  S11: number[]
  S21: number[]
  mean: {
    s11_mean_good: number
    s21_mean_good: number
    s11_mean_pass: number
    s21_mean_pass: number
  }
}

// ---- Agent 事件 ----
export type AgentEventType = 'session' | 'start' | 'tool' | 'text' | 'done' | 'error'

export interface AgentEvent {
  type: AgentEventType
  content?: string | null
  tool?: string | null
  args?: Record<string, unknown> | null
  session_id?: string | null
}

export interface SessionMessage {
  role: string
  content: string
}

export interface SessionInfo {
  session_id: string
  messages: SessionMessage[]
}
