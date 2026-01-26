<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import { useWallsStore } from '@/store/walls'

const router = useRouter()
const wallsStore = useWallsStore()

const step = ref(1) // 1: capture, 2: details
const capturedImage = ref(null)
const wallName = ref('')
const wallDescription = ref('')
const wallWidth = ref('')
const wallHeight = ref('')
const wallUnit = ref('feet') // 'feet', 'inches', or 'cm'
const loading = ref(false)
const error = ref('')

// Conversion constants
const INCHES_PER_FOOT = 12
const CM_PER_INCH = 2.54

const unitLabels = {
  feet: 'ft',
  inches: 'in',
  cm: 'cm'
}

const unitPlaceholders = {
  feet: { width: 'e.g., 10', height: 'e.g., 8' },
  inches: { width: 'e.g., 120', height: 'e.g., 96' },
  cm: { width: 'e.g., 300', height: 'e.g., 250' }
}

const toggleUnit = () => {
  const units = ['feet', 'inches', 'cm']
  const currentIndex = units.indexOf(wallUnit.value)
  const newUnit = units[(currentIndex + 1) % units.length]

  // Convert existing values
  if (wallWidth.value) {
    wallWidth.value = convertDimension(parseFloat(wallWidth.value), wallUnit.value, newUnit)
  }
  if (wallHeight.value) {
    wallHeight.value = convertDimension(parseFloat(wallHeight.value), wallUnit.value, newUnit)
  }

  wallUnit.value = newUnit
}

const convertDimension = (value, fromUnit, toUnit) => {
  if (!value) return ''

  // First convert to cm
  let cm = value
  if (fromUnit === 'feet') cm = value * INCHES_PER_FOOT * CM_PER_INCH
  else if (fromUnit === 'inches') cm = value * CM_PER_INCH

  // Then convert from cm to target unit
  let result = cm
  if (toUnit === 'feet') result = cm / (INCHES_PER_FOOT * CM_PER_INCH)
  else if (toUnit === 'inches') result = cm / CM_PER_INCH

  return result.toFixed(toUnit === 'feet' ? 2 : toUnit === 'inches' ? 1 : 0)
}

const getDimensionInCm = (value) => {
  if (!value) return null
  const num = parseFloat(value)
  if (wallUnit.value === 'cm') return num
  if (wallUnit.value === 'inches') return num * CM_PER_INCH
  if (wallUnit.value === 'feet') return num * INCHES_PER_FOOT * CM_PER_INCH
  return num
}

const onCapture = (data) => {
  capturedImage.value = data
  step.value = 2
}

const onCameraError = (message) => {
  error.value = message
}

const retake = () => {
  capturedImage.value = null
  step.value = 1
  error.value = ''
}

const saveWall = async () => {
  if (!wallName.value.trim()) {
    error.value = 'Please enter a name for your wall'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const file = new File([capturedImage.value.blob], 'wall.jpg', { type: 'image/jpeg' })

    await wallsStore.uploadWall(file, wallName.value, wallDescription.value, {
      width_cm: getDimensionInCm(wallWidth.value),
      height_cm: getDimensionInCm(wallHeight.value)
    })

    router.push('/gallery')
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save wall'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Step indicator -->
    <div class="flex items-center justify-center mb-8">
      <div
        v-for="s in 2"
        :key="s"
        class="flex items-center"
      >
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors"
          :class="step >= s ? 'bg-primary-500 text-white' : 'bg-dark-300 text-gray-400'"
        >
          {{ s }}
        </div>
        <div
          v-if="s < 2"
          class="w-12 h-1 mx-2"
          :class="step > s ? 'bg-primary-500' : 'bg-dark-300'"
        ></div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
      {{ error }}
    </div>

    <!-- Step 1: Camera Capture -->
    <div v-if="step === 1">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Wall</h2>
      <p class="text-gray-400 text-center mb-6">
        Take a photo of the wall where you want to place your pictures
      </p>
      <CameraCapture @capture="onCapture" @error="onCameraError" />
    </div>

    <!-- Step 2: Wall Details -->
    <div v-if="step === 2" class="card">
      <h2 class="text-2xl font-bold mb-4">Wall Details</h2>

      <!-- Preview of captured image -->
      <div class="mb-6">
        <img
          :src="capturedImage.dataUrl"
          alt="Captured wall"
          class="w-full max-h-64 object-contain rounded-lg bg-dark-300"
        />
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Wall Name *</label>
          <input
            v-model="wallName"
            type="text"
            placeholder="e.g., Living Room, Bedroom, Office"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Description (optional)</label>
          <textarea
            v-model="wallDescription"
            rows="2"
            placeholder="Any notes about this wall..."
            class="w-full px-4 py-2 bg-dark-300 border border-gray-600 rounded-lg text-white"
          ></textarea>
        </div>

        <!-- Wall Dimensions with Unit Toggle -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-gray-400">Wall Dimensions (optional)</span>
            <button
              @click="toggleUnit"
              class="px-3 py-1 text-sm bg-dark-300 rounded-full hover:bg-dark-100 transition"
            >
              Switch to {{ wallUnit === 'feet' ? 'inches' : wallUnit === 'inches' ? 'cm' : 'feet' }}
            </button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-400 mb-1">Width ({{ unitLabels[wallUnit] }})</label>
              <input
                v-model="wallWidth"
                type="number"
                :step="wallUnit === 'feet' ? '0.5' : '1'"
                min="0"
                :placeholder="unitPlaceholders[wallUnit].width"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-400 mb-1">Height ({{ unitLabels[wallUnit] }})</label>
              <input
                v-model="wallHeight"
                type="number"
                :step="wallUnit === 'feet' ? '0.5' : '1'"
                min="0"
                :placeholder="unitPlaceholders[wallUnit].height"
              />
            </div>
          </div>
        </div>

        <p class="text-xs text-gray-500">
          Providing wall dimensions helps with accurate frame placement
        </p>
      </div>

      <div class="flex gap-4 mt-6">
        <button @click="retake" class="btn btn-secondary flex-1">
          Retake Photo
        </button>
        <button
          @click="saveWall"
          :disabled="loading"
          class="btn btn-primary flex-1"
        >
          <span v-if="loading">Saving...</span>
          <span v-else>Save Wall</span>
        </button>
      </div>
    </div>
  </div>
</template>
