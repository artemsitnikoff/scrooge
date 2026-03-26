<template>
  <div>
    <div ref="container" style="display: flex; justify-content: center;"></div>
    <p v-if="widgetFailed" style="text-align: center; font-size: 0.78rem; color: var(--muted); margin-top: 8px;">
      Виджет Telegram не загрузился. Отключите блокировщик рекламы или попробуйте другой браузер.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { telegramLogin } from '@/api/auth'
import { useAuth } from '@/stores/auth'
import { useNotifications } from '@/stores/notifications'
import { useRouter } from 'vue-router'

const props = defineProps<{ botUsername: string }>()

const container = ref<HTMLElement>()
const widgetFailed = ref(false)
const auth = useAuth()
const notifications = useNotifications()
const router = useRouter()

// Telegram Login Widget callback
;(window as any).onTelegramAuth = async (user: Record<string, unknown>) => {
  try {
    const { data } = await telegramLogin(user)
    auth.setTokens(data)
    router.push('/')
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка входа через Telegram')
  }
}

onMounted(() => {
  if (!props.botUsername || !container.value) return
  const script = document.createElement('script')
  script.async = true
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', props.botUsername)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '10')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  script.onerror = () => { widgetFailed.value = true }
  container.value.appendChild(script)

  // Если через 5 секунд iframe не появился — значит заблокирован
  setTimeout(() => {
    if (container.value && !container.value.querySelector('iframe')) {
      widgetFailed.value = true
    }
  }, 5000)
})
</script>
