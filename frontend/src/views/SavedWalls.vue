<script setup>
import { ref, onMounted } from 'vue'
import { useWallsStore } from '@/store/walls'
import { getUploadUrl } from '@/services/api'

const wallsStore = useWallsStore()
const loading = ref(true)

onMounted(async () => {
  try {
    await wallsStore.fetchWalls()
  } finally {
    loading.value = false
  }
})

const deleteWall = async (wallId) => {
  if (!confirm('Are you sure you want to delete this wall?')) {
    return
  }

  try {
    await wallsStore.deleteWall(wallId)
  } catch (err) {
    alert('Failed to delete wall')
  }
}

const getImageUrl = (path) => {
  return getUploadUrl(path)
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">My Walls</h1>
      <router-link to="/capture/wall" class="btn btn-primary">
        Add Wall
      </router-link>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="wallsStore.walls.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
      <h3 class="text-xl font-semibold mb-2">No walls saved</h3>
      <p class="text-gray-400 mb-4">Capture a wall to start placing your frames</p>
      <router-link to="/capture/wall" class="btn btn-primary">
        Capture Wall
      </router-link>
    </div>

    <!-- Walls grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="wall in wallsStore.walls"
        :key="wall.id"
        class="card"
      >
        <div class="aspect-video bg-dark-300 rounded-lg overflow-hidden mb-3">
          <img
            :src="getImageUrl(wall.thumbnail_path || wall.image_path)"
            :alt="wall.name"
            class="w-full h-full object-cover"
          />
        </div>

        <h3 class="font-semibold text-lg mb-1">{{ wall.name }}</h3>
        <p v-if="wall.description" class="text-sm text-gray-400 mb-2 line-clamp-2">
          {{ wall.description }}
        </p>

        <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
          <span v-if="wall.width_cm && wall.height_cm">
            {{ wall.width_cm }} x {{ wall.height_cm }} cm
          </span>
          <span v-else>Dimensions not set</span>
          <span>{{ wall.frame_placements?.length || 0 }} frames</span>
        </div>

        <div class="flex gap-2">
          <router-link
            :to="`/wall/${wall.id}`"
            class="btn btn-primary flex-1 text-center"
          >
            Edit
          </router-link>
          <router-link
            :to="`/ar/${wall.id}`"
            class="btn btn-secondary"
          >
            AR View
          </router-link>
          <button
            @click="deleteWall(wall.id)"
            class="btn bg-red-600/20 text-red-400 hover:bg-red-600 hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
