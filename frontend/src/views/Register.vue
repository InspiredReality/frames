<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }

  loading.value = true

  try {
    await authStore.register(email.value, username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.error || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="card">
      <h1 class="text-2xl font-bold text-center mb-6">Create Account</h1>

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
          <label class="block text-sm text-gray-400 mb-1">Username</label>
          <input
            v-model="username"
            type="text"
            required
            placeholder="Choose a username"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Password</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="At least 6 characters"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Confirm Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your password"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="btn btn-primary w-full py-3"
        >
          <span v-if="loading">Creating account...</span>
          <span v-else>Create Account</span>
        </button>
      </form>

      <p class="mt-6 text-center text-gray-400">
        Already have an account?
        <router-link to="/login" class="text-primary-500 hover:underline">
          Sign in
        </router-link>
      </p>
    </div>
  </div>
</template>
