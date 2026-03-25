import api from './client'

export interface ScroogeObject {
  id: number
  name: string
  object_id: string
  expires_at: string | null
  subscription_active: boolean
}

export function listObjects() {
  return api.get<ScroogeObject[]>('/objects')
}

export function createObject(object_id: string, name: string) {
  return api.post<ScroogeObject>('/objects', { object_id, name })
}

export function renameObject(id: number, name: string) {
  return api.patch<ScroogeObject>(`/objects/${id}`, { name })
}

export function deleteObject(id: number) {
  return api.delete(`/objects/${id}`)
}
