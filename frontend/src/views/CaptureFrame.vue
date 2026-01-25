<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import DimensionInput from '@/components/DimensionInput.vue'
import FramePreview from '@/components/FramePreview.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import { usePicturesStore } from '@/store/pictures'

const router = useRouter()
const picturesStore = usePicturesStore()

const step = ref(1) // 1: capture, 2: crop & dimensions, 3: preview
const capturedImage = ref(null)
const croppedImage = ref(null)
const dimensions = ref({ width: '', height: '', depth: 1, unit: 'inches', orientation: 'portrait' })
const pictureName = ref('')
const loading = ref(false)
const error = ref('')

const cameraRef = ref(null)
const cropperRef = ref(null)

// Calculate aspect ratio from dimensions if both are set
const aspectRatio = computed(() => {
  if (dimensions.value.width && dimensions.value.height) {
    return parseFloat(dimensions.value.width) / parseFloat(dimensions.value.height)
  }
  return null
})

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
    error.value = 'Please enter a name for your picture'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Upload the cropped picture
    const file = new File([croppedImage.value.blob], 'frame.jpg', { type: 'image/jpeg' })
    const picture = await picturesStore.uploadPicture(file, pictureName.value)

    // Create the frame with dimensions
    await picturesStore.createFrame(picture.id, {
      width: parseFloat(dimensions.value.width),
      height: parseFloat(dimensions.value.height),
      depth: parseFloat(dimensions.value.depth) || 1,
      unit: dimensions.value.unit
    })

    router.push('/gallery')
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save picture'
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
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Picture Frame</h2>
      <p class="text-gray-400 text-center mb-6">
        Take a clear photo of the picture or artwork you want to frame
      </p>
      <CameraCapture ref="cameraRef" @capture="onCapture" @error="onCameraError" />
    </div>

    <!-- Step 2: Crop & Dimensions - Two Column Layout -->
    <div v-if="step === 2">
      <h2 class="text-2xl font-bold mb-6 text-center">Crop & Set Dimensions</h2>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Left Column: Original Image with Crop Tool -->
        <div class="card">
          <h3 class="font-semibold mb-3 flex items-center gap-2">
            <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">1</span>
            Crop Your Image
          </h3>
          <p class="text-sm text-gray-400 mb-4">
            Drag the corners or edges to select the area you want to keep
          </p>
          <ImageCropper
            ref="cropperRef"
            :imageUrl="capturedImage.dataUrl"
            :aspectRatio="aspectRatio"
            @crop="onCrop"
          />
        </div>

        <!-- Right Column: Cropped Preview + Dimensions -->
        <div class="space-y-4">
          <!-- Cropped Preview -->
          <div class="card">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">2</span>
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

          <!-- Dimensions Input -->
          <div class="card">
            <h3 class="font-semibold mb-3 flex items-center gap-2">
              <span class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-xs">3</span>
              Frame Dimensions
            </h3>
            <p class="text-sm text-gray-400 mb-4">
              Enter the real-world size of your picture frame
            </p>
            <DimensionInput v-model="dimensions" />
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
          <div>
            <h4 class="text-sm text-gray-400 mb-2">Your Picture</h4>
            <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden flex items-center justify-center">
              <img
                :src="croppedImage.dataUrl"
                alt="Cropped picture"
                class="max-w-full max-h-full object-contain"
              />
            </div>
          </div>

          <!-- 3D Preview -->
          <div>
            <h4 class="text-sm text-gray-400 mb-2">3D Frame Preview</h4>
            <FramePreview
              :imageUrl="croppedImage.dataUrl"
              :dimensions="{
                width: parseFloat(dimensions.width) || 10,
                height: parseFloat(dimensions.height) || 8,
                depth: parseFloat(dimensions.depth) || 1
              }"
            />
          </div>
        </div>

        <p class="text-sm text-gray-400 text-center mb-4">
          Drag to rotate the 3D preview
        </p>

        <!-- Name input -->
        <div class="mb-6">
          <label class="block text-sm text-gray-400 mb-1">Picture Name</label>
          <input
            v-model="pictureName"
            type="text"
            placeholder="e.g., Living Room Art, Family Photo"
          />
        </div>

        <!-- Summary -->
        <div class="bg-dark-300 rounded-lg p-4 mb-6">
          <h4 class="font-semibold mb-2">Frame Details</h4>
          <p class="text-gray-400 text-sm">
            Size: {{ dimensions.width }} x {{ dimensions.height }} {{ dimensions.unit }}
          </p>
          <p class="text-gray-400 text-sm">
            Depth: {{ dimensions.depth }} {{ dimensions.unit }}
          </p>
          <p class="text-gray-400 text-sm">
            Image: {{ croppedImage?.width }} x {{ croppedImage?.height }} px
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
