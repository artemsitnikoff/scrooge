<template>
  <aside class="sidebar">
    <div class="sidebar-logo">
      <h2>
        <span style="font-size: 1.4rem;">🦆</span> SCROOGE
      </h2>
      <span>Личный кабинет</span>
    </div>
    <nav class="sidebar-nav">
      <router-link to="/access-key">
        <span class="icon">🔑</span>
        <span>Ключ доступа</span>
      </router-link>
      <router-link to="/objects">
        <span class="icon">🏭</span>
        <span>Объекты</span>
      </router-link>
      <router-link to="/upload">
        <span class="icon">📤</span>
        <span>Загрузить данные</span>
      </router-link>
      <router-link to="/subscription">
        <span class="icon">💳</span>
        <span>Подписка</span>
      </router-link>
      <router-link to="/history">
        <span class="icon">📋</span>
        <span>История</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div style="margin-bottom: 8px; cursor: pointer; color: rgba(255,255,255,0.5);" @click="logout">
        Выйти
      </div>
      <div>SCROOGE v1.5.0</div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useAuth } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuth()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>
