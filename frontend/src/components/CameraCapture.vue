<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['capture', 'error'])

const videoRef = ref(null)
const canvasRef = ref(null)
const stream = ref(null)
const isReady = ref(false)
const facingMode = ref('environment') // 'user' or 'environment'

const startCamera = async () => {
  try {
    if (stream.value) {
      stream.value.getTracks().forEach(track => track.stop())
    }

    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: facingMode.value,
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      await videoRef.value.play()
      isReady.value = true
    }
  } catch (error) {
    console.error('Camera access error:', error)
    emit('error', error.message || 'Could not access camera')
  }
}

const switchCamera = async () => {
  facingMode.value = facingMode.value === 'user' ? 'environment' : 'user'
  await startCamera()
}

const capturePhoto = () => {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  ctx.drawImage(video, 0, 0)

  canvas.toBlob((blob) => {
    if (blob) {
      emit('capture', {
        blob,
        dataUrl: canvas.toDataURL('image/jpeg', 0.9),
        width: canvas.width,
        height: canvas.height
      })
    }
  }, 'image/jpeg', 0.9)
}

onMounted(() => {
  startCamera()
})

onUnmounted(() => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
  }
})

defineExpose({ capturePhoto, switchCamera })
</script>

<template>
  <div class="camera-container relative">
    <video
      ref="videoRef"
      autoplay
      playsinline
      muted
      class="w-full h-full object-cover"
    />
    <canvas ref="canvasRef" class="hidden" />

    <!-- Camera controls overlay -->
    <div class="absolute bottom-4 left-0 right-0 flex justify-center items-center space-x-4">
      <!-- Switch camera button -->
      <button
        @click="switchCamera"
        class="p-3 bg-dark-200/80 rounded-full text-white hover:bg-dark-300"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <!-- Capture button -->
      <button
        @click="capturePhoto"
        :disabled="!isReady"
        class="w-16 h-16 bg-white rounded-full border-4 border-primary-500 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
      >
        <span class="sr-only">Capture</span>
      </button>

      <!-- Placeholder for symmetry -->
      <div class="w-12 h-12"></div>
    </div>

    <!-- Loading overlay -->
    <div v-if="!isReady" class="absolute inset-0 flex items-center justify-center bg-black/50">
      <div class="spinner"></div>
    </div>
  </div>
</template>
