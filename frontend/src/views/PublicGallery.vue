<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'
import { getUploadUrl } from '@/services/api'
import FramePreview2D from '@/components/FramePreview2D.vue'

const router = useRouter()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()

const loading = ref(true)
const activeTab = ref('all') // 'all', 'walls', 'frames'
const selectedFrame = ref(null)

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

const getFrameDimensions = (picture) => {
  const frame = picture.frames?.[0]
  if (!frame) return {}
  return {
    widthCm: frame.dimensions?.cm?.width,
    heightCm: frame.dimensions?.cm?.height,
    frameColor: frame.styling?.frame_color || '#8B4513',
    frameThickness: frame.styling?.frame_thickness || 1
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <div class="flex items-start justify-between mb-4 gap-4">
      <div>
        <h1 class="text-2xl font-bold">Public Gallery</h1>
        <p class="text-gray-400 text-sm">Walls and frames shared by the community</p>
      </div>
      <div class="flex gap-2 flex-shrink-0">
        <router-link to="/register" class="btn btn-primary text-sm">
          Create Account
        </router-link>
        <router-link to="/login" class="btn btn-secondary text-sm">
          Sign In
        </router-link>
      </div>
    </div>

    <!-- Guest capture strip -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-6 p-3 bg-dark-300 rounded-lg border border-gray-700">
      <span class="text-sm text-gray-400">Try it free — no account needed:</span>
      <div class="flex gap-2">
        <router-link to="/capture/wall" class="btn btn-secondary text-sm py-1.5 px-3">
          Capture Wall
        </router-link>
        <router-link to="/capture/frame" class="btn btn-secondary text-sm py-1.5 px-3">
          Capture Frame
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
            class="card p-3 border border-transparent hover:border-primary-500/50 transition-colors"
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

    <!-- Frame preview modal -->
    <div
      v-if="selectedFrame"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="selectedFrame = null"
    >
      <div class="card max-w-sm w-full">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">{{ selectedFrame.name }}</h2>
          <button @click="selectedFrame = null" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex justify-center bg-dark-300 rounded-lg p-4 mb-4">
          <FramePreview2D
            v-if="selectedFrame.frames?.length"
            :imageUrl="getImageUrl(selectedFrame.image_path)"
            :widthCm="getFrameDimensions(selectedFrame).widthCm"
            :heightCm="getFrameDimensions(selectedFrame).heightCm"
            :frameColor="getFrameDimensions(selectedFrame).frameColor"
            :frameThickness="getFrameDimensions(selectedFrame).frameThickness"
            :maxWidth="300"
            :maxHeight="300"
          />
          <img v-else :src="getImageUrl(selectedFrame.image_path)" class="max-w-full max-h-64 rounded-lg" />
        </div>
        <router-link to="/register" class="btn btn-primary w-full text-center block">
          Create Account to Use This Frame
        </router-link>
      </div>
    </div>
  </div>
</template>
