<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './Sidebar.vue'
import { getAuthConfig } from '@/api/auth'
import { useAuth } from '@/stores/auth'

const auth = useAuth()

onMounted(async () => {
  if (!auth.appVersion) {
    try {
      const { data } = await getAuthConfig()
      auth.appVersion = data.version
    } catch { /* ignore */ }
  }
})
</script>
