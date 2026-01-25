<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()
const menuOpen = ref(false)

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="bg-dark-200 border-b border-gray-700">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center space-x-2">
          <span class="text-2xl font-bold text-primary-500">Frames</span>
        </router-link>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center space-x-6">
          <template v-if="authStore.isAuthenticated">
            <router-link to="/capture/frame" class="text-gray-300 hover:text-white transition">
              Capture Frame
            </router-link>
            <router-link to="/capture/wall" class="text-gray-300 hover:text-white transition">
              Capture Wall
            </router-link>
            <router-link to="/gallery" class="text-gray-300 hover:text-white transition">
              Gallery
            </router-link>
            <router-link to="/walls" class="text-gray-300 hover:text-white transition">
              My Walls
            </router-link>
            <button @click="logout" class="btn btn-secondary">
              Logout
            </button>
          </template>
          <template v-else>
            <router-link to="/login" class="text-gray-300 hover:text-white transition">
              Login
            </router-link>
            <router-link to="/register" class="btn btn-primary">
              Get Started
            </router-link>
          </template>
        </div>

        <!-- Mobile menu button -->
        <button @click="toggleMenu" class="md:hidden text-gray-300 p-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="!menuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Mobile Navigation -->
      <div v-if="menuOpen" class="md:hidden pb-4">
        <template v-if="authStore.isAuthenticated">
          <router-link to="/capture/frame" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            Capture Frame
          </router-link>
          <router-link to="/capture/wall" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            Capture Wall
          </router-link>
          <router-link to="/gallery" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            Gallery
          </router-link>
          <router-link to="/walls" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            My Walls
          </router-link>
          <button @click="logout" class="block w-full text-left py-2 text-gray-300 hover:text-white">
            Logout
          </button>
        </template>
        <template v-else>
          <router-link to="/login" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            Login
          </router-link>
          <router-link to="/register" class="block py-2 text-gray-300 hover:text-white" @click="menuOpen = false">
            Register
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>
