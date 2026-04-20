<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import DimensionInput from '@/components/DimensionInput.vue'
import FramePreview from '@/components/FramePreview.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import QrCodeCard from '@/components/QrCodeCard.vue'
import { usePicturesStore } from '@/store/pictures'
import { useWallsStore } from '@/store/walls'
import { getUploadUrl } from '@/services/api'

const router = useRouter()
const picturesStore = usePicturesStore()
const wallsStore = useWallsStore()

const step = ref(1) // 1: capture, 2: crop & dimensions, 3: preview
const capturedImage = ref(null)
const croppedImage = ref(null)
const dimensions = ref({ width: '', height: '', depth: 1, unit: 'inches', orientation: 'portrait' })
const pictureName = ref('')
const selectedWallId = ref(null)
const frameColor = ref('#000000')
const frameThickness = ref(1)
const showColorPicker = ref(false)
const totalDimensions = ref({ width: 0, height: 0 })
const loading = ref(false)
const error = ref('')

const presetColors = [
  { label: 'Black', value: '#000000' },
  { label: 'White', value: '#FFFFFF' },
  { label: 'Brown', value: '#8B4513' }
]

const cameraRef = ref(null)
const cropperRef = ref(null)

// Fetch walls on mount
onMounted(async () => {
  await wallsStore.fetchWalls()
})

// Calculate aspect ratio from dimensions if both are set
const aspectRatio = computed(() => {
  if (dimensions.value.width && dimensions.value.height) {
    return parseFloat(dimensions.value.width) / parseFloat(dimensions.value.height)
  }
  return null
})

// Stable reference for FramePreview dimensions (avoids infinite re-render loop)
const framePreviewDimensions = computed(() => ({
  width: parseFloat(dimensions.value.width) || 10,
  height: parseFloat(dimensions.value.height) || 8,
  depth: parseFloat(dimensions.value.depth) || 1
}))

// Get selected wall
const selectedWall = computed(() => {
  if (!selectedWallId.value) return null
  return wallsStore.walls.find(w => w.id === selectedWallId.value)
})

const getWallImageUrl = (path) => {
  return getUploadUrl(path)
}

const onCapture = (data) => {
  capturedImage.value = data
  croppedImage.value = data // Initialize with full image
  step.value = 2
}

const onCameraError = (message) => {
  error.value = message
}

const onCrop = (data) => {
  croppedImage.value = data
}

const retake = () => {
  capturedImage.value = null
  croppedImage.value = null
  step.value = 1
  error.value = ''
}

const goToPreview = () => {
  if (!dimensions.value.width || !dimensions.value.height) {
    error.value = 'Please enter frame dimensions'
    return
  }
  if (!croppedImage.value) {
    error.value = 'Please crop your image'
    return
  }
  error.value = ''
  step.value = 3
}

const savePicture = async () => {
  if (!pictureName.value.trim()) {
    error.value = 'Please enter a name for your frame'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Upload the cropped picture with optional wall assignment
    const file = new File([croppedImage.value.blob], 'frame.jpg', { type: 'image/jpeg' })
    const picture = await picturesStore.uploadPicture(file, pictureName.value, '', selectedWallId.value)

    // Create the frame with dimensions and styling
    const frame = await picturesStore.createFrame(picture.id, {
      width: parseFloat(dimensions.value.width),
      height: parseFloat(dimensions.value.height),
      depth: parseFloat(dimensions.value.depth) || 1,
      unit: dimensions.value.unit,
      frame_color: frameColor.value,
      frame_thickness: frameThickness.value,
      total_width: totalDimensions.value.width,
      total_height: totalDimensions.value.height
    })

    // If a wall was selected, also add a frame placement to that wall
    if (selectedWallId.value && frame?.id) {
      await wallsStore.addFramePlacement(selectedWallId.value, {
        frame_id: frame.id,
        position: { x: 0, y: 0 },
        rotation: { x: 0, y: 0, z: 0 },
        scale: 1.0
      })
    }

    router.push('/gallery')
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save frame'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto">
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
      <span :class="step >= 1 ? 'text-primary-400' : ''">1. Capture</span>
      <span :class="step >= 2 ? 'text-primary-400' : ''">2. Crop & Size</span>
      <span :class="step >= 3 ? 'text-primary-400' : ''">3. Preview</span>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
      {{ error }}
    </div>

    <!-- Step 1: Camera Capture -->
    <div v-if="step === 1" class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Frame</h2>
      <p class="text-gray-400 text-center mb-6">
        Take a clear photo of the artwork or picture you want to add
      </p>
      <CameraCapture ref="cameraRef" @capture="onCapture" @error="onCameraError" />
      <div class="mt-6">
        <QrCodeCard />
      </div>
    </div>

    <!-- Step 2: Crop & Dimensions - Two Column Layout -->
    <div v-if="step === 2">
      <h2 class="text-2xl font-bold mb-6 text-center">Crop & Set Dimensions</h2>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Left Column: Dimensions + Wall Selection -->
        <div class="space-y-4">
          <!-- Dimensions Input -->
          <div class="card">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">1</span>
              Frame Dimensions
            </h3>
            <p class="text-sm text-gray-400 mb-4">
              Enter the real-world size of your picture frame
            </p>
            <DimensionInput v-model="dimensions" />
          </div>

          <!-- Wall Selection (Optional) -->
          <div class="card" v-if="wallsStore.walls.length > 0">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-gray-500 rounded-full flex items-center justify-center text-xs">+</span>
              Assign to Wall (Optional)
            </h3>
            <p class="text-sm text-gray-400 mb-3">
              Select a wall to place this picture on
            </p>
            <div class="grid grid-cols-3 gap-2">
              <button
                @click="selectedWallId = null"
                class="aspect-video rounded-lg border-2 transition flex items-center justify-center text-sm"
                :class="selectedWallId === null ? 'border-primary-500 bg-primary-500/10' : 'border-gray-600 hover:border-gray-500'"
              >
                None
              </button>
              <button
                v-for="wall in wallsStore.walls"
                :key="wall.id"
                @click="selectedWallId = wall.id"
                class="aspect-video rounded-lg border-2 overflow-hidden transition relative"
                :class="selectedWallId === wall.id ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
              >
                <img
                  :src="getWallImageUrl(wall.thumbnail_path || wall.image_path)"
                  :alt="wall.name"
                  class="w-full h-full object-cover"
                />
                <div class="absolute bottom-0 left-0 right-0 bg-black/60 px-1 py-0.5">
                  <span class="text-xs truncate block">{{ wall.name }}</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Right Column: Crop Tool + Cropped Result -->
        <div class="space-y-4">
          <div class="card">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">2</span>
              Crop Your Image
            </h3>
            <p class="text-sm text-gray-400 mb-4">
              Drag the corners or edges to select the area you want to keep
            </p>
            <ImageCropper
              ref="cropperRef"
              :imageUrl="capturedImage.dataUrl"
              :aspectRatio="aspectRatio"
              :orientation="dimensions.orientation"
              @crop="onCrop"
            />
          </div>

          <!-- Cropped Preview -->
          <div class="card">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">3</span>
              Cropped Result
            </h3>
            <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden flex items-center justify-center">
              <img
                v-if="croppedImage?.dataUrl"
                :src="croppedImage.dataUrl"
                alt="Cropped preview"
                class="max-w-full max-h-full object-contain"
              />
              <span v-else class="text-gray-500">Crop preview will appear here</span>
            </div>
            <div v-if="croppedImage" class="mt-2 text-xs text-gray-500 text-center">
              {{ croppedImage.width }} x {{ croppedImage.height }} pixels
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-4 mt-6 max-w-md mx-auto">
        <button @click="retake" class="btn btn-secondary flex-1">
          Retake Photo
        </button>
        <button @click="goToPreview" class="btn btn-primary flex-1">
          Preview 3D Frame
        </button>
      </div>
    </div>

    <!-- Step 3: Preview and Save -->
    <div v-if="step === 3" class="max-w-2xl mx-auto">
      <div class="card">
        <h2 class="text-2xl font-bold mb-4">Preview & Save</h2>

        <!-- Side by side: cropped image and 3D preview -->
        <div class="grid md:grid-cols-2 gap-4 mb-6">
          <!-- Cropped Image -->
          <!-- <div>
            <h4 class="text-sm text-gray-400 mb-2">Your Image</h4>
            <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden flex items-center justify-center">
              <img
                :src="croppedImage.dataUrl"
                alt="Cropped picture"
                class="max-w-full max-h-full object-contain"
              />
            </div>
          </div> -->

          <!-- 3D Preview -->
          <div>
            <h4 class="text-sm text-gray-400 mb-2">3D Frame Preview</h4>
            <FramePreview
              :imageUrl="croppedImage.dataUrl"
              :dimensions="framePreviewDimensions"
              :frameColor="frameColor"
              :frameThickness="frameThickness"
              @update:totalDimensions="totalDimensions = $event"
            />
          </div>
        </div>

        <p class="text-sm text-gray-400 text-center mb-4">
          Drag to rotate the 3D preview
        </p>

        <!-- Name input -->
        <div class="mb-6">
          <label class="block text-sm text-gray-400 mb-1">Frame Name</label>
          <input
            v-model="pictureName"
            type="text"
            placeholder="e.g., Living Room Art, Family Photo"
          />
        </div>

        <!-- Frame Thickness -->
        <div class="mb-6">
          <label class="block text-sm text-gray-400 mb-1">Frame Thickness (inches)</label>
          <input
            v-model.number="frameThickness"
            type="number"
            min="0.25"
            max="5"
            step="0.25"
            class="w-full"
          />
        </div>

        <!-- Frame Color -->
        <div class="mb-6">
          <label class="block text-sm text-gray-400 mb-2">Frame Color</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="preset in presetColors"
              :key="preset.value"
              @click="frameColor = preset.value; showColorPicker = false"
              class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
              :class="frameColor === preset.value && !showColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span
                class="w-5 h-5 rounded-full border border-gray-500"
                :style="{ backgroundColor: preset.value }"
              ></span>
              <span class="text-sm">{{ preset.label }}</span>
            </button>
            <button
              @click="showColorPicker = !showColorPicker"
              class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
              :class="showColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span
                class="w-5 h-5 rounded-full border border-gray-500"
                :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }"
              ></span>
              <span class="text-sm">Custom</span>
            </button>
          </div>
          <div v-if="showColorPicker" class="mt-2">
            <input
              type="color"
              v-model="frameColor"
              class="w-full h-10 rounded cursor-pointer bg-transparent border border-gray-600"
            />
          </div>
        </div>

        <!-- Summary -->
        <div class="bg-dark-300 rounded-lg p-4 mb-6">
          <h4 class="font-semibold mb-2">Frame Details</h4>
          <p class="text-gray-400 text-sm">
            Total Size: {{ totalDimensions.width }} x {{ totalDimensions.height }} {{ dimensions.unit }}
          </p>
          <p class="text-gray-400 text-sm">
            Image: {{ dimensions.width }} x {{ dimensions.height }} {{ dimensions.unit }}
          </p>
          <p class="text-gray-400 text-sm">
            Frame: {{ frameThickness * 2 }} x {{ frameThickness * 2 }} {{ dimensions.unit }}
          </p>
          <p v-if="selectedWall" class="text-gray-400 text-sm">
            Wall: {{ selectedWall.name }}
          </p>
        </div>

        <div class="flex gap-4">
          <button @click="step = 2" class="btn btn-secondary flex-1">
            Edit Crop/Dimensions
          </button>
          <button
            @click="savePicture"
            :disabled="loading"
            class="btn btn-primary flex-1"
          >
            <span v-if="loading">Saving...</span>
            <span v-else>Save to Gallery</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
