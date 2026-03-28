<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-text">
        <h1>🦆 <span>SCROOGE</span></h1>
        <p style="color: var(--muted); font-size: 0.82rem; margin-top: 4px;">
          Передача данных в ФГИС УТКО
        </p>
      </div>

      <p class="login-subtitle">Войдите в личный кабинет</p>

      <!-- Email OTP — всегда показываем -->
      <EmailLogin />

      <template v-if="botUsername">
        <div class="divider">или</div>
        <TelegramLogin :bot-username="botUsername" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAuthConfig } from '@/api/auth'
import { useAuth } from '@/stores/auth'
import TelegramLogin from '@/components/auth/TelegramLogin.vue'
import EmailLogin from '@/components/auth/EmailLogin.vue'

const auth = useAuth()
const botUsername = ref('')

onMounted(async () => {
  try {
    const { data } = await getAuthConfig()
    botUsername.value = data.bot_username
    auth.appVersion = data.version
  } catch {
    // config недоступен
  }
})
</script>
