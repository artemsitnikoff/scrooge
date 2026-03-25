<template>
  <div>
    <h1>Объекты</h1>
    <p class="subtitle">Управление объектами ТКО</p>

    <div style="margin-bottom: 24px;">
      <button class="btn btn-primary btn-sm" @click="showAdd = true">
        + Добавить объект
      </button>
    </div>

    <div v-if="loading" style="color: var(--muted);">Загрузка...</div>

    <div v-else-if="objects.length === 0" class="card" style="text-align: center; color: var(--muted);">
      Объектов пока нет. Добавьте первый объект.
    </div>

    <div v-else style="display: grid; gap: 12px; max-width: 600px;">
      <div v-for="obj in objects" :key="obj.id" class="card" style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <div class="card-title" style="margin-bottom: 4px;">{{ obj.name }}</div>
          <div style="font-size: 0.76rem; color: var(--muted); font-family: monospace;">
            {{ obj.object_id.substring(0, 8) }}...
          </div>
          <span
            :class="['badge', obj.subscription_active ? 'badge-success' : 'badge-warning']"
            style="margin-top: 6px;"
          >
            {{ obj.subscription_active ? 'Подписка активна' : 'Подписка неактивна' }}
          </span>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-outline btn-sm" @click="startRename(obj)" title="Переименовать">✏️</button>
          <button class="btn btn-outline btn-sm" @click="remove(obj)" title="Удалить" style="color: var(--red);">✕</button>
        </div>
      </div>
    </div>

    <!-- Модалка добавления -->
    <div v-if="showAdd" class="modal-overlay" @click.self="showAdd = false">
      <div class="modal">
        <h2>Добавить объект</h2>
        <div class="input-group">
          <label>UUID объекта</label>
          <input v-model="addForm.objectId" class="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
        </div>
        <div class="input-group">
          <label>Название (необязательно)</label>
          <input v-model="addForm.name" class="input" placeholder="Мой полигон" />
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-primary" :disabled="adding" @click="addObject">
            {{ adding ? 'Добавление...' : 'Добавить' }}
          </button>
          <button class="btn btn-outline" @click="showAdd = false">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модалка переименования -->
    <div v-if="renaming" class="modal-overlay" @click.self="renaming = null">
      <div class="modal">
        <h2>Изменить название</h2>
        <div class="input-group">
          <label>Новое название</label>
          <input v-model="renameName" class="input" @keyup.enter="doRename" />
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-primary" @click="doRename">Сохранить</button>
          <button class="btn btn-outline" @click="renaming = null">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listObjects, createObject, renameObject, deleteObject, type ScroogeObject } from '@/api/objects'
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
const loading = ref(true)
const objects = ref<ScroogeObject[]>([])
const showAdd = ref(false)
const adding = ref(false)
const addForm = reactive({ objectId: '', name: '' })
const renaming = ref<ScroogeObject | null>(null)
const renameName = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await listObjects()
    objects.value = data
  } finally {
    loading.value = false
  }
}

async function addObject() {
  if (!addForm.objectId.trim()) return
  adding.value = true
  try {
    await createObject(addForm.objectId.trim(), addForm.name.trim())
    showAdd.value = false
    addForm.objectId = ''
    addForm.name = ''
    notifications.success('Объект добавлен')
    await load()
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка добавления')
  } finally {
    adding.value = false
  }
}

function startRename(obj: ScroogeObject) {
  renaming.value = obj
  renameName.value = obj.name
}

async function doRename() {
  if (!renaming.value || !renameName.value.trim()) return
  try {
    await renameObject(renaming.value.id, renameName.value.trim())
    renaming.value = null
    notifications.success('Название изменено')
    await load()
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка')
  }
}

async function remove(obj: ScroogeObject) {
  if (!confirm(`Удалить объект "${obj.name}"?`)) return
  try {
    await deleteObject(obj.id)
    notifications.success('Объект удалён')
    await load()
  } catch (e: any) {
    notifications.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}

onMounted(load)
</script>
