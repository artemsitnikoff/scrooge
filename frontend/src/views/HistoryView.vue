<template>
  <div>
    <h1>История отправок</h1>
    <p class="subtitle">Все передачи данных в ФГИС УТКО</p>

    <div v-if="loading" style="color: var(--muted);">Загрузка...</div>

    <div v-else-if="items.length === 0" class="card" style="text-align: center; color: var(--muted); max-width: 520px;">
      Отправок пока не было.
    </div>

    <div v-else style="max-width: 900px;">
      <table class="table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Объект</th>
            <th>Файл</th>
            <th>Записей</th>
            <th>Статус</th>
            <th>Источник</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td style="white-space: nowrap;">{{ formatDate(item.created_at) }}</td>
            <td style="font-weight: 600;">{{ item.object_name }}</td>
            <td style="font-size: 0.78rem; color: var(--muted);">{{ item.filename || '—' }}</td>
            <td>{{ item.record_count }}</td>
            <td>
              <span v-if="item.utko_success === true" class="badge badge-success">Успех</span>
              <span v-else-if="item.utko_success === false" class="badge badge-danger">Ошибка</span>
              <span v-else class="badge badge-warning">—</span>
            </td>
            <td>
              <span style="font-size: 0.76rem; color: var(--muted);">
                {{ item.source === 'bot' ? '🤖 Бот' : '🌐 Веб' }}
              </span>
            </td>
            <td>
              <button class="btn btn-outline btn-sm" @click="openDetail(item.id)">
                Подробнее
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка детально -->
    <div v-if="detail" class="modal-overlay" @click.self="detail = null">
      <div class="modal" style="max-width: 800px; max-height: 80vh; overflow-y: auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h2 style="margin-bottom: 0;">{{ detail.object_name }}</h2>
          <button class="btn btn-outline btn-sm" @click="detail = null">✕</button>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
          <div class="card" style="padding: 16px; text-align: center;">
            <div style="font-size: 0.72rem; color: var(--muted); text-transform: uppercase;">Записей</div>
            <div style="font-weight: 800; font-size: 1.3rem; color: var(--navy);">{{ detail.record_count }}</div>
          </div>
          <div class="card" style="padding: 16px; text-align: center;">
            <div style="font-size: 0.72rem; color: var(--muted); text-transform: uppercase;">Статус</div>
            <div style="font-weight: 800; font-size: 1.1rem;">
              <span v-if="detail.utko_success === true" style="color: var(--green);">Успех</span>
              <span v-else style="color: var(--red);">Ошибка</span>
            </div>
          </div>
          <div class="card" style="padding: 16px; text-align: center;">
            <div style="font-size: 0.72rem; color: var(--muted); text-transform: uppercase;">Источник</div>
            <div style="font-weight: 700;">{{ detail.source === 'bot' ? '🤖 Бот' : '🌐 Веб' }}</div>
          </div>
        </div>

        <div style="font-size: 0.82rem; color: var(--muted); margin-bottom: 16px;">
          {{ formatDateFull(detail.created_at) }} · {{ detail.filename || 'без файла' }}
        </div>

        <!-- Ответ УТКО -->
        <div v-if="detail.utko_response" style="margin-bottom: 20px;">
          <button
            class="btn btn-outline btn-sm"
            style="width: 100%; justify-content: center;"
            @click="showResponse = !showResponse"
          >
            {{ showResponse ? '▲ Скрыть ответ ФГИС УТКО' : '▼ Показать ответ ФГИС УТКО' }}
          </button>
          <div
            v-if="showResponse"
            style="margin-top: 10px; background: var(--navy); color: #e5e7eb; border-radius: 10px; padding: 16px; font-family: monospace; font-size: 0.76rem; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto;"
          >{{ detail.utko_response }}</div>
        </div>

        <!-- Таблица записей -->
        <div v-if="detail.records.length > 0" style="overflow-x: auto;">
          <div class="card-title" style="margin-bottom: 10px;">Данные из файла</div>
          <table class="table" style="font-size: 0.74rem;">
            <thead>
              <tr>
                <th>#</th>
                <th>Госномер</th>
                <th>Дата въезда</th>
                <th>Вес въезд</th>
                <th>Вес выезд</th>
                <th>Масса ТКО</th>
                <th>Перевозчик</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(rec, i) in detail.records" :key="i">
                <td style="color: var(--muted);">{{ i + 1 }}</td>
                <td style="font-weight: 600;">{{ rec.registrationNumber || '—' }}</td>
                <td>{{ rec.dateBefore || '—' }}</td>
                <td>{{ rec.weightBefore || '—' }}</td>
                <td>{{ rec.weightAfter || '—' }}</td>
                <td style="font-weight: 600;">{{ rec.garbageWeight || '—' }}</td>
                <td style="font-size: 0.72rem;">{{ rec.companyName || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listHistory, getHistoryDetail, type HistoryItem, type HistoryDetail } from '@/api/history'
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
const loading = ref(true)
const items = ref<HistoryItem[]>([])
const detail = ref<HistoryDetail | null>(null)
const showResponse = ref(false)

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' }) +
    ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function formatDateFull(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function load() {
  loading.value = true
  try {
    const { data } = await listHistory()
    items.value = data
  } finally {
    loading.value = false
  }
}

async function openDetail(id: number) {
  showResponse.value = false
  try {
    const { data } = await getHistoryDetail(id)
    detail.value = data
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка загрузки')
  }
}

onMounted(load)
</script>
