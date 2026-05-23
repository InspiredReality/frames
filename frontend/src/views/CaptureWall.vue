<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import QrCodeCard from '@/components/QrCodeCard.vue'
import { useWallsStore } from '@/store/walls'

const router = useRouter()
const wallsStore = useWallsStore()

const step = ref(1) // 1: capture/choose, 2: crop, 3: details
const capturedImage = ref(null)
const croppedImage = ref(null)
const wallName = ref('')
const wallDescription = ref('')
const wallUnit = ref('ft') // 'ft' or 'cm'
// Source of truth - always stored in cm
const wallWidthCm = ref(0)
const wallHeightCm = ref(0)
const loading = ref(false)
const error = ref('')
const lockAspectRatio = ref(false)

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

// Computed display values for ft & in mode (derived from cm source of truth)
const displayWidthFt = computed({
  get: () => {
    if (!wallWidthCm.value) return ''
    const totalInches = wallWidthCm.value / CM_PER_INCH
    return Math.floor(totalInches / INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(val) || 0
    const inches = parseFloat(displayWidthIn.value) || 0
    wallWidthCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayWidthIn = computed({
  get: () => {
    if (!wallWidthCm.value) return ''
    const totalInches = wallWidthCm.value / CM_PER_INCH
    return Math.round(totalInches % INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(displayWidthFt.value) || 0
    const inches = parseFloat(val) || 0
    wallWidthCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayHeightFt = computed({
  get: () => {
    if (!wallHeightCm.value) return ''
    const totalInches = wallHeightCm.value / CM_PER_INCH
    return Math.floor(totalInches / INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(val) || 0
    const inches = parseFloat(displayHeightIn.value) || 0
    wallHeightCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayHeightIn = computed({
  get: () => {
    if (!wallHeightCm.value) return ''
    const totalInches = wallHeightCm.value / CM_PER_INCH
    return Math.round(totalInches % INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(displayHeightFt.value) || 0
    const inches = parseFloat(val) || 0
    wallHeightCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

// Computed display values for cm mode
const displayWidthCm = computed({
  get: () => wallWidthCm.value ? Math.round(wallWidthCm.value) : '',
  set: (val) => { wallWidthCm.value = parseFloat(val) || 0 }
})

const displayHeightCm = computed({
  get: () => wallHeightCm.value ? Math.round(wallHeightCm.value) : '',
  set: (val) => { wallHeightCm.value = parseFloat(val) || 0 }
})

// Toggle functions - just change display unit, no conversion needed
const selectFtIn = () => { wallUnit.value = 'ft' }
const selectCm = () => { wallUnit.value = 'cm' }

// Aspect ratio of the original captured photo (used for optional lock)
const capturedAspectRatio = computed(() => {
  if (!capturedImage.value?.width || !capturedImage.value?.height) return null
  return capturedImage.value.width / capturedImage.value.height
})
const cropAspectRatio = computed(() => lockAspectRatio.value ? capturedAspectRatio.value : null)

// Reset lock when going back to capture
watch(step, (s) => { if (s === 1) lockAspectRatio.value = false })

// Get values in cm for saving (source of truth)
const getWidthInCm = () => wallWidthCm.value || null
const getHeightInCm = () => wallHeightCm.value || null

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
  step.value = 2  // Go to step 2 for color + dimensions
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
      width_cm: getWidthInCm(),
      height_cm: getHeightInCm()
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

    <!-- Step labels -->
    <div class="flex justify-center gap-8 mb-6 text-sm text-gray-400">
      <span :class="step >= 1 ? 'text-primary-400' : ''">1. Take/Upload Photo</span>
      <span :class="step >= 2 ? 'text-primary-400' : ''">2. Crop & Size</span>
      <span :class="step >= 3 ? 'text-primary-400' : ''">3. Save to Gallery</span>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
      {{ error }}
    </div>

    <!-- Step 1: Camera Capture or Blank Color -->
    <div v-if="step === 1">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Wall</h2>
      <p class="text-gray-400 text-center mb-6">
        Take or upload a photo of the wall or use a blank color background
      </p>

      <CameraCapture @capture="onCapture" @error="onCameraError" />

      <div class="mt-6">
        <QrCodeCard />
      </div>

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

    <!-- Step 2: Crop & Size (or Color & Size for blank walls) -->
    <div v-if="step === 2" class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-4 text-center">{{ useBlankColor ? 'Color & Size' : 'Crop & Size' }}</h2>
      <p class="text-gray-400 text-center mb-6">
        {{ useBlankColor ? 'Choose wall color and enter dimensions' : 'Crop your wall photo and enter dimensions' }}
      </p>

      <!-- Photo cropping (for captured images) -->
      <div v-if="!useBlankColor && capturedImage" class="card mb-4">
        <ImageCropper
          :imageUrl="capturedImage.dataUrl"
          :aspectRatio="cropAspectRatio"
          @crop="onCrop"
        />
        <div class="flex items-center gap-2 mt-3 p-3 bg-dark-300 rounded-lg">
          <input
            type="checkbox"
            id="lockRatio"
            v-model="lockAspectRatio"
            class="w-4 h-4 rounded border-gray-600 bg-dark-100 text-primary-500 focus:ring-primary-500 cursor-pointer"
          />
          <label for="lockRatio" class="text-sm text-gray-300 cursor-pointer select-none">
            Lock aspect ratio
            <span v-if="capturedAspectRatio" class="text-gray-500">({{ capturedAspectRatio.toFixed(2) }})</span>
          </label>
        </div>
      </div>

      <!-- Color selection (for blank color walls) -->
      <div v-if="useBlankColor" class="card mb-4">
        <h3 class="font-semibold mb-3">Wall Color</h3>
        <div
          class="w-full h-32 rounded-lg border border-gray-600 mb-3"
          :style="{ backgroundColor: wallColor }"
        ></div>
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

      <!-- Wall Dimensions -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold">Wall Dimensions (optional)</h3>
          <div class="flex gap-2">
            <button
              @click="selectFtIn"
              class="px-3 py-1 text-sm rounded-full transition"
              :class="wallUnit === 'ft' ? 'bg-primary-500 text-white' : 'bg-dark-300 hover:bg-dark-100'"
            >
              ft & in
            </button>
            <button
              @click="selectCm"
              class="px-3 py-1 text-sm rounded-full transition"
              :class="wallUnit === 'cm' ? 'bg-primary-500 text-white' : 'bg-dark-300 hover:bg-dark-100'"
            >
              cm
            </button>
          </div>
        </div>

        <!-- ft & in inputs -->
        <div v-if="wallUnit === 'ft'" class="space-y-3">
          <div>
            <label class="block text-xs text-gray-400 mb-1">Width</label>
            <div class="flex gap-2">
              <div class="flex-1">
                <input
                  v-model="displayWidthFt"
                  type="number"
                  min="0"
                  placeholder="ft"
                  class="w-full"
                />
              </div>
              <div class="flex-1">
                <input
                  v-model="displayWidthIn"
                  type="number"
                  min="0"
                  max="11"
                  placeholder="in"
                  class="w-full"
                />
              </div>
            </div>
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Height</label>
            <div class="flex gap-2">
              <div class="flex-1">
                <input
                  v-model="displayHeightFt"
                  type="number"
                  min="0"
                  placeholder="ft"
                  class="w-full"
                />
              </div>
              <div class="flex-1">
                <input
                  v-model="displayHeightIn"
                  type="number"
                  min="0"
                  max="11"
                  placeholder="in"
                  class="w-full"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- cm inputs -->
        <div v-else class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1">Width (cm)</label>
            <input
              v-model="displayWidthCm"
              type="number"
              min="0"
              placeholder="e.g., 300"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Height (cm)</label>
            <input
              v-model="displayHeightCm"
              type="number"
              min="0"
              placeholder="e.g., 250"
            />
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">
          Providing wall dimensions helps with accurate frame placement
        </p>
      </div>

      <!-- Cropped Result Preview -->
      <div v-if="!useBlankColor && croppedImage?.dataUrl" class="card mb-4">
        <h3 class="font-semibold mb-2">Cropped Result</h3>
        <img
          :src="croppedImage.dataUrl"
          alt="Cropped preview"
          class="w-full rounded-lg"
        />
        <div class="mt-2 text-xs text-gray-500 text-center">
          {{ croppedImage.width }} x {{ croppedImage.height }} pixels
        </div>
      </div>

      <div class="flex gap-4">
        <button @click="retake" class="btn btn-secondary flex-1">
          {{ useBlankColor ? 'Go Back' : 'Retake Photo' }}
        </button>
        <button @click="confirmCrop" class="btn btn-primary flex-1">
          Continue
        </button>
      </div>
    </div>

    <!-- Step 3: Save to Gallery -->
    <div v-if="step === 3" class="card">
      <h2 class="text-2xl font-bold mb-4 text-center">Save to Gallery</h2>
      <p class="text-gray-400 text-center mb-6">
        Give your wall a name and save it
      </p>

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
            class="w-full px-4 py-2 bg-dark-300 border border-gray-600 rounded-lg text-white resize-none"
          ></textarea>
        </div>
      </div>

      <div class="flex gap-4 mt-6">
        <button @click="step = 2" class="btn btn-secondary flex-1">
          {{ useBlankColor ? 'Edit Color & Size' : 'Edit Crop & Size' }}
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
