<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import DimensionInput from '@/components/DimensionInput.vue'
import FramePreview from '@/components/FramePreview.vue'
import { usePicturesStore } from '@/store/pictures'

const router = useRouter()
const picturesStore = usePicturesStore()

const step = ref(1) // 1: capture, 2: dimensions, 3: preview
const capturedImage = ref(null)
const dimensions = ref({ width: '', height: '', depth: 1, unit: 'inches' })
const pictureName = ref('')
const loading = ref(false)
const error = ref('')

const cameraRef = ref(null)

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

const goToPreview = () => {
  if (!dimensions.value.width || !dimensions.value.height) {
    error.value = 'Please enter frame dimensions'
    return
  }
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
    // Upload the picture
    const file = new File([capturedImage.value.blob], 'frame.jpg', { type: 'image/jpeg' })
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

    <!-- Step 1: Camera Capture -->
    <div v-if="step === 1">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Picture Frame</h2>
      <p class="text-gray-400 text-center mb-6">
        Take a clear photo of the picture or artwork you want to frame
      </p>
      <CameraCapture ref="cameraRef" @capture="onCapture" @error="onCameraError" />
    </div>

    <!-- Step 2: Dimensions -->
    <div v-if="step === 2" class="card">
      <h2 class="text-2xl font-bold mb-4">Set Frame Dimensions</h2>

      <!-- Preview of captured image -->
      <div class="mb-6">
        <img
          :src="capturedImage.dataUrl"
          alt="Captured frame"
          class="w-full max-h-64 object-contain rounded-lg bg-dark-300"
        />
      </div>

      <DimensionInput v-model="dimensions" />

      <div class="flex gap-4 mt-6">
        <button @click="retake" class="btn btn-secondary flex-1">
          Retake Photo
        </button>
        <button @click="goToPreview" class="btn btn-primary flex-1">
          Preview 3D Frame
        </button>
      </div>
    </div>

    <!-- Step 3: Preview and Save -->
    <div v-if="step === 3" class="card">
      <h2 class="text-2xl font-bold mb-4">Preview & Save</h2>

      <!-- 3D Preview -->
      <div class="mb-6">
        <FramePreview
          :imageUrl="capturedImage.dataUrl"
          :dimensions="{
            width: parseFloat(dimensions.width) || 10,
            height: parseFloat(dimensions.height) || 8,
            depth: parseFloat(dimensions.depth) || 1
          }"
        />
        <p class="text-sm text-gray-400 text-center mt-2">
          Drag to rotate the 3D preview
        </p>
      </div>

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
      </div>

      <div class="flex gap-4">
        <button @click="step = 2" class="btn btn-secondary flex-1">
          Edit Dimensions
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
</template>
