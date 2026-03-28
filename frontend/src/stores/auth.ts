import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuth = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userId = ref(Number(localStorage.getItem('user_id')) || 0)
  const accountId = ref(Number(localStorage.getItem('account_id')) || 0)
  const appVersion = ref('')

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(data: {
    access_token: string
    refresh_token: string
    user_id: number
    account_id: number
  }) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    userId.value = data.user_id
    accountId.value = data.account_id
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user_id', String(data.user_id))
    localStorage.setItem('account_id', String(data.account_id))
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    userId.value = 0
    accountId.value = 0
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('account_id')
  }

  return { accessToken, refreshToken, userId, accountId, appVersion, isAuthenticated, setTokens, logout }
})
