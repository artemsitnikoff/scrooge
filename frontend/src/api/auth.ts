import axios from 'axios'

const base = '/api/v2/auth'

export function getAuthConfig() {
  return axios.get<{ bot_username: string; smtp_enabled: boolean; version: string }>(`${base}/config`)
}

export function sendOtp(email: string) {
  return axios.post(`${base}/email/send-otp`, { email })
}

export function verifyOtp(email: string, code: string) {
  return axios.post(`${base}/email/verify-otp`, { email, code })
}

export function telegramLogin(data: Record<string, unknown>) {
  return axios.post(`${base}/telegram`, data)
}
