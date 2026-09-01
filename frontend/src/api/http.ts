import axios from 'axios'

// 统一 axios 实例：baseURL='/api'，开发态由 vite 代理到 127.0.0.1:8000
const http = axios.create({
  baseURL: '/api',
  timeout: 120_000,
})

// 统一错误信息提取
export function errMsg(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail) return detail
    return error.message
  }
  return String(error)
}

export default http
