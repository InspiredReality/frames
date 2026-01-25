<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WallViewer from '@/components/WallViewer.vue'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'
import { getUploadUrl } from '@/services/api'

const route = useRoute()
const router = useRouter()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const showFramePicker = ref(false)

onMounted(async () => {
  try {
    await Promise.all([
      wallsStore.fetchWall(parseInt(route.params.id)),
      picturesStore.fetchPictures()
    ])
  } catch (err) {
    error.value = 'Failed to load wall'
  } finally {
    loading.value = false
  }
})

const wall = computed(() => wallsStore.currentWall)

const allFrames = computed(() => {
  const frames = []
  picturesStore.pictures.forEach(picture => {
    if (picture.frames) {
      picture.frames.forEach(frame => {
        frames.push({
          ...frame,
          pictureName: picture.name,
          pictureImage: picture.thumbnail_path || picture.image_path
        })
      })
    }
  })
  return frames
})

const addFrame = async (frame) => {
  try {
    saving.value = true
    await wallsStore.addFramePlacement(wall.value.id, {
      frame_id: frame.id,
      position: { x: 0, y: 0, z: 0.05 },
      rotation: { x: 0, y: 0, z: 0 },
      scale: 1.0
    })
    showFramePicker.value = false
  } catch (err) {
    error.value = 'Failed to add frame'
  } finally {
    saving.value = false
  }
}

const removeFrame = async (placementIndex) => {
  if (!confirm('Remove this frame from the wall?')) return

  try {
    saving.value = true
    const placements = [...(wall.value.frame_placements || [])]
    placements.splice(placementIndex, 1)
    await wallsStore.updateWall(wall.value.id, { frame_placements: placements })
  } catch (err) {
    error.value = 'Failed to remove frame'
  } finally {
    saving.value = false
  }
}

const getImageUrl = (path) => getUploadUrl(path)
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-400 mb-4">{{ error }}</p>
      <button @click="router.back()" class="btn btn-secondary">Go Back</button>
    </div>

    <!-- Editor -->
    <div v-else-if="wall">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">{{ wall.name }}</h1>
          <p class="text-gray-400">Edit frame placements</p>
        </div>
        <div class="flex gap-3">
          <button @click="showFramePicker = true" class="btn btn-primary">
            Add Frame
          </button>
          <router-link :to="`/ar/${wall.id}`" class="btn btn-secondary">
            AR View
          </router-link>
        </div>
      </div>

      <!-- 3D Wall Viewer -->
      <div class="card mb-6">
        <WallViewer
          :wallImageUrl="getImageUrl(wall.image_path)"
          :framePlacements="wall.frame_placements || []"
          :frames="allFrames"
        />
      </div>

      <!-- Placed frames list -->
      <div class="card">
        <h3 class="font-semibold mb-4">Placed Frames ({{ wall.frame_placements?.length || 0 }})</h3>

        <div v-if="!wall.frame_placements?.length" class="text-center py-6 text-gray-400">
          No frames placed yet. Click "Add Frame" to start.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="(placement, index) in wall.frame_placements"
            :key="index"
            class="flex items-center justify-between bg-dark-300 rounded-lg p-3"
          >
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-dark-100 rounded overflow-hidden">
                <img
                  v-if="allFrames.find(f => f.id === placement.frame_id)?.pictureImage"
                  :src="getImageUrl(allFrames.find(f => f.id === placement.frame_id).pictureImage)"
                  class="w-full h-full object-cover"
                />
              </div>
              <div>
                <p class="font-medium">
                  {{ allFrames.find(f => f.id === placement.frame_id)?.pictureName || 'Unknown' }}
                </p>
                <p class="text-sm text-gray-400">
                  Position: ({{ placement.position?.x?.toFixed(2) }}, {{ placement.position?.y?.toFixed(2) }})
                </p>
              </div>
            </div>
            <button
              @click="removeFrame(index)"
              class="text-red-400 hover:text-red-300"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Frame picker modal -->
    <div
      v-if="showFramePicker"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="showFramePicker = false"
    >
      <div class="card max-w-lg w-full max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">Select a Frame</h2>
          <button @click="showFramePicker = false" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="allFrames.length === 0" class="text-center py-6">
          <p class="text-gray-400 mb-4">No frames available. Create some pictures first.</p>
          <router-link to="/capture/frame" class="btn btn-primary">
            Capture Frame
          </router-link>
        </div>

        <div v-else class="grid grid-cols-2 gap-3">
          <button
            v-for="frame in allFrames"
            :key="frame.id"
            @click="addFrame(frame)"
            :disabled="saving"
            class="bg-dark-300 rounded-lg p-2 hover:ring-2 hover:ring-primary-500 transition text-left"
          >
            <div class="aspect-square bg-dark-100 rounded overflow-hidden mb-2">
              <img
                :src="getImageUrl(frame.pictureImage)"
                :alt="frame.pictureName"
                class="w-full h-full object-cover"
              />
            </div>
            <p class="font-medium truncate text-sm">{{ frame.pictureName }}</p>
            <p class="text-xs text-gray-400">
              {{ frame.dimensions?.inches?.width }}" x {{ frame.dimensions?.inches?.height }}"
            </p>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
