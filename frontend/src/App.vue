<script setup>
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div class="min-h-screen bg-dark-100">
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
