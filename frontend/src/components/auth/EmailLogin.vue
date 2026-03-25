<template>
  <div>
    <template v-if="!codeSent">
      <div class="input-group">
        <label>Email</label>
        <input
          v-model="email"
          type="email"
          class="input"
          placeholder="mail@example.com"
          @keyup.enter="sendCode"
        />
      </div>
      <button class="btn btn-primary" style="width: 100%;" :disabled="loading" @click="sendCode">
        {{ loading ? 'Отправка...' : 'Получить код' }}
      </button>
    </template>
    <template v-else>
      <p style="text-align: center; margin-bottom: 16px; color: var(--muted); font-size: 0.88rem;">
        Код отправлен на <b>{{ email }}</b>
      </p>
      <div class="input-group">
        <label>Код из письма</label>
        <input
          v-model="code"
          type="text"
          class="input"
          placeholder="000000"
          maxlength="6"
          style="text-align: center; font-size: 1.4rem; letter-spacing: 0.3em; font-weight: 700;"
          @keyup.enter="verifyCode"
        />
      </div>
      <button class="btn btn-primary" style="width: 100%;" :disabled="loading" @click="verifyCode">
        {{ loading ? 'Проверка...' : 'Войти' }}
      </button>
      <button
        class="btn btn-outline btn-sm"
        style="width: 100%; margin-top: 10px;"
        @click="codeSent = false"
      >
        Другой email
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { sendOtp, verifyOtp } from '@/api/auth'
import { useAuth } from '@/stores/auth'
import { useNotifications } from '@/stores/notifications'
import { useRouter } from 'vue-router'

const auth = useAuth()
const notifications = useNotifications()
const router = useRouter()

const email = ref('')
const code = ref('')
const codeSent = ref(false)
const loading = ref(false)

async function sendCode() {
  if (!email.value) return
  loading.value = true
  try {
    await sendOtp(email.value)
    codeSent.value = true
    notifications.success('Код отправлен на почту')
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка отправки кода')
  } finally {
    loading.value = false
  }
}

async function verifyCode() {
  if (!code.value) return
  loading.value = true
  try {
    const { data } = await verifyOtp(email.value, code.value)
    auth.setTokens(data)
    router.push('/')
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Неверный код')
  } finally {
    loading.value = false
  }
}
</script>
