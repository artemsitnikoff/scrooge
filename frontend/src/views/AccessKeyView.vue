<template>
  <div>
    <h1>Ключ доступа УТКО</h1>
    <p class="subtitle">Глобальный ключ для отправки данных в ФГИС УТКО</p>

    <div class="card" style="max-width: 520px;">
      <div v-if="loading" style="color: var(--muted);">Загрузка...</div>
      <template v-else>
        <div v-if="masked" style="margin-bottom: 20px;">
          <div style="font-size: 0.82rem; color: var(--muted); margin-bottom: 6px;">Текущий ключ</div>
          <div style="font-family: monospace; font-size: 1.1rem; font-weight: 600; color: var(--navy);">
            {{ masked }}
          </div>
        </div>
        <div v-else style="margin-bottom: 20px; color: var(--muted); font-size: 0.88rem;">
          Ключ не установлен
        </div>

        <template v-if="!editing">
          <div style="display: flex; gap: 10px;">
            <button class="btn btn-primary btn-sm" @click="editing = true">
              {{ masked ? 'Изменить ключ' : 'Установить ключ' }}
            </button>
            <button v-if="masked" class="btn btn-danger btn-sm" @click="removeKey">
              Удалить
            </button>
          </div>
        </template>
        <template v-else>
          <div class="input-group">
            <label>Ключ доступа (UUID)</label>
            <input
              v-model="newKey"
              class="input"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              @keyup.enter="saveKey"
            />
          </div>
          <div style="display: flex; gap: 10px;">
            <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveKey">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button class="btn btn-outline btn-sm" @click="editing = false; newKey = ''">
              Отмена
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAccessKey, setAccessKey, deleteAccessKey } from '@/api/accessKey'
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
const loading = ref(true)
const masked = ref<string | null>(null)
const editing = ref(false)
const newKey = ref('')
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await getAccessKey()
    masked.value = data.masked
  } finally {
    loading.value = false
  }
}

async function saveKey() {
  if (!newKey.value.trim()) return
  saving.value = true
  try {
    const { data } = await setAccessKey(newKey.value.trim())
    masked.value = data.masked
    editing.value = false
    newKey.value = ''
    notifications.success('Ключ сохранён')
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function removeKey() {
  try {
    await deleteAccessKey()
    masked.value = null
    notifications.success('Ключ удалён')
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}

onMounted(load)
</script>
