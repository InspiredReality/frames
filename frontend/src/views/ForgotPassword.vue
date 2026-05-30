<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const email = ref('')
const loading = ref(false)
const error = ref('')
const submitted = ref(false)

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    await authStore.forgotPassword(email.value)
    submitted.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12">
    <div class="card">
      <h1 class="text-2xl font-bold text-center mb-2">Forgot Password</h1>

      <div v-if="!submitted">
        <p class="text-gray-400 text-sm text-center mb-6">
          Enter your email and we'll send you a reset link.
        </p>

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

          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary w-full py-3"
          >
            <span v-if="loading">Sending...</span>
            <span v-else>Send Reset Link</span>
          </button>
        </form>
      </div>

      <div v-else class="space-y-4">
        <div class="p-3 bg-green-500/20 border border-green-500 rounded-lg text-green-400 text-sm text-center">
          Check your email for a reset link. It expires in 15 minutes.
        </div>
      </div>

      <p class="mt-6 text-center text-gray-400">
        <router-link to="/login" class="text-primary-500 hover:underline">
          Back to login
        </router-link>
      </p>
    </div>
  </div>
</template>
