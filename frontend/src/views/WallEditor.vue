<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WallViewer from '@/components/WallViewer.vue'
import FramePreview2D from '@/components/FramePreview2D.vue'
import ImageCropper from '@/components/ImageCropper.vue'
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

// Frame editing state
const selectedPlacementIndex = ref(null)
const editingPosition = ref({ x: 0, y: 0 })
const savedPosition = ref({ x: 0, y: 0 })
const savingPosition = ref(false)
const positionUnit = ref('cm') // 'cm' or 'ft'

// Wall editing state
const editingWall = ref(false)
const wallEdit = ref({ name: '', description: '', width: 0, height: 0, unit: 'cm' })
const savingWall = ref(false)

// Frame property editing state
const editingFrameDimensions = ref(false)
const frameDimensionEdit = ref({ width: 0, height: 0, unit: 'cm' })
const editingFrameColor = ref(false)
const frameColorEdit = ref('#000000')
const savingFrameEdit = ref(false)

// Frame color presets
const presetColors = [
  { label: 'Black', value: '#000000' },
  { label: 'White', value: '#FFFFFF' },
  { label: 'Brown', value: '#8B4513' }
]
const showCustomColorPicker = ref(false)

// Recrop state
const showRecropModal = ref(false)
const recropImageUrl = ref('')
const recropAspectRatio = ref(null)
const lockAspectRatio = ref(true)
const croppedImage = ref(null)
const savingRecrop = ref(false)

const effectiveAspectRatio = computed(() => {
  return lockAspectRatio.value ? recropAspectRatio.value : null
})

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

// Frames available to add (not already placed on this wall)
const availableFrames = computed(() => {
  const placedFrameIds = (wall.value?.frame_placements || []).map(p => p.frame_id)
  return allFrames.value.filter(frame => !placedFrameIds.includes(frame.id))
})

const addFrame = async (frame) => {
  try {
    saving.value = true
    await wallsStore.addFramePlacement(wall.value.id, {
      frame_id: frame.id,
      position: { x: 0, y: 0 },
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
    const removedPlacement = placements[placementIndex]
    placements.splice(placementIndex, 1)

    // Update wall's frame_placements
    await wallsStore.updateWall(wall.value.id, { frame_placements: placements })

    // Also update the picture's wall_id to null to keep data in sync
    if (removedPlacement?.picture_id) {
      await picturesStore.updatePicture(removedPlacement.picture_id, { wall_id: null })
    } else if (removedPlacement?.frame_id) {
      // Find picture by frame_id if picture_id is not available
      const picture = picturesStore.pictures.find(p =>
        p.frames?.some(f => f.id === removedPlacement.frame_id)
      )
      if (picture) {
        await picturesStore.updatePicture(picture.id, { wall_id: null })
      }
    }
  } catch (err) {
    error.value = 'Failed to remove frame'
  } finally {
    saving.value = false
  }
}

const getImageUrl = (path) => getUploadUrl(path)

// Get selected placement and frame data
const selectedPlacement = computed(() => {
  if (selectedPlacementIndex.value === null) return null
  return wall.value?.frame_placements?.[selectedPlacementIndex.value] || null
})

const selectedFrame = computed(() => {
  if (!selectedPlacement.value) return null
  return allFrames.value.find(f => f.id === selectedPlacement.value.frame_id) || null
})

// Get the picture for the selected frame
const selectedPicture = computed(() => {
  if (!selectedFrame.value) return null
  return picturesStore.pictures.find(p =>
    p.frames?.some(f => f.id === selectedFrame.value.id)
  ) || null
})

// Handle frame selection from viewer or list
const selectFrame = (data) => {
  if (typeof data === 'number') {
    // Called from list with index
    selectedPlacementIndex.value = data
  } else {
    // Called from viewer with { frameId, placementIndex }
    selectedPlacementIndex.value = data.placementIndex
  }

  // Initialize position editing values
  if (selectedPlacement.value) {
    const pos = {
      x: selectedPlacement.value.position?.x || 0,
      y: selectedPlacement.value.position?.y || 0
    }
    editingPosition.value = { ...pos }
    savedPosition.value = { ...pos }
    positionUnit.value = 'cm'
  }
}

// Update frame position
const savePosition = async () => {
  if (selectedPlacementIndex.value === null) return

  savingPosition.value = true
  try {
    const placements = [...(wall.value.frame_placements || [])]
    placements[selectedPlacementIndex.value] = {
      ...placements[selectedPlacementIndex.value],
      position: {
        ...placements[selectedPlacementIndex.value].position,
        x: editingPosition.value.x,
        y: editingPosition.value.y
      }
    }

    await wallsStore.updateWall(wall.value.id, { frame_placements: placements })
    savedPosition.value = { ...editingPosition.value }
  } catch (err) {
    console.error('Failed to update position:', err)
    error.value = 'Failed to update position'
  } finally {
    savingPosition.value = false
  }
}

const resetPosition = () => {
  editingPosition.value = { ...savedPosition.value }
}

// Position display: convert internal meters (center-based) to wall-relative measurements
const wallWidthM = computed(() => (wall.value?.width_cm || 0) * 0.01)
const wallHeightM = computed(() => (wall.value?.height_cm || 0) * 0.01)

// "From left" = wallWidth/2 + x (in meters), converted to cm
const posFromLeftCm = computed({
  get: () => +((wallWidthM.value / 2 + editingPosition.value.x) * 100).toFixed(1),
  set: (val) => { editingPosition.value.x = (val / 100) - wallWidthM.value / 2 }
})
// "From floor" = wallHeight/2 + y (in meters), converted to cm
const posFromFloorCm = computed({
  get: () => +((wallHeightM.value / 2 + editingPosition.value.y) * 100).toFixed(1),
  set: (val) => { editingPosition.value.y = (val / 100) - wallHeightM.value / 2 }
})

// ft & in display for position
const posFromLeftFtIn = computed(() => cmToFtIn(posFromLeftCm.value))
const posFromFloorFtIn = computed(() => cmToFtIn(posFromFloorCm.value))

const posFromLeftFt = ref(0)
const posFromLeftIn = ref(0)
const posFromFloorFt = ref(0)
const posFromFloorIn = ref(0)

const syncFtInFromCm = () => {
  const lft = cmToFtIn(posFromLeftCm.value)
  posFromLeftFt.value = lft.ft
  posFromLeftIn.value = lft.inches
  const fft = cmToFtIn(posFromFloorCm.value)
  posFromFloorFt.value = fft.ft
  posFromFloorIn.value = fft.inches
}

const applyFtInToPosition = (axis) => {
  if (axis === 'x') {
    posFromLeftCm.value = +ftInToCm(posFromLeftFt.value || 0, posFromLeftIn.value || 0).toFixed(1)
  } else {
    posFromFloorCm.value = +ftInToCm(posFromFloorFt.value || 0, posFromFloorIn.value || 0).toFixed(1)
  }
}

const togglePositionUnit = () => {
  if (positionUnit.value === 'cm') {
    syncFtInFromCm()
    positionUnit.value = 'ft'
  } else {
    applyFtInToPosition('x')
    applyFtInToPosition('y')
    positionUnit.value = 'cm'
  }
}

// Handle frame drag-move from 3D viewer
const onFrameMoved = async (data) => {
  const { placementIndex, position } = data
  try {
    const placements = [...(wall.value.frame_placements || [])]
    placements[placementIndex] = {
      ...placements[placementIndex],
      position: {
        ...placements[placementIndex].position,
        x: position.x,
        y: position.y
      }
    }
    await wallsStore.updateWall(wall.value.id, { frame_placements: placements })
  } catch (err) {
    console.error('Failed to save frame position:', err)
    error.value = 'Failed to save frame position'
  }
}

// Wall editing
const cmToFtIn = (cm) => {
  const totalInches = cm / 2.54
  const ft = Math.floor(totalInches / 12)
  const inches = +(totalInches - ft * 12).toFixed(1)
  return { ft, inches }
}

const ftInToCm = (ft, inches) => {
  return (ft * 12 + inches) * 2.54
}

const toggleWallUnit = () => {
  const w = parseFloat(wallEdit.value.width) || 0
  const h = parseFloat(wallEdit.value.height) || 0
  if (wallEdit.value.unit === 'cm') {
    // Convert cm -> ft & in
    const wFtIn = cmToFtIn(w)
    const hFtIn = cmToFtIn(h)
    wallEdit.value.widthFt = wFtIn.ft
    wallEdit.value.widthIn = wFtIn.inches
    wallEdit.value.heightFt = hFtIn.ft
    wallEdit.value.heightIn = hFtIn.inches
    wallEdit.value.unit = 'ft'
  } else {
    // Convert ft & in -> cm
    wallEdit.value.width = +ftInToCm(
      parseFloat(wallEdit.value.widthFt) || 0,
      parseFloat(wallEdit.value.widthIn) || 0
    ).toFixed(1)
    wallEdit.value.height = +ftInToCm(
      parseFloat(wallEdit.value.heightFt) || 0,
      parseFloat(wallEdit.value.heightIn) || 0
    ).toFixed(1)
    wallEdit.value.unit = 'cm'
  }
}

const startEditWall = () => {
  wallEdit.value = {
    name: wall.value?.name || '',
    description: wall.value?.description || '',
    width: wall.value?.width_cm || 0,
    height: wall.value?.height_cm || 0,
    unit: 'cm',
    widthFt: 0,
    widthIn: 0,
    heightFt: 0,
    heightIn: 0
  }
  editingWall.value = true
}

const cancelEditWall = () => {
  editingWall.value = false
}

const saveWall = async () => {
  savingWall.value = true
  let widthCm, heightCm
  if (wallEdit.value.unit === 'ft') {
    widthCm = ftInToCm(parseFloat(wallEdit.value.widthFt) || 0, parseFloat(wallEdit.value.widthIn) || 0)
    heightCm = ftInToCm(parseFloat(wallEdit.value.heightFt) || 0, parseFloat(wallEdit.value.heightIn) || 0)
  } else {
    widthCm = parseFloat(wallEdit.value.width) || 0
    heightCm = parseFloat(wallEdit.value.height) || 0
  }
  try {
    await wallsStore.updateWall(wall.value.id, {
      name: wallEdit.value.name,
      description: wallEdit.value.description,
      width_cm: widthCm,
      height_cm: heightCm
    })
    editingWall.value = false
  } catch (err) {
    console.error('Failed to update wall:', err)
    error.value = 'Failed to update wall'
  } finally {
    savingWall.value = false
  }
}

// Frame dimension editing
const startEditFrameDimensions = () => {
  if (!selectedFrame.value) return
  frameDimensionEdit.value = {
    width: selectedFrame.value.dimensions?.cm?.width || 0,
    height: selectedFrame.value.dimensions?.cm?.height || 0,
    unit: 'cm'
  }
  editingFrameDimensions.value = true
}

const cancelEditFrameDimensions = () => {
  editingFrameDimensions.value = false
}

const saveFrameDimensions = async () => {
  if (!selectedFrame.value || !selectedPicture.value) return
  savingFrameEdit.value = true
  try {
    await picturesStore.updateFrame(selectedPicture.value.id, selectedFrame.value.id, {
      width: frameDimensionEdit.value.width,
      height: frameDimensionEdit.value.height,
      unit: frameDimensionEdit.value.unit
    })
    editingFrameDimensions.value = false
    await picturesStore.fetchPictures()
  } catch (err) {
    console.error('Failed to update frame dimensions:', err)
    error.value = 'Failed to update dimensions'
  } finally {
    savingFrameEdit.value = false
  }
}

// Frame color editing
const startEditFrameColor = () => {
  if (!selectedFrame.value) return
  frameColorEdit.value = selectedFrame.value.styling?.frame_color || '#000000'
  showCustomColorPicker.value = false
  editingFrameColor.value = true
}

const cancelEditFrameColor = () => {
  editingFrameColor.value = false
}

const saveFrameColor = async () => {
  if (!selectedFrame.value || !selectedPicture.value) return
  savingFrameEdit.value = true
  try {
    await picturesStore.updateFrame(selectedPicture.value.id, selectedFrame.value.id, {
      frame_color: frameColorEdit.value
    })
    editingFrameColor.value = false
    await picturesStore.fetchPictures()
  } catch (err) {
    console.error('Failed to update frame color:', err)
    error.value = 'Failed to update frame color'
  } finally {
    savingFrameEdit.value = false
  }
}

// Recrop functionality
const startRecrop = () => {
  if (!selectedPicture.value) return
  recropImageUrl.value = getImageUrl(selectedPicture.value.original_image_path || selectedPicture.value.image_path)
  croppedImage.value = null
  lockAspectRatio.value = true

  if (selectedFrame.value) {
    const widthCm = selectedFrame.value.dimensions?.cm?.width
    const heightCm = selectedFrame.value.dimensions?.cm?.height
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

const handleCrop = (cropData) => {
  croppedImage.value = cropData
}

const cancelRecrop = () => {
  showRecropModal.value = false
  croppedImage.value = null
}

const saveRecrop = async () => {
  if (!croppedImage.value || !selectedPicture.value) return

  savingRecrop.value = true
  try {
    const file = new File([croppedImage.value.blob], 'recropped.jpg', { type: 'image/jpeg' })
    const formData = new FormData()
    formData.append('image', file)

    const response = await fetch(`/api/pictures/${selectedPicture.value.id}/image`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: formData
    })

    if (!response.ok) throw new Error('Failed to update image')

    // Update frame dimensions to match new crop aspect ratio
    if (selectedFrame.value && croppedImage.value.width && croppedImage.value.height) {
      const oldWidthCm = selectedFrame.value.dimensions?.cm?.width || 20
      const oldHeightCm = selectedFrame.value.dimensions?.cm?.height || 25
      const newAspectRatio = croppedImage.value.width / croppedImage.value.height

      let newWidthCm, newHeightCm
      if (oldWidthCm >= oldHeightCm) {
        newWidthCm = oldWidthCm
        newHeightCm = oldWidthCm / newAspectRatio
      } else {
        newHeightCm = oldHeightCm
        newWidthCm = oldHeightCm * newAspectRatio
      }

      await picturesStore.updateFrame(selectedPicture.value.id, selectedFrame.value.id, {
        width: newWidthCm,
        height: newHeightCm,
        unit: 'cm'
      })
    }

    await picturesStore.fetchPictures()
    showRecropModal.value = false
    croppedImage.value = null
  } catch (err) {
    console.error('Failed to save recropped image:', err)
    error.value = 'Failed to save recropped image'
  } finally {
    savingRecrop.value = false
  }
}

// Reset frame edit states when closing editor
const closeFrameEditor = () => {
  selectedPlacementIndex.value = null
  editingFrameDimensions.value = false
  editingFrameColor.value = false
  showRecropModal.value = false
}

// Get frame dimensions for preview
const getFrameDimensions = (frame) => {
  if (frame?.dimensions?.cm) {
    return {
      widthCm: frame.dimensions.cm.width || 20,
      heightCm: frame.dimensions.cm.height || 25,
      frameColor: frame.styling?.frame_color || '#8B4513'
    }
  }
  return { widthCm: 20, heightCm: 25, frameColor: '#8B4513' }
}
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
          :wallWidthCm="wall.width_cm || 0"
          :wallHeightCm="wall.height_cm || 0"
          :framePlacements="wall.frame_placements || []"
          :frames="allFrames"
          @frameSelected="selectFrame"
          @frameMoved="onFrameMoved"
        />
        <p class="text-xs text-gray-500 mt-2 text-center">Left-click and drag frames to move them. Right-click and drag to rotate the view.</p>
      </div>

      <!-- Wall Details -->
      <div class="card mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-semibold">Wall Details</h3>
            <template v-if="!editingWall">
              <p v-if="wall.description" class="text-sm text-gray-400 mt-1">{{ wall.description }}</p>
              <p class="text-sm text-gray-400 mt-1">
                <template v-if="wall.width_cm && wall.height_cm">
                  {{ wall.width_cm.toFixed(1) }} x {{ wall.height_cm.toFixed(1) }} cm
                  ({{ (wall.width_cm / 2.54).toFixed(1) }}" x {{ (wall.height_cm / 2.54).toFixed(1) }}")
                </template>
                <template v-else>
                  No dimensions set
                </template>
              </p>
            </template>
          </div>
          <button
            v-if="!editingWall"
            @click="startEditWall"
            class="btn btn-secondary text-sm"
          >
            Edit Wall
          </button>
        </div>

        <div v-if="editingWall" class="mt-4 space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Wall Name</label>
            <input
              type="text"
              v-model="wallEdit.name"
              placeholder="e.g., Living Room Wall"
              class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              v-model="wallEdit.description"
              placeholder="Optional description..."
              rows="2"
              class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm resize-none"
            ></textarea>
          </div>
          <div class="flex items-center gap-2 mb-2">
            <span class="text-sm text-gray-400">Unit:</span>
            <button
              @click="toggleWallUnit"
              class="px-3 py-1 rounded text-xs font-medium transition"
              :class="wallEdit.unit === 'cm' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              cm
            </button>
            <button
              @click="toggleWallUnit"
              class="px-3 py-1 rounded text-xs font-medium transition"
              :class="wallEdit.unit === 'ft' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              ft &amp; in
            </button>
          </div>
          <!-- cm inputs -->
          <div v-if="wallEdit.unit === 'cm'" class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-400 mb-1">Width (cm)</label>
              <input
                type="number"
                v-model.number="wallEdit.width"
                step="0.1"
                min="0"
                class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
              />
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-1">Height (cm)</label>
              <input
                type="number"
                v-model.number="wallEdit.height"
                step="0.1"
                min="0"
                class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
              />
            </div>
          </div>
          <!-- ft & in inputs -->
          <div v-else class="space-y-3">
            <div>
              <label class="block text-sm text-gray-400 mb-1">Width</label>
              <div class="grid grid-cols-2 gap-2">
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="wallEdit.widthFt"
                    min="0"
                    class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-sm text-gray-400">ft</span>
                </div>
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="wallEdit.widthIn"
                    step="0.1"
                    min="0"
                    max="11.9"
                    class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-sm text-gray-400">in</span>
                </div>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-1">Height</label>
              <div class="grid grid-cols-2 gap-2">
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="wallEdit.heightFt"
                    min="0"
                    class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-sm text-gray-400">ft</span>
                </div>
                <div class="flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="wallEdit.heightIn"
                    step="0.1"
                    min="0"
                    max="11.9"
                    class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-sm text-gray-400">in</span>
                </div>
              </div>
            </div>
          </div>
          <div class="flex gap-3">
            <button
              @click="cancelEditWall"
              class="btn btn-secondary flex-1 text-sm"
            >
              Cancel
            </button>
            <button
              @click="saveWall"
              :disabled="savingWall"
              class="btn btn-primary flex-1 text-sm"
            >
              {{ savingWall ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>
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
            @click="selectFrame(index)"
            class="flex items-center justify-between bg-dark-300 rounded-lg p-3 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
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
              @click.stop="removeFrame(index)"
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

        <div v-if="availableFrames.length === 0" class="text-center py-6">
          <p class="text-gray-400 mb-4">
            {{ allFrames.length === 0 ? 'No frames available. Add some frames first.' : 'All frames are already placed on this wall.' }}
          </p>
          <router-link v-if="allFrames.length === 0" to="/capture/frame" class="btn btn-primary">
            Add Frame
          </router-link>
        </div>

        <div v-else class="grid grid-cols-2 gap-3">
          <button
            v-for="frame in availableFrames"
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

    <!-- Frame editor modal -->
    <div
      v-if="selectedPlacement && selectedFrame"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="closeFrameEditor"
    >
      <div class="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">{{ selectedFrame.pictureName }}</h2>
          <button @click="closeFrameEditor" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Frame Preview -->
        <div class="flex justify-center mb-4 bg-dark-300 rounded-lg p-4">
          <FramePreview2D
            :imageUrl="getImageUrl(selectedPicture?.image_path || selectedFrame.pictureImage)"
            :widthCm="getFrameDimensions(selectedFrame).widthCm"
            :heightCm="getFrameDimensions(selectedFrame).heightCm"
            :frameColor="getFrameDimensions(selectedFrame).frameColor"
            :maxWidth="300"
            :maxHeight="300"
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
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold">Dimensions</h3>
            <button
              v-if="!editingFrameDimensions"
              @click="startEditFrameDimensions"
              class="text-gray-400 hover:text-primary-400 text-sm"
            >
              Edit
            </button>
          </div>
          <!-- Display mode -->
          <div v-if="!editingFrameDimensions">
            <p class="text-sm text-gray-400">
              {{ selectedFrame.dimensions?.inches?.width?.toFixed(1) }}" x {{ selectedFrame.dimensions?.inches?.height?.toFixed(1) }}"
              ({{ selectedFrame.dimensions?.cm?.width?.toFixed(1) }} x {{ selectedFrame.dimensions?.cm?.height?.toFixed(1) }} cm)
            </p>
          </div>
          <!-- Edit mode -->
          <div v-else class="bg-dark-300 rounded-lg p-3 space-y-3">
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
                :disabled="savingFrameEdit"
                class="px-3 py-1 bg-primary-600 hover:bg-primary-700 rounded text-sm"
              >
                {{ savingFrameEdit ? 'Saving...' : 'Save' }}
              </button>
              <button
                @click="cancelEditFrameDimensions"
                class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Frame color -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold">Frame Color</h3>
            <button
              v-if="!editingFrameColor"
              @click="startEditFrameColor"
              class="text-gray-400 hover:text-primary-400 text-sm"
            >
              Edit
            </button>
          </div>
          <!-- Display mode -->
          <div v-if="!editingFrameColor" class="flex items-center gap-2">
            <span
              class="w-5 h-5 rounded-full border border-gray-500 inline-block"
              :style="{ backgroundColor: selectedFrame.styling?.frame_color || '#8B4513' }"
            ></span>
            <span class="text-sm text-gray-400">{{ selectedFrame.styling?.frame_color || '#8B4513' }}</span>
          </div>
          <!-- Edit mode -->
          <div v-else class="bg-dark-300 rounded-lg p-3 space-y-3">
            <div class="flex gap-2 flex-wrap">
              <button
                v-for="preset in presetColors"
                :key="preset.value"
                @click="frameColorEdit = preset.value; showCustomColorPicker = false"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
                :class="frameColorEdit === preset.value && !showCustomColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
              >
                <span
                  class="w-5 h-5 rounded-full border border-gray-500"
                  :style="{ backgroundColor: preset.value }"
                ></span>
                <span class="text-sm">{{ preset.label }}</span>
              </button>
              <button
                @click="showCustomColorPicker = !showCustomColorPicker"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
                :class="showCustomColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
              >
                <span
                  class="w-5 h-5 rounded-full border border-gray-500"
                  :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }"
                ></span>
                <span class="text-sm">Custom</span>
              </button>
            </div>
            <div v-if="showCustomColorPicker">
              <input
                type="color"
                v-model="frameColorEdit"
                class="w-full h-10 rounded cursor-pointer bg-transparent border border-gray-600"
              />
            </div>
            <div class="flex gap-2">
              <button
                @click="saveFrameColor"
                :disabled="savingFrameEdit"
                class="px-3 py-1 bg-primary-600 hover:bg-primary-700 rounded text-sm"
              >
                {{ savingFrameEdit ? 'Saving...' : 'Save' }}
              </button>
              <button
                @click="cancelEditFrameColor"
                class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Position editing -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Position on Wall</h3>
          <p class="text-sm text-gray-400 mb-3">Distance from the left edge and floor</p>

          <!-- Unit toggle -->
          <div class="flex items-center gap-2 mb-3">
            <span class="text-sm text-gray-400">Unit:</span>
            <button
              @click="togglePositionUnit"
              class="px-3 py-1 rounded text-xs font-medium transition"
              :class="positionUnit === 'cm' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              cm
            </button>
            <button
              @click="togglePositionUnit"
              class="px-3 py-1 rounded text-xs font-medium transition"
              :class="positionUnit === 'ft' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              ft &amp; in
            </button>
          </div>

          <div class="flex gap-4">
            <!-- Left column: X slider + buttons -->
            <div class="flex-1">
              <!-- X Position (horizontal slider) -->
              <div class="mb-3">
                <label class="block text-sm text-gray-400 mb-1">X Position</label>
                <input
                  type="range"
                  v-model.number="posFromLeftCm"
                  :min="0"
                  :max="wall?.width_cm || 300"
                  step="0.5"
                  class="w-full"
                  @input="positionUnit === 'ft' && syncFtInFromCm()"
                />
                <!-- cm input -->
                <div v-if="positionUnit === 'cm'" class="mt-1">
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      v-model.number="posFromLeftCm"
                      step="0.1"
                      min="0"
                      class="w-full px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400">cm</span>
                  </div>
                </div>
                <!-- ft & in input -->
                <div v-else class="mt-1 flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="posFromLeftFt"
                    min="0"
                    @input="applyFtInToPosition('x')"
                    class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-xs text-gray-400">ft</span>
                  <input
                    type="number"
                    v-model.number="posFromLeftIn"
                    step="0.1"
                    min="0"
                    max="11.9"
                    @input="applyFtInToPosition('x')"
                    class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-xs text-gray-400">in</span>
                </div>
              </div>

              <!-- Buttons stacked -->
              <div class="space-y-2 mt-3">
                <button
                  @click="resetPosition"
                  :disabled="editingPosition.x === savedPosition.x && editingPosition.y === savedPosition.y"
                  class="btn btn-secondary w-full text-sm"
                >
                  Reset
                </button>
                <button
                  @click="savePosition"
                  :disabled="savingPosition || (editingPosition.x === savedPosition.x && editingPosition.y === savedPosition.y)"
                  class="btn btn-primary w-full text-sm"
                >
                  {{ savingPosition ? 'Saving...' : 'Save Position' }}
                </button>
              </div>
            </div>

            <!-- Right column: Y slider (vertical) + input -->
            <div class="flex flex-col items-center" style="width: 120px;">
              <label class="block text-sm text-gray-400 mb-1">Y Position</label>
              <div class="flex items-stretch gap-2 flex-1">
                <!-- Vertical slider -->
                <div class="flex items-center" style="height: 180px;">
                  <input
                    type="range"
                    v-model.number="posFromFloorCm"
                    :min="0"
                    :max="wall?.height_cm || 300"
                    step="0.5"
                    class="vertical-slider"
                    style="width: 180px; transform: rotate(-90deg); transform-origin: center center;"
                    @input="positionUnit === 'ft' && syncFtInFromCm()"
                  />
                </div>
                <!-- Input beside slider -->
                <div class="flex flex-col justify-center">
                  <template v-if="positionUnit === 'cm'">
                    <input
                      type="number"
                      v-model.number="posFromFloorCm"
                      step="0.1"
                      min="0"
                      class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400 text-center mt-1">cm</span>
                  </template>
                  <template v-else>
                    <div class="space-y-1">
                      <div class="flex items-center gap-1">
                        <input
                          type="number"
                          v-model.number="posFromFloorFt"
                          min="0"
                          @input="applyFtInToPosition('y')"
                          class="w-12 px-1 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                        />
                        <span class="text-xs text-gray-400">ft</span>
                      </div>
                      <div class="flex items-center gap-1">
                        <input
                          type="number"
                          v-model.number="posFromFloorIn"
                          step="0.1"
                          min="0"
                          max="11.9"
                          @input="applyFtInToPosition('y')"
                          class="w-12 px-1 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                        />
                        <span class="text-xs text-gray-400">in</span>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button
            @click="removeFrame(selectedPlacementIndex); closeFrameEditor()"
            class="btn bg-red-600 hover:bg-red-700 text-white flex-1"
          >
            Remove from Wall
          </button>
        </div>
      </div>
    </div>
    <!-- Recrop modal -->
    <div
      v-if="showRecropModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-[60]"
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

        <div v-if="recropAspectRatio" class="mb-4 flex items-center gap-2">
          <input
            type="checkbox"
            id="lockAspectRatioWall"
            v-model="lockAspectRatio"
            class="w-4 h-4 rounded border-gray-600 bg-dark-300 text-primary-500 focus:ring-primary-500"
          />
          <label for="lockAspectRatioWall" class="text-sm text-gray-300">
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
