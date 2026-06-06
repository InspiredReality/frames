<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'
import { getUploadUrl } from '@/services/api'
import FramePreview2D from '@/components/FramePreview2D.vue'
import ImageCropper from '@/components/ImageCropper.vue'

const router = useRouter()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()

const loading = ref(true)
const activeTab = ref('all')
const selectedFrame = ref(null)

const CM_PER_INCH = 2.54

// --- Edit/copy state ---
const editLoadingImage = ref(false)
const editImageDataUrl = ref(null)
const editCroppedData = ref(null)
const editDimensions = ref({ widthCm: 0, heightCm: 0, thicknessCm: 2.54, unit: 'in' })
const editColor = ref('#000000')
const editShowColorPicker = ref(false)
const editSaving = ref(false)
const editError = ref('')

const editPresetColors = [
  { label: 'None', value: null },
  { label: 'Black', value: '#000000' },
  { label: 'White', value: '#FFFFFF' },
  { label: 'Brown', value: '#8B4513' }
]

const editDisplayWidth = computed({
  get: () => {
    const cm = editDimensions.value.widthCm
    return editDimensions.value.unit === 'cm' ? +cm.toFixed(1) : +(cm / CM_PER_INCH).toFixed(2)
  },
  set: (val) => {
    editDimensions.value.widthCm = editDimensions.value.unit === 'cm' ? val : val * CM_PER_INCH
  }
})

const editDisplayHeight = computed({
  get: () => {
    const cm = editDimensions.value.heightCm
    return editDimensions.value.unit === 'cm' ? +cm.toFixed(1) : +(cm / CM_PER_INCH).toFixed(2)
  },
  set: (val) => {
    editDimensions.value.heightCm = editDimensions.value.unit === 'cm' ? val : val * CM_PER_INCH
  }
})

const editDisplayThickness = computed({
  get: () => {
    const cm = editDimensions.value.thicknessCm
    return editDimensions.value.unit === 'cm' ? +cm.toFixed(1) : +(cm / CM_PER_INCH).toFixed(2)
  },
  set: (val) => {
    editDimensions.value.thicknessCm = editDimensions.value.unit === 'cm' ? val : val * CM_PER_INCH
  }
})

const editAspectRatio = computed(() => {
  const w = editDimensions.value.widthCm
  const h = editDimensions.value.heightCm
  return w && h ? w / h : null
})

// Load image + init edit state whenever a frame is selected
watch(selectedFrame, async (frame) => {
  editImageDataUrl.value = null
  editCroppedData.value = null
  editError.value = ''
  editShowColorPicker.value = false

  if (!frame) return

  const frameData = frame.frames?.[0]
  editDimensions.value = {
    widthCm: frameData?.dimensions?.cm?.width || 0,
    heightCm: frameData?.dimensions?.cm?.height || 0,
    thicknessCm: (frameData?.styling?.frame_thickness ?? 1) * CM_PER_INCH,
    unit: 'in'
  }
  editColor.value = frameData?.styling?.frame_color || '#000000'

  const imageUrl = frame.image_path ? getUploadUrl(frame.image_path) : null
  if (!imageUrl) return

  editLoadingImage.value = true
  try {
    const resp = await fetch(imageUrl)
    const blob = await resp.blob()
    editImageDataUrl.value = await new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target.result)
      reader.readAsDataURL(blob)
    })
  } catch {
    editImageDataUrl.value = imageUrl // fallback to direct URL
  } finally {
    editLoadingImage.value = false
  }
})

const getIteratedName = (name) => {
  const match = (name || 'Frame').trim().match(/^(.*)\s+\((\d+)\)$/)
  if (match) return `${match[1]} (${parseInt(match[2]) + 1})`
  return `${name} (2)`
}

const saveEditedCopy = async () => {
  if (!editCroppedData.value?.blob) {
    editError.value = 'Image not ready — wait a moment and try again'
    return
  }

  editSaving.value = true
  editError.value = ''

  try {
    const iteratedName = getIteratedName(selectedFrame.value?.name || 'Frame')
    const file = new File([editCroppedData.value.blob], 'frame.jpg', { type: 'image/jpeg' })
    const picture = await picturesStore.uploadPicture(file, iteratedName)

    await picturesStore.createFrame(picture.id, {
      width: editDimensions.value.widthCm / CM_PER_INCH,
      height: editDimensions.value.heightCm / CM_PER_INCH,
      depth: 1,
      unit: 'inches',
      frame_color: editColor.value,
      frame_thickness: editDimensions.value.thicknessCm / CM_PER_INCH,
    })

    selectedFrame.value = null
    await picturesStore.fetchPublicPictures()
  } catch (err) {
    const d = err.response?.data
    editError.value = d?.error || (typeof d?.detail === 'string' ? d.detail : null) || 'Failed to save copy'
  } finally {
    editSaving.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      wallsStore.fetchPublicWalls(),
      picturesStore.fetchPublicPictures()
    ])
  } finally {
    loading.value = false
  }
})

const filteredItems = computed(() => {
  if (activeTab.value === 'walls') return { walls: wallsStore.publicWalls, frames: [] }
  if (activeTab.value === 'frames') return { walls: [], frames: picturesStore.publicPictures }
  return { walls: wallsStore.publicWalls, frames: picturesStore.publicPictures }
})

const getImageUrl = (path) => getUploadUrl(path)

const navigateToWall = (wall) => {
  router.push(`/wall/${wall.id}`)
}

const getFrameDimensions = (picture) => {
  const frame = picture.frames?.[0]
  if (!frame) return {}
  return {
    widthCm: frame.dimensions?.cm?.width,
    heightCm: frame.dimensions?.cm?.height,
    frameColor: frame.styling?.frame_color || '#8B4513',
    frameThickness: frame.styling?.frame_thickness ?? 1
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold whitespace-nowrap">Public Gallery</h1>
      <p class="text-gray-400 text-sm">Walls and frames shared by the community</p>
    </div>

    <!-- Guest capture strip -->
    <div class="flex flex-col gap-3 mb-6 p-3 bg-dark-300 rounded-lg border border-gray-700">
      <span class="text-sm text-gray-400">Try it free — no account needed:</span>
      <div class="flex gap-2">
        <router-link to="/capture/wall" class="btn btn-secondary text-sm py-1.5 px-3">
          Capture Wall
        </router-link>
        <router-link to="/capture/frame" class="btn btn-secondary text-sm py-1.5 px-3">
          Capture Frame
        </router-link>
      </div>
      <p class="text-sm text-gray-400">Create account to save private Walls &amp; Frames.</p>
      <div class="flex gap-2">
        <router-link to="/register" class="btn btn-primary text-sm py-1.5 px-3">
          Create Account
        </router-link>
        <router-link to="/login" class="btn btn-secondary">
          Login
        </router-link>
      </div>
    </div>

    <!-- Tab filters -->
    <div class="flex gap-2 mb-6">
      <button
        @click="activeTab = 'all'"
        class="px-4 py-2 rounded-lg transition"
        :class="activeTab === 'all' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
      >
        All
      </button>
      <button
        @click="activeTab = 'walls'"
        class="px-4 py-2 rounded-lg transition"
        :class="activeTab === 'walls' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
      >
        Walls ({{ wallsStore.publicWalls.length }})
      </button>
      <button
        @click="activeTab = 'frames'"
        class="px-4 py-2 rounded-lg transition"
        :class="activeTab === 'frames' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
      >
        Frames ({{ picturesStore.publicPictures.length }})
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <div v-else-if="!filteredItems.walls.length && !filteredItems.frames.length" class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="text-xl font-semibold mb-2">Nothing public yet</h3>
      <p class="text-gray-400 mb-6">Be the first to share a wall or frame with the community.</p>
      <router-link to="/register" class="btn btn-primary">Create Account</router-link>
    </div>

    <div v-else class="space-y-8">
      <!-- Walls -->
      <div v-if="filteredItems.walls.length > 0">
        <h2 v-if="activeTab === 'all'" class="text-lg font-semibold mb-4 text-gray-300">Walls</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="wall in filteredItems.walls"
            :key="wall.id"
            @click="navigateToWall(wall)"
            class="card p-3 border border-transparent hover:border-primary-500/50 transition-colors cursor-pointer"
          >
            <div class="aspect-video bg-dark-300 rounded-lg overflow-hidden mb-3">
              <img
                :src="getImageUrl(wall.thumbnail_path || wall.image_path)"
                :alt="wall.name"
                class="w-full h-full object-cover"
              />
            </div>
            <h3 class="font-medium mb-1">{{ wall.name }}</h3>
            <p class="text-sm text-gray-400">
              {{ wall.frame_placements?.length || 0 }} frame(s)
            </p>
          </div>
        </div>
      </div>

      <!-- Frames -->
      <div v-if="filteredItems.frames.length > 0">
        <h2 v-if="activeTab === 'all'" class="text-lg font-semibold mb-4 text-gray-300">Frames</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div
            v-for="frame in filteredItems.frames"
            :key="frame.id"
            @click="selectedFrame = frame"
            class="card p-2 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
          >
            <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden mb-2">
              <img
                :src="getImageUrl(frame.thumbnail_path || frame.image_path)"
                :alt="frame.name"
                class="w-full h-full object-cover"
              />
            </div>
            <h3 class="font-medium truncate text-sm">{{ frame.name }}</h3>
          </div>
        </div>
      </div>
    </div>

    <!-- Frame edit/copy modal -->
    <div
      v-if="selectedFrame"
      class="fixed inset-0 bg-black/70 flex items-start justify-center p-4 z-50 overflow-y-auto"
      @click.self="selectedFrame = null"
    >
      <div class="card max-w-md w-full my-4">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-xl font-bold">{{ selectedFrame.name }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">Saving as: <span class="text-primary-400">{{ getIteratedName(selectedFrame.name) }}</span></p>
          </div>
          <button @click="selectedFrame = null" class="text-gray-400 hover:text-white flex-shrink-0 ml-2">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Image / Cropper -->
        <div class="mb-4">
          <div v-if="editLoadingImage" class="flex justify-center items-center bg-dark-300 rounded-lg h-48">
            <div class="spinner"></div>
          </div>
          <ImageCropper
            v-else-if="editImageDataUrl"
            :imageUrl="editImageDataUrl"
            :aspectRatio="editAspectRatio"
            @crop="editCroppedData = $event"
          />
          <div v-else class="flex justify-center bg-dark-300 rounded-lg p-4">
            <FramePreview2D
              v-if="selectedFrame.frames?.length"
              :imageUrl="getImageUrl(selectedFrame.image_path)"
              :widthCm="getFrameDimensions(selectedFrame).widthCm"
              :heightCm="getFrameDimensions(selectedFrame).heightCm"
              :frameColor="getFrameDimensions(selectedFrame).frameColor"
              :frameThickness="getFrameDimensions(selectedFrame).frameThickness"
              :maxWidth="300"
              :maxHeight="240"
            />
            <img v-else :src="getImageUrl(selectedFrame.image_path)" class="max-w-full max-h-48 rounded-lg" />
          </div>
        </div>

        <!-- Dimensions -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm text-gray-400">Dimensions</label>
            <div class="flex rounded-lg overflow-hidden border border-gray-600 text-xs">
              <button
                @click="editDimensions.unit = 'in'"
                class="px-2 py-1 transition"
                :class="editDimensions.unit === 'in' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400'"
              >in</button>
              <button
                @click="editDimensions.unit = 'cm'"
                class="px-2 py-1 transition"
                :class="editDimensions.unit === 'cm' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400'"
              >cm</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs text-gray-500 mb-1">Width</label>
              <input
                v-model.number="editDisplayWidth"
                type="number"
                min="0.1"
                step="0.1"
                class="w-full px-2 py-1.5 bg-dark-100 border border-gray-600 rounded text-sm"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Height</label>
              <input
                v-model.number="editDisplayHeight"
                type="number"
                min="0.1"
                step="0.1"
                class="w-full px-2 py-1.5 bg-dark-100 border border-gray-600 rounded text-sm"
              />
            </div>
          </div>
        </div>

        <!-- Frame Thickness -->
        <div class="mb-4">
          <label class="block text-sm text-gray-400 mb-1">
            Frame Thickness ({{ editDimensions.unit === 'cm' ? 'cm' : 'in' }})
          </label>
          <input
            v-model.number="editDisplayThickness"
            type="number"
            min="0"
            :max="editDimensions.unit === 'cm' ? 12.7 : 5"
            :step="editDimensions.unit === 'cm' ? 0.1 : 0.25"
            class="w-full px-2 py-1.5 bg-dark-100 border border-gray-600 rounded text-sm"
          />
        </div>

        <!-- Frame Color -->
        <div class="mb-5">
          <label class="block text-sm text-gray-400 mb-2">Frame Color</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="preset in editPresetColors"
              :key="String(preset.value)"
              @click="editColor = preset.value; editShowColorPicker = false"
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border-2 transition text-sm"
              :class="editColor === preset.value && !editShowColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span
                v-if="preset.value"
                class="w-4 h-4 rounded-full border border-gray-500"
                :style="{ backgroundColor: preset.value }"
              ></span>
              <span
                v-else
                class="w-4 h-4 rounded-full border border-gray-500 overflow-hidden"
                style="background: linear-gradient(135deg, transparent 45%, #6b7280 45%, #6b7280 55%, transparent 55%)"
              ></span>
              {{ preset.label }}
            </button>
            <button
              @click="editShowColorPicker = !editShowColorPicker"
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border-2 transition text-sm"
              :class="editShowColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
            >
              <span class="w-4 h-4 rounded-full border border-gray-500" style="background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red)"></span>
              Custom
            </button>
          </div>
          <div v-if="editShowColorPicker" class="mt-2">
            <input
              type="color"
              v-model="editColor"
              class="w-full h-10 rounded cursor-pointer bg-transparent border border-gray-600"
            />
          </div>
        </div>

        <!-- Error -->
        <div v-if="editError" class="mb-3 p-2 bg-red-500/20 border border-red-500 rounded text-red-400 text-sm">
          {{ editError }}
        </div>

        <!-- Save button -->
        <button
          @click="saveEditedCopy"
          :disabled="editSaving || editLoadingImage || !editCroppedData?.blob"
          class="btn btn-primary w-full"
        >
          <span v-if="editSaving">Saving…</span>
          <span v-else-if="editLoadingImage">Loading image…</span>
          <span v-else>Save as "{{ getIteratedName(selectedFrame.name) }}"</span>
        </button>
      </div>
    </div>

  </div>
</template>
