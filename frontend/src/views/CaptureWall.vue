<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import { useWallsStore } from '@/store/walls'

const router = useRouter()
const wallsStore = useWallsStore()

const step = ref(1) // 1: capture/choose, 2: crop, 3: details
const capturedImage = ref(null)
const croppedImage = ref(null)
const wallName = ref('')
const wallDescription = ref('')
const wallWidth = ref('')
const wallHeight = ref('')
const wallUnit = ref('feet') // 'feet', 'inches', or 'cm'
const loading = ref(false)
const error = ref('')

// Blank color wall state
const useBlankColor = ref(false)
const wallColor = ref('#e0e0e0')
const showCustomWallColor = ref(false)

const wallColorPresets = [
  { label: 'White', value: '#FFFFFF' },
  { label: 'Off-White', value: '#F5F5DC' },
  { label: 'Light Gray', value: '#D3D3D3' },
  { label: 'Gray', value: '#808080' },
  { label: 'Black', value: '#000000' },
  { label: 'Brown', value: '#8B4513' }
]

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
  croppedImage.value = data // Initialize with full image
  useBlankColor.value = false
  step.value = 2
}

const onCrop = (data) => {
  croppedImage.value = data
}

const skipCrop = () => {
  step.value = 3
}

const confirmCrop = () => {
  step.value = 3
}

const onCameraError = (message) => {
  error.value = message
}

const selectBlankColor = () => {
  useBlankColor.value = true
  capturedImage.value = null
  croppedImage.value = null
  step.value = 3
}

const retake = () => {
  capturedImage.value = null
  croppedImage.value = null
  useBlankColor.value = false
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
    let file = null
    let bgColor = null

    if (useBlankColor.value) {
      bgColor = wallColor.value
    } else {
      file = new File([croppedImage.value.blob], 'wall.jpg', { type: 'image/jpeg' })
    }

    await wallsStore.uploadWall(file, wallName.value, wallDescription.value, {
      width_cm: getDimensionInCm(wallWidth.value),
      height_cm: getDimensionInCm(wallHeight.value)
    }, bgColor)

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
        v-for="s in 3"
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
          v-if="s < 3"
          class="w-12 h-1 mx-2"
          :class="step > s ? 'bg-primary-500' : 'bg-dark-300'"
        ></div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
      {{ error }}
    </div>

    <!-- Step 1: Camera Capture or Blank Color -->
    <div v-if="step === 1">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Wall</h2>
      <p class="text-gray-400 text-center mb-6">
        Take a photo of the wall or use a blank color background
      </p>

      <CameraCapture @capture="onCapture" @error="onCameraError" />

      <div class="mt-6 text-center">
        <div class="flex items-center gap-4 mb-4">
          <div class="flex-1 h-px bg-gray-600"></div>
          <span class="text-gray-400 text-sm">or</span>
          <div class="flex-1 h-px bg-gray-600"></div>
        </div>
        <button
          @click="selectBlankColor"
          class="btn btn-secondary w-full"
        >
          Use Blank Color Background
        </button>
      </div>
    </div>

    <!-- Step 2: Crop -->
    <div v-if="step === 2" class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-4 text-center">Crop Your Wall Photo</h2>
      <p class="text-gray-400 text-center mb-6">
        Drag the corners or edges to select the wall area
      </p>

      <div class="card mb-4">
        <ImageCropper
          :imageUrl="capturedImage.dataUrl"
          @crop="onCrop"
        />
      </div>

      <!-- Cropped Preview -->
      <div v-if="croppedImage?.dataUrl" class="card mb-4">
        <h3 class="font-semibold mb-2">Cropped Result</h3>
        <div class="bg-dark-300 rounded-lg overflow-hidden flex items-center justify-center" style="max-height: 200px;">
          <img
            :src="croppedImage.dataUrl"
            alt="Cropped preview"
            class="max-w-full max-h-full object-contain"
          />
        </div>
        <div class="mt-2 text-xs text-gray-500 text-center">
          {{ croppedImage.width }} x {{ croppedImage.height }} pixels
        </div>
      </div>

      <div class="flex gap-4">
        <button @click="retake" class="btn btn-secondary flex-1">
          Retake Photo
        </button>
        <button @click="confirmCrop" class="btn btn-primary flex-1">
          Continue
        </button>
      </div>
    </div>

    <!-- Step 3: Wall Details -->
    <div v-if="step === 3" class="card">
      <h2 class="text-2xl font-bold mb-4">Wall Details</h2>

      <!-- Preview of cropped image -->
      <div v-if="!useBlankColor && croppedImage" class="mb-6">
        <img
          :src="croppedImage.dataUrl"
          alt="Cropped wall"
          class="w-full max-h-64 object-contain rounded-lg bg-dark-300"
        />
      </div>

      <!-- Color preview for blank walls -->
      <div v-else class="mb-6">
        <div
          class="w-full h-40 rounded-lg border border-gray-600"
          :style="{ backgroundColor: wallColor }"
        ></div>

        <!-- Color selection -->
        <div class="mt-3">
          <label class="block text-sm text-gray-400 mb-2">Wall Color</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="preset in wallColorPresets"
              :key="preset.value"
              @click="wallColor = preset.value; showCustomWallColor = false"
              class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
              :class="wallColor === preset.value && !showCustomWallColor ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span
                class="w-5 h-5 rounded-full border border-gray-500"
                :style="{ backgroundColor: preset.value }"
              ></span>
              <span class="text-sm">{{ preset.label }}</span>
            </button>
            <button
              @click="showCustomWallColor = !showCustomWallColor"
              class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
              :class="showCustomWallColor ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span
                class="w-5 h-5 rounded-full border border-gray-500"
                :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }"
              ></span>
              <span class="text-sm">Custom</span>
            </button>
          </div>
          <div v-if="showCustomWallColor" class="mt-2">
            <input
              type="color"
              v-model="wallColor"
              class="w-full h-10 rounded cursor-pointer bg-transparent border border-gray-600"
            />
          </div>
        </div>
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
        <button @click="useBlankColor ? retake() : (step = 2)" class="btn btn-secondary flex-1">
          {{ useBlankColor ? 'Go Back' : 'Edit Crop' }}
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
