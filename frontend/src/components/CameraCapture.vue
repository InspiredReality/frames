<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  defaultZoom: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['capture', 'error'])

const videoRef = ref(null)
const canvasRef = ref(null)
const fileInputRef = ref(null)
const stream = ref(null)
const isReady = ref(false)
const cameraError = ref(null) // null | 'denied' | 'unavailable'
const facingMode = ref('environment') // 'user' or 'environment'
let autoCaptureId = null

const applyZoom = async (target) => {
  if (target === null || !stream.value) return
  try {
    const track = stream.value.getVideoTracks()[0]
    if (!track || typeof track.getCapabilities !== 'function') return
    const caps = track.getCapabilities()
    if (!caps?.zoom) return
    const clamped = Math.max(caps.zoom.min, Math.min(caps.zoom.max, target))
    await track.applyConstraints({ advanced: [{ zoom: clamped }] })
  } catch {
    // zoom not supported on this device/browser — silently ignore
  }
}

const startCamera = async () => {
  cameraError.value = null
  isReady.value = false
  try {
    if (stream.value) {
      stream.value.getTracks().forEach(track => track.stop())
    }

    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: facingMode.value,
        width: { ideal: 1080 },
        height: { ideal: 1920 }
      }
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      await videoRef.value.play()
      isReady.value = true
      await applyZoom(props.defaultZoom)
    }
  } catch (err) {
    console.error('Camera access error:', err)
    const isDenied = err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError'
    cameraError.value = isDenied ? 'denied' : 'unavailable'
    emit('error', isDenied ? 'camera-permission-denied' : (err.message || 'Could not access camera'))
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

const triggerUpload = () => {
  fileInputRef.value?.click()
}

const handleFileUpload = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      const canvas = canvasRef.value
      const ctx = canvas.getContext('2d')
      canvas.width = img.width
      canvas.height = img.height
      ctx.drawImage(img, 0, 0)

      canvas.toBlob((blob) => {
        if (blob) {
          emit('capture', {
            blob,
            dataUrl: e.target.result,
            width: img.width,
            height: img.height
          })
        }
      }, 'image/jpeg', 0.9)
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)

  event.target.value = ''
}

const startAutoCapture = (intervalMs = 800) => {
  stopAutoCapture()
  autoCaptureId = setInterval(() => {
    if (isReady.value) capturePhoto()
  }, intervalMs)
}

const stopAutoCapture = () => {
  if (autoCaptureId !== null) {
    clearInterval(autoCaptureId)
    autoCaptureId = null
  }
}

onMounted(() => {
  startCamera()
})

onUnmounted(() => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
  }
  stopAutoCapture()
})

defineExpose({ capturePhoto, switchCamera, triggerUpload, startAutoCapture, stopAutoCapture })
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

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      class="hidden"
      @change="handleFileUpload"
    />

    <!-- Camera controls overlay -->
    <div class="absolute bottom-4 left-0 right-0 flex justify-center items-center space-x-4">
      <!-- Switch camera button -->
      <button
        @click="switchCamera"
        class="p-3 bg-dark-200/80 rounded-full text-white hover:bg-dark-300"
        title="Switch camera"
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
        title="Take photo"
      >
        <span class="sr-only">Capture</span>
      </button>

      <!-- Upload button -->
      <button
        @click="triggerUpload"
        class="p-3 bg-dark-200/80 rounded-full text-white hover:bg-dark-300"
        title="Upload photo"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </button>
    </div>

    <!-- Camera error overlay -->
    <div v-if="cameraError" class="absolute inset-0 flex flex-col items-center justify-center bg-black/80 text-center px-6 gap-4">
      <svg class="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
      <div v-if="cameraError === 'denied'">
        <p class="text-white font-semibold mb-1">Camera access denied</p>
        <p class="text-gray-400 text-sm">Allow camera access in your browser's site settings, then tap Retry.</p>
      </div>
      <div v-else>
        <p class="text-white font-semibold mb-1">Camera unavailable</p>
        <p class="text-gray-400 text-sm">Your camera could not be accessed. Check that no other app is using it.</p>
      </div>
      <button
        @click="startCamera"
        class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm transition"
      >
        Retry
      </button>
    </div>

    <!-- Loading overlay -->
    <div v-else-if="!isReady" class="absolute inset-0 flex items-center justify-center bg-black/50">
      <div class="spinner"></div>
    </div>
  </div>
</template>
