<template>
  <div>
    <h1>Подписка</h1>
    <p class="subtitle">Управление подписками на объекты</p>

    <div v-if="loading" style="color: var(--muted);">Загрузка...</div>

    <div v-else-if="objects.length === 0" class="card" style="text-align: center; color: var(--muted); max-width: 520px;">
      Нет объектов. Сначала добавьте объект.
    </div>

    <div v-else style="max-width: 600px; display: grid; gap: 16px;">
      <div v-for="obj in objects" :key="obj.id" class="card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
          <div>
            <div class="card-title" style="margin-bottom: 4px;">{{ obj.name }}</div>
            <span
              :class="['badge', obj.active ? 'badge-success' : 'badge-danger']"
            >
              {{ obj.active ? `Активна (${obj.days_left} дн.)` : 'Неактивна' }}
            </span>
          </div>
        </div>

        <div v-if="obj.active && obj.expires_at" style="font-size: 0.82rem; color: var(--muted); margin-bottom: 16px;">
          Действует до {{ formatDate(obj.expires_at) }}
        </div>

        <!-- Тарифы -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div
            style="border: 1.5px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; cursor: pointer; transition: all 0.2s;"
            :style="{ borderColor: 'var(--gold)' }"
            @click="pay(obj.id, 'month')"
          >
            <div style="font-weight: 800; font-size: 1.2rem; color: var(--navy);">2 900 &#8381;</div>
            <div style="font-size: 0.78rem; color: var(--muted); margin-top: 4px;">Месяц</div>
          </div>
          <div
            style="border: 1.5px solid var(--gold); border-radius: 12px; padding: 16px; text-align: center; cursor: pointer; background: var(--gold-light); transition: all 0.2s;"
            @click="pay(obj.id, 'year')"
          >
            <div style="font-weight: 800; font-size: 1.2rem; color: var(--navy);">29 000 &#8381;</div>
            <div style="font-size: 0.78rem; color: var(--gold-dark); margin-top: 4px;">
              Год <span style="font-weight: 700;">(экономия 5 800 &#8381;)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listSubscriptions, createPayment, type SubscriptionObject } from '@/api/subscriptions'
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
const loading = ref(true)
const objects = ref<SubscriptionObject[]>([])
const paying = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await listSubscriptions()
    objects.value = data
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

async function pay(objectId: number, plan: string) {
  if (paying.value) return
  paying.value = true
  try {
    const { data } = await createPayment(objectId, plan)
    // Редирект на страницу оплаты ЮKassa
    window.location.href = data.payment_url
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка создания платежа')
  } finally {
    paying.value = false
  }
}

onMounted(load)
</script>
