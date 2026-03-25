import api from './client'

export interface UploadPreview {
  records: Record<string, unknown>[]
  record_count: number
  errors: string[]
  cache_key: string
}

export interface ConfirmResult {
  success: boolean
  message: string
  sent_count: number
}

export function uploadFile(objectId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  return api.post<UploadPreview>(`/upload/${objectId}`, form)
}

export function confirmUpload(objectId: number, cacheKey: string) {
  return api.post<ConfirmResult>(`/upload/${objectId}/confirm`, { cache_key: cacheKey })
}
