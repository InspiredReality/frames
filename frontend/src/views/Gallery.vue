<script setup>
import { ref, onMounted } from 'vue'
import { usePicturesStore } from '@/store/pictures'
import { getUploadUrl } from '@/services/api'

const picturesStore = usePicturesStore()
const loading = ref(true)
const selectedPicture = ref(null)

onMounted(async () => {
  try {
    await picturesStore.fetchPictures()
  } finally {
    loading.value = false
  }
})

const openDetails = (picture) => {
  selectedPicture.value = picture
}

const closeDetails = () => {
  selectedPicture.value = null
}

const deletePicture = async (pictureId) => {
  if (!confirm('Are you sure you want to delete this picture and all its frames?')) {
    return
  }

  try {
    await picturesStore.deletePicture(pictureId)
    selectedPicture.value = null
  } catch (err) {
    alert('Failed to delete picture')
  }
}

const getImageUrl = (path) => {
  return getUploadUrl(path)
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">My Gallery</h1>
      <router-link to="/capture/frame" class="btn btn-primary">
        Add Picture
      </router-link>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="picturesStore.pictures.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <h3 class="text-xl font-semibold mb-2">No pictures yet</h3>
      <p class="text-gray-400 mb-4">Capture your first picture frame to get started</p>
      <router-link to="/capture/frame" class="btn btn-primary">
        Capture Frame
      </router-link>
    </div>

    <!-- Pictures grid -->
    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div
        v-for="picture in picturesStore.pictures"
        :key="picture.id"
        @click="openDetails(picture)"
        class="card p-2 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
      >
        <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden mb-2">
          <img
            :src="getImageUrl(picture.thumbnail_path || picture.image_path)"
            :alt="picture.name"
            class="w-full h-full object-cover"
          />
        </div>
        <h3 class="font-medium truncate">{{ picture.name }}</h3>
        <p class="text-sm text-gray-400">
          {{ picture.frames?.length || 0 }} frame(s)
        </p>
      </div>
    </div>

    <!-- Picture details modal -->
    <div
      v-if="selectedPicture"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="closeDetails"
    >
      <div class="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">{{ selectedPicture.name }}</h2>
          <button @click="closeDetails" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <img
          :src="getImageUrl(selectedPicture.image_path)"
          :alt="selectedPicture.name"
          class="w-full rounded-lg mb-4"
        />

        <div v-if="selectedPicture.frames?.length" class="mb-4">
          <h3 class="font-semibold mb-2">Frames</h3>
          <div class="space-y-2">
            <div
              v-for="frame in selectedPicture.frames"
              :key="frame.id"
              class="bg-dark-300 rounded-lg p-3"
            >
              <p class="text-sm">
                {{ frame.dimensions?.inches?.width }}" x {{ frame.dimensions?.inches?.height }}"
                ({{ frame.dimensions?.cm?.width?.toFixed(1) }} x {{ frame.dimensions?.cm?.height?.toFixed(1) }} cm)
              </p>
            </div>
          </div>
        </div>

        <div class="flex gap-3">
          <router-link
            :to="`/walls?frame=${selectedPicture.frames?.[0]?.id}`"
            class="btn btn-primary flex-1"
            v-if="selectedPicture.frames?.length"
          >
            Place on Wall
          </router-link>
          <button
            @click="deletePicture(selectedPicture.id)"
            class="btn bg-red-600 hover:bg-red-700 text-white"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
