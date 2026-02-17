<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { usePicturesStore } from '@/store/pictures'
import { useWallsStore } from '@/store/walls'
import { getUploadUrl } from '@/services/api'
import FramePreview2D from '@/components/FramePreview2D.vue'
import ImageCropper from '@/components/ImageCropper.vue'

const picturesStore = usePicturesStore()
const wallsStore = useWallsStore()
const loading = ref(true)
const selectedFrame = ref(null)
const selectedWall = ref(null)
const activeTab = ref('all') // 'all', 'walls', 'frames'
const assigningWall = ref(false)

// Dimension editing state
const editingFrameDimensions = ref(false)
const editingWallDimensions = ref(false)
const frameDimensionEdit = ref({ width: 0, height: 0, unit: 'cm' })
const wallDimensionEdit = ref({ width: 0, height: 0 })
const savingDimensions = ref(false)

// Recrop state
const showRecropModal = ref(false)
const recropImageUrl = ref('')
const recropAspectRatio = ref(null)
const lockAspectRatio = ref(true)
const croppedImage = ref(null)
const savingRecrop = ref(false)

// Computed aspect ratio that respects lock toggle
const effectiveAspectRatio = computed(() => {
  return lockAspectRatio.value ? recropAspectRatio.value : null
})

// Lock body scroll when any modal is open (prevents background scrolling on mobile)
const isAnyModalOpen = computed(() => {
  return !!(selectedFrame.value || selectedWall.value || showRecropModal.value)
})

watch(isAnyModalOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onMounted(async () => {
  try {
    await Promise.all([
      picturesStore.fetchPictures(),
      wallsStore.fetchWalls()
    ])
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
})

const filteredItems = computed(() => {
  if (activeTab.value === 'walls') {
    return { walls: wallsStore.walls, frames: [] }
  }
  if (activeTab.value === 'frames') {
    return { walls: [], frames: picturesStore.pictures }
  }
  return { walls: wallsStore.walls, frames: picturesStore.pictures }
})

const hasContent = computed(() => {
  return wallsStore.walls.length > 0 || picturesStore.pictures.length > 0
})

const openFrameDetails = (frame) => {
  selectedFrame.value = frame
  selectedWall.value = null
}

const openWallDetails = (wall) => {
  selectedWall.value = wall
  selectedFrame.value = null
}

const closeModal = () => {
  selectedFrame.value = null
  selectedWall.value = null
}

const deleteFrame = async (frameId) => {
  if (!confirm('Are you sure you want to delete this frame?')) {
    return
  }

  try {
    await picturesStore.deletePicture(frameId)
    selectedFrame.value = null
  } catch (err) {
    alert('Failed to delete frame')
  }
}

const deleteWall = async (wallId) => {
  if (!confirm('Are you sure you want to delete this wall?')) {
    return
  }

  try {
    await wallsStore.deleteWall(wallId)
    selectedWall.value = null
  } catch (err) {
    alert('Failed to delete wall')
  }
}

const getImageUrl = (path) => {
  return getUploadUrl(path)
}

// Get frames assigned to a wall (via frame_placements for consistency)
const getWallFrames = (wall) => {
  // Return pictures that have placements on this wall
  const placedPictureIds = (wall.frame_placements || []).map(p => p.picture_id).filter(Boolean)
  const placedFrameIds = (wall.frame_placements || []).map(p => p.frame_id).filter(Boolean)

  return picturesStore.pictures.filter(p =>
    placedPictureIds.includes(p.id) ||
    p.frames?.some(f => placedFrameIds.includes(f.id))
  )
}

// Get frame count from placements (for consistency with SavedWalls)
const getWallFrameCount = (wall) => {
  return wall.frame_placements?.length || 0
}

// Add frame to wall (creates placement for AR)
const addFrameToWall = async (picture, wallId) => {
  if (!picture.frames || picture.frames.length === 0) {
    alert('This picture has no frame dimensions. Please add dimensions first.')
    return
  }

  assigningWall.value = true
  try {
    // Get the first frame's data (the 3D frame with dimensions)
    const frameData = picture.frames[0]

    // Add placement to wall's frame_placements array for AR
    await wallsStore.addFramePlacement(wallId, {
      frame_id: frameData.id,
      picture_id: picture.id,
      position: { x: 0, y: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      scale: 1.0
    })

    // Also update the picture's wall_id for tracking
    await picturesStore.updatePicture(picture.id, { wall_id: wallId })

    // Update local state
    if (selectedFrame.value && selectedFrame.value.id === picture.id) {
      selectedFrame.value.wall_id = wallId
    }

    // Refresh walls to get updated frame_placements
    await wallsStore.fetchWalls()
  } catch (err) {
    console.error('Failed to add frame to wall:', err)
    alert('Failed to add frame to wall')
  } finally {
    assigningWall.value = false
  }
}

// Remove frame from wall
const removeFrameFromWall = async (pictureId) => {
  assigningWall.value = true
  try {
    // Get the picture to find its wall_id and frame info
    const picture = picturesStore.pictures.find(p => p.id === pictureId)
    if (picture && picture.wall_id) {
      // Also remove from wall's frame_placements array
      const wall = wallsStore.walls.find(w => w.id === picture.wall_id)
      if (wall && wall.frame_placements?.length) {
        const frameId = picture.frames?.[0]?.id
        const updatedPlacements = wall.frame_placements.filter(
          p => p.picture_id !== pictureId && p.frame_id !== frameId
        )
        await wallsStore.updateWall(wall.id, { frame_placements: updatedPlacements })
      }
    }

    // Update the picture's wall_id to null
    await picturesStore.updatePicture(pictureId, { wall_id: null })

    if (selectedFrame.value && selectedFrame.value.id === pictureId) {
      selectedFrame.value.wall_id = null
    }

    // Refresh walls to get updated frame_placements
    await wallsStore.fetchWalls()
  } catch (err) {
    console.error('Failed to remove frame from wall:', err)
    alert('Failed to remove frame from wall')
  } finally {
    assigningWall.value = false
  }
}

// Get wall name by id
const getWallName = (wallId) => {
  if (!wallId) return null
  const wall = wallsStore.walls.find(w => w.id === wallId)
  return wall ? wall.name : null
}

// Frame dimension editing
const startEditingFrameDimensions = (frame) => {
  if (frame.frames?.length) {
    const frameData = frame.frames[0]
    frameDimensionEdit.value = {
      width: frameData.dimensions?.cm?.width || 0,
      height: frameData.dimensions?.cm?.height || 0,
      unit: 'cm'
    }
    editingFrameDimensions.value = true
  }
}

const cancelEditingFrameDimensions = () => {
  editingFrameDimensions.value = false
}

const saveFrameDimensions = async () => {
  if (!selectedFrame.value?.frames?.length) return

  savingDimensions.value = true
  try {
    const frameData = selectedFrame.value.frames[0]
    await picturesStore.updateFrame(selectedFrame.value.id, frameData.id, {
      width: frameDimensionEdit.value.width,
      height: frameDimensionEdit.value.height,
      unit: frameDimensionEdit.value.unit
    })
    editingFrameDimensions.value = false
    // Refresh pictures to get updated data
    await picturesStore.fetchPictures()
    // Update selectedFrame with new data
    selectedFrame.value = picturesStore.pictures.find(p => p.id === selectedFrame.value.id)
  } catch (err) {
    console.error('Failed to update frame dimensions:', err)
    alert('Failed to update dimensions')
  } finally {
    savingDimensions.value = false
  }
}

// Wall dimension editing
const startEditingWallDimensions = () => {
  wallDimensionEdit.value = {
    width: selectedWall.value?.width_cm || 0,
    height: selectedWall.value?.height_cm || 0
  }
  editingWallDimensions.value = true
}

const cancelEditingWallDimensions = () => {
  editingWallDimensions.value = false
}

const saveWallDimensions = async () => {
  if (!selectedWall.value) return

  savingDimensions.value = true
  try {
    await wallsStore.updateWall(selectedWall.value.id, {
      width_cm: wallDimensionEdit.value.width,
      height_cm: wallDimensionEdit.value.height
    })
    editingWallDimensions.value = false
    // Refresh walls to get updated data
    await wallsStore.fetchWalls()
    // Update selectedWall with new data
    selectedWall.value = wallsStore.walls.find(w => w.id === selectedWall.value.id)
  } catch (err) {
    console.error('Failed to update wall dimensions:', err)
    alert('Failed to update dimensions')
  } finally {
    savingDimensions.value = false
  }
}

// Recrop functionality
const startRecrop = () => {
  if (selectedFrame.value) {
    recropImageUrl.value = getImageUrl(selectedFrame.value.original_image_path || selectedFrame.value.image_path)
    croppedImage.value = null
    lockAspectRatio.value = true // Default to locked

    // Calculate aspect ratio from current frame dimensions
    if (selectedFrame.value.frames?.length) {
      const frameData = selectedFrame.value.frames[0]
      const widthCm = frameData.dimensions?.cm?.width
      const heightCm = frameData.dimensions?.cm?.height
      if (widthCm && heightCm) {
        recropAspectRatio.value = widthCm / heightCm
      } else {
        recropAspectRatio.value = null
      }
    } else {
      recropAspectRatio.value = null
    }

    showRecropModal.value = true
  }
}

const handleCrop = (cropData) => {
  croppedImage.value = cropData
}

const cancelRecrop = () => {
  showRecropModal.value = false
  croppedImage.value = null
}

const saveRecrop = async () => {
  if (!croppedImage.value || !selectedFrame.value) return

  savingRecrop.value = true
  try {
    // Create a new file from the cropped blob
    const file = new File([croppedImage.value.blob], 'recropped.jpg', { type: 'image/jpeg' })

    // Upload the new cropped image as a replacement
    const formData = new FormData()
    formData.append('image', file)

    // Use the API to update the picture's image
    const response = await fetch(`/api/pictures/${selectedFrame.value.id}/image`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error('Failed to update image')
    }

    // Update frame dimensions to match the new crop aspect ratio
    if (selectedFrame.value.frames?.length && croppedImage.value.width && croppedImage.value.height) {
      const frameData = selectedFrame.value.frames[0]
      const oldWidthCm = frameData.dimensions?.cm?.width || 20
      const oldHeightCm = frameData.dimensions?.cm?.height || 25

      // Calculate new aspect ratio from cropped image
      const newAspectRatio = croppedImage.value.width / croppedImage.value.height

      // Keep the larger dimension and adjust the other proportionally
      let newWidthCm, newHeightCm
      if (oldWidthCm >= oldHeightCm) {
        // Keep width, adjust height
        newWidthCm = oldWidthCm
        newHeightCm = oldWidthCm / newAspectRatio
      } else {
        // Keep height, adjust width
        newHeightCm = oldHeightCm
        newWidthCm = oldHeightCm * newAspectRatio
      }

      // Update frame dimensions
      await picturesStore.updateFrame(selectedFrame.value.id, frameData.id, {
        width: newWidthCm,
        height: newHeightCm,
        unit: 'cm'
      })
    }

    // Refresh pictures to get updated data
    await picturesStore.fetchPictures()
    // Update selectedFrame with new data
    selectedFrame.value = picturesStore.pictures.find(p => p.id === selectedFrame.value.id)

    showRecropModal.value = false
    croppedImage.value = null
  } catch (err) {
    console.error('Failed to save recropped image:', err)
    alert('Failed to save recropped image')
  } finally {
    savingRecrop.value = false
  }
}

// Get frame dimensions for preview
const getFrameDimensions = (frame) => {
  if (frame?.frames?.length) {
    const frameData = frame.frames[0]
    return {
      widthCm: frameData.dimensions?.cm?.width || 20,
      heightCm: frameData.dimensions?.cm?.height || 25,
      frameColor: frameData.styling?.frame_color || '#8B4513'
    }
  }
  return { widthCm: 20, heightCm: 25, frameColor: '#8B4513' }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">My Gallery</h1>
      <div class="flex gap-2">
        <router-link to="/capture/wall" class="btn btn-secondary">
          Add Wall
        </router-link>
        <router-link to="/capture/frame" class="btn btn-primary">
          Add Frame
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
        Walls ({{ wallsStore.walls.length }})
      </button>
      <button
        @click="activeTab = 'frames'"
        class="px-4 py-2 rounded-lg transition"
        :class="activeTab === 'frames' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
      >
        Frames ({{ picturesStore.pictures.length }})
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!hasContent" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <h3 class="text-xl font-semibold mb-2">Your gallery is empty</h3>
      <p class="text-gray-400 mb-4">Start by capturing a wall or a frame</p>
      <div class="flex gap-3 justify-center">
        <router-link to="/capture/wall" class="btn btn-secondary">
          Capture Wall
        </router-link>
        <router-link to="/capture/frame" class="btn btn-primary">
          Capture Frame
        </router-link>
      </div>
    </div>

    <!-- Content -->
    <div v-else class="space-y-8">
      <!-- Walls Section -->
      <div v-if="filteredItems.walls.length > 0">
        <h2 class="text-lg font-semibold mb-4 text-gray-300" v-if="activeTab === 'all'">
          Walls
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="wall in filteredItems.walls"
            :key="'wall-' + wall.id"
            @click="openWallDetails(wall)"
            class="card p-3 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
          >
            <div class="aspect-video bg-dark-300 rounded-lg overflow-hidden mb-3">
              <img
                :src="getImageUrl(wall.thumbnail_path || wall.image_path)"
                :alt="wall.name"
                class="w-full h-full object-cover"
              />
            </div>
            <div class="flex items-start justify-between">
              <div>
                <h3 class="font-medium">{{ wall.name }}</h3>
                <p class="text-sm text-gray-400">
                  {{ getWallFrameCount(wall) }} frame(s) assigned
                </p>
              </div>
              <span class="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded">Wall</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Frames Section -->
      <div v-if="filteredItems.frames.length > 0">
        <h2 class="text-lg font-semibold mb-4 text-gray-300" v-if="activeTab === 'all'">
          Frames
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div
            v-for="frame in filteredItems.frames"
            :key="'frame-' + frame.id"
            @click="openFrameDetails(frame)"
            class="card p-2 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
          >
            <div class="aspect-square bg-dark-300 rounded-lg overflow-hidden mb-2">
              <img
                :src="getImageUrl(frame.thumbnail_path || frame.image_path)"
                :alt="frame.name"
                class="w-full h-full object-cover"
              />
            </div>
            <h3 class="font-medium truncate">{{ frame.name }}</h3>
            <p class="text-sm text-gray-400">
              <span v-if="getWallName(frame.wall_id)">{{ getWallName(frame.wall_id) }}</span>
              <span v-else class="text-gray-500">Not assigned</span>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Frame details modal -->
    <div
      v-if="selectedFrame"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="closeModal"
    >
      <div class="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">{{ selectedFrame.name }}</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Framed Preview -->
        <div class="flex justify-center mb-4 bg-dark-300 rounded-lg p-4">
          <FramePreview2D
            v-if="selectedFrame.frames?.length"
            :imageUrl="getImageUrl(selectedFrame.image_path)"
            :widthCm="getFrameDimensions(selectedFrame).widthCm"
            :heightCm="getFrameDimensions(selectedFrame).heightCm"
            :frameColor="getFrameDimensions(selectedFrame).frameColor"
            :maxWidth="350"
            :maxHeight="350"
          />
          <img
            v-else
            :src="getImageUrl(selectedFrame.image_path)"
            :alt="selectedFrame.name"
            class="max-w-full max-h-80 rounded-lg"
          />
        </div>

        <!-- Recrop button -->
        <div class="mb-4">
          <button
            @click="startRecrop"
            class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Recrop Image
          </button>
        </div>

        <!-- Frame dimensions -->
        <div v-if="selectedFrame.frames?.length" class="mb-4">
          <h3 class="font-semibold mb-2">Dimensions</h3>
          <div class="space-y-2">
            <div
              v-for="frameSize in selectedFrame.frames"
              :key="frameSize.id"
              class="bg-dark-300 rounded-lg p-3"
            >
              <!-- Display mode -->
              <div v-if="!editingFrameDimensions" class="flex items-center justify-between">
                <p
                  class="text-sm cursor-pointer hover:text-primary-400 transition"
                  @click="startEditingFrameDimensions(selectedFrame)"
                  title="Click to edit"
                >
                  {{ frameSize.dimensions?.inches?.width }}" x {{ frameSize.dimensions?.inches?.height }}"
                  ({{ frameSize.dimensions?.cm?.width?.toFixed(1) }} x {{ frameSize.dimensions?.cm?.height?.toFixed(1) }} cm)
                </p>
                <button
                  @click="startEditingFrameDimensions(selectedFrame)"
                  class="text-gray-400 hover:text-primary-400 text-sm"
                >
                  Edit
                </button>
              </div>
              <!-- Edit mode -->
              <div v-else class="space-y-3">
                <div class="flex gap-2 items-end">
                  <div>
                    <label class="block text-xs text-gray-400 mb-1">Width</label>
                    <input
                      v-model.number="frameDimensionEdit.width"
                      type="number"
                      step="0.1"
                      min="0"
                      class="w-20 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                  </div>
                  <span class="text-gray-400 pb-1">x</span>
                  <div>
                    <label class="block text-xs text-gray-400 mb-1">Height</label>
                    <input
                      v-model.number="frameDimensionEdit.height"
                      type="number"
                      step="0.1"
                      min="0"
                      class="w-20 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                  </div>
                  <select
                    v-model="frameDimensionEdit.unit"
                    class="px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  >
                    <option value="cm">cm</option>
                    <option value="inches">inches</option>
                  </select>
                </div>
                <div class="flex gap-2">
                  <button
                    @click="saveFrameDimensions"
                    :disabled="savingDimensions"
                    class="px-3 py-1 bg-primary-600 hover:bg-primary-700 rounded text-sm"
                  >
                    {{ savingDimensions ? 'Saving...' : 'Save' }}
                  </button>
                  <button
                    @click="cancelEditingFrameDimensions"
                    class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Wall assignment -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Add to Wall</h3>
          <p class="text-sm text-gray-400 mb-3">Select a wall to place this frame on for AR viewing</p>
          <div class="grid grid-cols-3 gap-2">
            <button
              @click="removeFrameFromWall(selectedFrame.id)"
              :disabled="assigningWall"
              class="aspect-video rounded-lg border-2 transition flex items-center justify-center text-sm"
              :class="!selectedFrame.wall_id ? 'border-primary-500 bg-primary-500/10' : 'border-gray-600 hover:border-gray-500'"
            >
              None
            </button>
            <button
              v-for="wall in wallsStore.walls"
              :key="wall.id"
              @click="addFrameToWall(selectedFrame, wall.id)"
              :disabled="assigningWall || selectedFrame.wall_id === wall.id"
              class="aspect-video rounded-lg border-2 overflow-hidden transition relative"
              :class="selectedFrame.wall_id === wall.id ? 'border-primary-500 border-2' : 'border-gray-600 hover:border-gray-500'"
            >
              <img
                :src="getImageUrl(wall.thumbnail_path || wall.image_path)"
                :alt="wall.name"
                class="w-full h-full object-cover"
              />
              <div class="absolute bottom-0 left-0 right-0 bg-black/60 px-1 py-0.5">
                <span class="text-xs truncate block">{{ wall.name }}</span>
              </div>
              <div v-if="selectedFrame.wall_id === wall.id" class="absolute inset-0 bg-primary-500/20 flex items-center justify-center">
                <svg class="w-6 h-6 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
            </button>
          </div>
          <p v-if="wallsStore.walls.length === 0" class="text-sm text-gray-400 mt-2">
            No walls yet. <router-link to="/capture/wall" class="text-primary-400 hover:underline">Add a wall</router-link> first.
          </p>
          <p v-if="assigningWall" class="text-sm text-primary-400 mt-2">Adding frame to wall...</p>
        </div>

        <div class="flex gap-3">
          <router-link
            :to="`/wall/${selectedFrame.wall_id}`"
            class="btn btn-primary flex-1"
            v-if="selectedFrame.wall_id"
          >
            View on Wall
          </router-link>
          <button
            @click="deleteFrame(selectedFrame.id)"
            class="btn bg-red-600 hover:bg-red-700 text-white"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Wall details modal -->
    <div
      v-if="selectedWall"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="closeModal"
    >
      <div class="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">{{ selectedWall.name }}</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <img
          :src="getImageUrl(selectedWall.image_path)"
          :alt="selectedWall.name"
          class="w-full rounded-lg mb-4"
        />

        <div v-if="selectedWall.description" class="mb-4">
          <p class="text-gray-400">{{ selectedWall.description }}</p>
        </div>

        <div class="mb-4">
          <h3 class="font-semibold mb-2">Dimensions</h3>
          <!-- Display mode -->
          <div v-if="!editingWallDimensions">
            <div class="flex items-center justify-between">
              <p
                class="text-gray-400 cursor-pointer hover:text-primary-400 transition"
                @click="startEditingWallDimensions"
                title="Click to edit"
              >
                <span v-if="selectedWall.width_cm || selectedWall.height_cm">
                  {{ selectedWall.width_cm?.toFixed(0) || '?' }} x {{ selectedWall.height_cm?.toFixed(0) || '?' }} cm
                </span>
                <span v-else class="text-gray-500">Click to set dimensions</span>
              </p>
              <button
                @click="startEditingWallDimensions"
                class="text-gray-400 hover:text-primary-400 text-sm"
              >
                Edit
              </button>
            </div>
          </div>
          <!-- Edit mode -->
          <div v-else class="bg-dark-300 rounded-lg p-3 space-y-3">
            <div class="flex gap-2 items-end">
              <div>
                <label class="block text-xs text-gray-400 mb-1">Width</label>
                <input
                  v-model.number="wallDimensionEdit.width"
                  type="number"
                  step="1"
                  min="0"
                  class="w-20 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  placeholder="Width"
                />
              </div>
              <span class="text-gray-400 pb-1">x</span>
              <div>
                <label class="block text-xs text-gray-400 mb-1">Height</label>
                <input
                  v-model.number="wallDimensionEdit.height"
                  type="number"
                  step="1"
                  min="0"
                  class="w-20 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  placeholder="Height"
                />
              </div>
              <span class="text-sm text-gray-400 pb-1">cm</span>
            </div>
            <div class="flex gap-2">
              <button
                @click="saveWallDimensions"
                :disabled="savingDimensions"
                class="px-3 py-1 bg-primary-600 hover:bg-primary-700 rounded text-sm"
              >
                {{ savingDimensions ? 'Saving...' : 'Save' }}
              </button>
              <button
                @click="cancelEditingWallDimensions"
                class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Assigned frames -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Frames on this wall ({{ getWallFrameCount(selectedWall) }})</h3>
          <div v-if="getWallFrames(selectedWall).length > 0" class="grid grid-cols-3 gap-2">
            <div
              v-for="frame in getWallFrames(selectedWall)"
              :key="frame.id"
              @click="openFrameDetails(frame)"
              class="aspect-square bg-dark-300 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
            >
              <img
                :src="getImageUrl(frame.thumbnail_path || frame.image_path)"
                :alt="frame.name"
                class="w-full h-full object-cover"
              />
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">
            No frames assigned yet. Assign frames from the Frames tab.
          </p>
        </div>

        <div class="flex gap-3">
          <router-link
            :to="`/wall/${selectedWall.id}`"
            class="btn btn-primary flex-1"
          >
            View/Edit Wall
          </router-link>
          <button
            @click="deleteWall(selectedWall.id)"
            class="btn bg-red-600 hover:bg-red-700 text-white"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Recrop modal -->
    <div
      v-if="showRecropModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="cancelRecrop"
    >
      <div class="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">Recrop Image</h2>
          <button @click="cancelRecrop" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="mb-4">
          <ImageCropper
            :key="effectiveAspectRatio"
            :imageUrl="recropImageUrl"
            :aspectRatio="effectiveAspectRatio"
            @crop="handleCrop"
          />
        </div>

        <!-- Aspect ratio lock toggle -->
        <div v-if="recropAspectRatio" class="mb-4 flex items-center gap-2">
          <input
            type="checkbox"
            id="lockAspectRatio"
            v-model="lockAspectRatio"
            class="w-4 h-4 rounded border-gray-600 bg-dark-300 text-primary-500 focus:ring-primary-500"
          />
          <label for="lockAspectRatio" class="text-sm text-gray-300">
            Lock to current frame ratio ({{ recropAspectRatio?.toFixed(2) }})
          </label>
        </div>

        <div class="flex gap-3 justify-end">
          <button
            @click="cancelRecrop"
            class="btn bg-gray-600 hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            @click="saveRecrop"
            :disabled="!croppedImage || savingRecrop"
            class="btn btn-primary"
          >
            {{ savingRecrop ? 'Saving...' : 'Save Crop' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
