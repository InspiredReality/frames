<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
})

const handleSubmit = async () => {
  error.value = ''

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  if (newPassword.value.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }

  loading.value = true
  try {
    await authStore.resetPassword(token.value, newPassword.value)
    success.value = true
    setTimeout(() => router.push('/login'), 2000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid or expired token. Please request a new one.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="card">
      <h1 class="text-2xl font-bold text-center mb-6">Reset Password</h1>

      <div v-if="success" class="p-3 bg-green-500/20 border border-green-500 rounded-lg text-green-400 text-sm text-center">
        Password reset successfully! Redirecting to login…
      </div>

      <form v-else @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="error" class="p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm">
          {{ error }}
        </div>

        <input v-model="token" type="hidden" />

        <div>
          <label class="block text-sm text-gray-400 mb-1">New Password</label>
          <input
            v-model="newPassword"
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
            placeholder="Repeat new password"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="btn btn-primary w-full py-3"
        >
          <span v-if="loading">Resetting...</span>
          <span v-else>Reset Password</span>
        </button>
      </form>

      <p class="mt-6 text-center text-gray-400">
        <router-link to="/forgot-password" class="text-primary-500 hover:underline">
          Request a new token
        </router-link>
      </p>
    </div>
  </div>
</template>
