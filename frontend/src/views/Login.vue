<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  error.value = ''
  loading.value = true

  try {
    await authStore.login(email.value, password.value)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    error.value = err.response?.data?.error || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="card">
      <h1 class="text-2xl font-bold text-center mb-6">Welcome Back</h1>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="error" class="p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm">
          {{ error }}
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="your@email.com"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Password</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="Your password"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="btn btn-primary w-full py-3"
        >
          <span v-if="loading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <p class="mt-6 text-center text-gray-400">
        Don't have an account?
        <router-link to="/register" class="text-primary-500 hover:underline">
          Sign up
        </router-link>
      </p>
    </div>
  </div>
</template>
