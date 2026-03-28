import api from './client'

export interface HistoryItem {
  id: number
  object_name: string
  filename: string | null
  record_count: number
  error_count: number
  utko_success: boolean | null
  source: string
  created_at: string
}

export interface HistoryDetail {
  id: number
  object_name: string
  filename: string | null
  record_count: number
  error_count: number
  records: Record<string, unknown>[]
  utko_success: boolean | null
  utko_response: string | null
  source: string
  created_at: string
}

export function listHistory(limit = 50, offset = 0) {
  return api.get<HistoryItem[]>('/history', { params: { limit, offset } })
}

export function getHistoryDetail(id: number) {
  return api.get<HistoryDetail>(`/history/${id}`)
}
