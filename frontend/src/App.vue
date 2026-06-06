<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import { useAuthStore } from './store/auth'

const authStore = useAuthStore()

onMounted(() => {
  if (authStore.token) {
    authStore.fetchUser().catch(() => {})
  }
})
</script>

<template>
  <div class="min-h-screen bg-dark-100 overflow-x-hidden">
    <NavBar />
    <main class="container mx-auto px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.container {
  max-width: 1200px;
}
</style>
