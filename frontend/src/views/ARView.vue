<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UnityScene from '@/components/UnityScene.vue'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'

const route = useRoute()
const router = useRouter()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()

const loading = ref(true)
const error = ref('')
const unityRef = ref(null)

onMounted(async () => {
  try {
    if (route.params.wallId) {
      await wallsStore.fetchWall(parseInt(route.params.wallId))
    }
    await picturesStore.fetchPictures()
  } catch (err) {
    error.value = 'Failed to load data'
  } finally {
    loading.value = false
  }
})

const wall = computed(() => wallsStore.currentWall)

const sceneData = computed(() => {
  if (!wall.value) return {}

  return {
    wallId: wall.value.id,
    wallImage: wall.value.image_path,
    wallDimensions: {
      width: wall.value.width_cm || 300,
      height: wall.value.height_cm || 250
    },
    framePlacements: wall.value.frame_placements || []
  }
})

const onUnityLoaded = (instance) => {
  console.log('Unity loaded')
}

const onUnityError = (err) => {
  console.error('Unity error:', err)
}

const onUnityMessage = (data) => {
  console.log('Message from Unity:', data)

  // Handle different message types from Unity
  if (data.type === 'frameMoved') {
    // Update frame position in the backend
    // This would be called when a user drags a frame in AR
  }
}
</script>

<template>
  <div class="h-[calc(100vh-8rem)]">
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center h-full">
      <div class="spinner"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex flex-col items-center justify-center h-full">
      <p class="text-red-400 mb-4">{{ error }}</p>
      <button @click="router.back()" class="btn btn-secondary">Go Back</button>
    </div>

    <!-- AR View -->
    <div v-else class="h-full flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-xl font-bold">AR View</h1>
          <p class="text-sm text-gray-400" v-if="wall">{{ wall.name }}</p>
        </div>
        <button @click="router.back()" class="btn btn-secondary">
          Exit AR
        </button>
      </div>

      <!-- Unity WebXR Scene -->
      <div class="flex-1 rounded-lg overflow-hidden">
        <UnityScene
          ref="unityRef"
          :sceneData="sceneData"
          @loaded="onUnityLoaded"
          @error="onUnityError"
          @message="onUnityMessage"
        />
      </div>

      <!-- AR Controls (shown when Unity is not available) -->
      <div class="mt-4 card">
        <h3 class="font-semibold mb-2">AR Controls</h3>
        <p class="text-sm text-gray-400 mb-4">
          To enable full AR features, build your Unity WebXR project and place it in the /public/unity/ folder.
        </p>
        <div class="flex gap-2">
          <button class="btn btn-secondary flex-1" disabled>
            Start AR Session
          </button>
          <button class="btn btn-secondary flex-1" disabled>
            Take Screenshot
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
