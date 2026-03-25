<template>
  <div>
    <h1>Загрузить данные</h1>
    <p class="subtitle">Загрузите файл с данными весового контроля для отправки в ФГИС УТКО</p>

    <!-- Выбор объекта -->
    <div v-if="!selectedObject" style="max-width: 520px;">
      <div v-if="loadingObjects" style="color: var(--muted);">Загрузка объектов...</div>
      <div v-else-if="objects.length === 0" class="card" style="text-align: center; color: var(--muted);">
        Нет объектов. Сначала добавьте объект.
      </div>
      <div v-else style="display: grid; gap: 10px;">
        <div
          v-for="obj in objects"
          :key="obj.id"
          class="card"
          style="cursor: pointer; display: flex; align-items: center; justify-content: space-between;"
          @click="selectedObject = obj"
        >
          <div>
            <div class="card-title" style="margin-bottom: 2px;">{{ obj.name }}</div>
            <span
              :class="['badge', obj.subscription_active ? 'badge-success' : 'badge-danger']"
            >
              {{ obj.subscription_active ? 'Активна' : 'Неактивна' }}
            </span>
          </div>
          <span style="color: var(--gold); font-weight: 700;">→</span>
        </div>
      </div>
    </div>

    <!-- Загрузка файла -->
    <div v-else-if="!preview" style="max-width: 520px;">
      <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
        <button class="btn btn-outline btn-sm" @click="selectedObject = null">← Назад</button>
        <span style="font-weight: 600;">{{ selectedObject.name }}</span>
      </div>

      <div
        class="upload-zone"
        :class="{ dragover }"
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="onDrop"
        @click="fileInput?.click()"
      >
        <div class="icon">📎</div>
        <p>Перетащите файл сюда или нажмите для выбора</p>
        <p class="hint">.xlsx, .xls, .json</p>
      </div>
      <input ref="fileInput" type="file" accept=".xlsx,.xls,.json" hidden @change="onFileSelect" />

      <div v-if="uploading" style="margin-top: 16px; color: var(--muted);">Загрузка и парсинг файла...</div>
    </div>

    <!-- Превью -->
    <div v-else-if="!result" style="max-width: 800px;">
      <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
        <button class="btn btn-outline btn-sm" @click="preview = null">← Назад</button>
        <span style="font-weight: 600;">{{ selectedObject!.name }}</span>
      </div>

      <div class="card" style="margin-bottom: 16px;">
        <div style="display: flex; gap: 24px; align-items: center;">
          <div>
            <span style="font-size: 2rem;">✅</span>
          </div>
          <div>
            <div style="font-weight: 700; font-size: 1.1rem; color: var(--navy);">
              {{ preview.record_count }} записей
            </div>
            <div v-if="preview.errors.length" style="color: var(--red); font-size: 0.82rem; margin-top: 4px;">
              {{ preview.errors.length }} ошибок
            </div>
          </div>
        </div>
      </div>

      <div v-if="preview.errors.length" class="card" style="margin-bottom: 16px; border-color: var(--red);">
        <div class="card-title" style="color: var(--red);">Ошибки</div>
        <ul style="font-size: 0.8rem; color: var(--muted); padding-left: 20px;">
          <li v-for="(err, i) in preview.errors.slice(0, 10)" :key="i">{{ err }}</li>
          <li v-if="preview.errors.length > 10">...и ещё {{ preview.errors.length - 10 }}</li>
        </ul>
      </div>

      <div v-if="preview.record_count > 0" style="display: flex; gap: 10px;">
        <button class="btn btn-primary" :disabled="confirming" @click="confirm">
          {{ confirming ? 'Отправка...' : `Отправить ${preview.record_count} записей` }}
        </button>
        <button class="btn btn-outline" @click="preview = null">Отмена</button>
      </div>
    </div>

    <!-- Результат -->
    <div v-else style="max-width: 520px;">
      <div class="card" style="text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 12px;">
          {{ result.success ? '🎉' : '❌' }}
        </div>
        <div style="font-weight: 700; font-size: 1.1rem; color: var(--navy); margin-bottom: 8px;">
          {{ result.success ? 'Данные отправлены!' : 'Ошибка отправки' }}
        </div>
        <p style="color: var(--muted); font-size: 0.88rem; margin-bottom: 20px;">
          {{ result.message }}
        </p>
        <button class="btn btn-primary" @click="reset">Загрузить ещё</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listObjects, type ScroogeObject } from '@/api/objects'
import { uploadFile, confirmUpload, type UploadPreview, type ConfirmResult } from '@/api/upload'
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
const loadingObjects = ref(true)
const objects = ref<ScroogeObject[]>([])
const selectedObject = ref<ScroogeObject | null>(null)
const fileInput = ref<HTMLInputElement>()
const dragover = ref(false)
const uploading = ref(false)
const preview = ref<UploadPreview | null>(null)
const confirming = ref(false)
const result = ref<ConfirmResult | null>(null)

async function loadObjects() {
  loadingObjects.value = true
  try {
    const { data } = await listObjects()
    objects.value = data
    if (data.length === 1) {
      selectedObject.value = data[0]
    }
  } finally {
    loadingObjects.value = false
  }
}

async function handleFile(file: File) {
  if (!selectedObject.value) return
  uploading.value = true
  try {
    const { data } = await uploadFile(selectedObject.value.id, file)
    preview.value = data
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка загрузки файла')
  } finally {
    uploading.value = false
  }
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) handleFile(input.files[0])
}

function onDrop(e: DragEvent) {
  dragover.value = false
  if (e.dataTransfer?.files?.[0]) handleFile(e.dataTransfer.files[0])
}

async function confirm() {
  if (!preview.value || !selectedObject.value) return
  confirming.value = true
  try {
    const { data } = await confirmUpload(selectedObject.value.id, preview.value.cache_key)
    result.value = data
  } catch (e: any) {
    const detail = e.response?.data?.detail || 'Ошибка отправки'
    notifications.error(detail)
    result.value = { success: false, message: detail, sent_count: 0 }
  } finally {
    confirming.value = false
  }
}

function reset() {
  preview.value = null
  result.value = null
  selectedObject.value = null
  loadObjects()
}

onMounted(loadObjects)
</script>
