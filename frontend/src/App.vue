<template>
  <div class="toast-container">
    <div
      v-for="toast in notifications.toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
    >
      {{ toast.message }}
    </div>
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { useNotifications } from '@/stores/notifications'

const notifications = useNotifications()
</script>
