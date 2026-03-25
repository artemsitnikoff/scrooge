import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

let nextId = 0

export const useNotifications = defineStore('notifications', () => {
  const toasts = ref<Toast[]>([])

  function show(message: string, type: Toast['type'] = 'info', duration = 4000) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function success(message: string) { show(message, 'success') }
  function error(message: string) { show(message, 'error', 6000) }
  function info(message: string) { show(message, 'info') }

  return { toasts, show, success, error, info }
})
