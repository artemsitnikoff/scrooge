import axios from 'axios'
import { useAuth } from '@/stores/auth'
import router from '@/router'

const api = axios.create({
  baseURL: '/api/v2',
})

api.interceptors.request.use((config) => {
  const auth = useAuth()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const auth = useAuth()
      // Попробуем обновить токен
      if (auth.refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const resp = await axios.post('/api/v2/auth/refresh', {
            refresh_token: auth.refreshToken,
          })
          auth.setTokens(resp.data)
          error.config.headers.Authorization = `Bearer ${resp.data.access_token}`
          return api(error.config)
        } catch {
          auth.logout()
          router.push({ name: 'login' })
        }
      } else {
        auth.logout()
        router.push({ name: 'login' })
      }
    }
    return Promise.reject(error)
  },
)

export default api
