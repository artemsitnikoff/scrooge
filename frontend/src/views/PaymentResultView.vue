<template>
  <div style="max-width: 480px; margin: 60px auto; text-align: center;">
    <div class="card">
      <div v-if="checking" style="color: var(--muted);">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">⏳</div>
        Проверяем статус оплаты...
      </div>
      <template v-else>
        <div style="font-size: 3rem; margin-bottom: 12px;">
          {{ paid ? '🎉' : '⚠️' }}
        </div>
        <h2 style="margin-bottom: 8px;">
          {{ paid ? 'Оплата прошла успешно!' : 'Ожидаем подтверждение оплаты' }}
        </h2>
        <p style="color: var(--muted); font-size: 0.88rem; margin-bottom: 24px;">
          {{ paid
            ? 'Подписка активирована. Теперь вы можете загружать данные.'
            : 'Оплата обрабатывается. Подписка будет активирована автоматически.'
          }}
        </p>
        <router-link to="/subscription" class="btn btn-primary">
          К подпискам
        </router-link>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { checkPaymentStatus } from '@/api/subscriptions'

const route = useRoute()
const checking = ref(true)
const paid = ref(false)

onMounted(async () => {
  const paymentId = route.query.payment_id as string
  if (!paymentId) {
    checking.value = false
    return
  }

  // Проверяем статус несколько раз (webhook может прийти с задержкой)
  for (let i = 0; i < 5; i++) {
    try {
      const { data } = await checkPaymentStatus(paymentId)
      if (data.paid) {
        paid.value = true
        break
      }
    } catch {
      // ignore
    }
    if (i < 4) {
      await new Promise(r => setTimeout(r, 2000))
    }
  }
  checking.value = false
})
</script>
