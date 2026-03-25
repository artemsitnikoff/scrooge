import api from './client'

export function getAccessKey() {
  return api.get<{ access_key: string | null; masked: string | null }>('/access-key')
}

export function setAccessKey(access_key: string) {
  return api.put<{ access_key: string; masked: string }>('/access-key', { access_key })
}

export function deleteAccessKey() {
  return api.delete('/access-key')
}
