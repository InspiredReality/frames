<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WallViewer from '@/components/WallViewer.vue'
import FramePreview2D from '@/components/FramePreview2D.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'
import { useAuthStore } from '@/store/auth'
import { getUploadUrl } from '@/services/api'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()
const authStore = useAuthStore()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saveError = ref('')
const showFramePicker = ref(false)
const pickerTab = ref('my') // 'my' or 'public'
const wallViewerRef = ref(null)

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

// Wall image editing state
const showWallRecropModal = ref(false)
const wallRecropImageUrl = ref('')
const wallCroppedImage = ref(null)
const savingWallImage = ref(false)
const wallImageInput = ref(null)

// Frame property editing state
const editingFrameDimensions = ref(false)
const frameDimensionEdit = ref({ width: 0, height: 0, unit: 'cm' })
const frameStyleEdit = ref({ color: '#000000', thickness: 1 })
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

const showSaveLayoutModal = ref(false)
const layoutName = ref('')

// Lock body scroll when any modal is open (prevents background scrolling on mobile)
const isAnyModalOpen = computed(() => {
  return !!(showFramePicker.value || selectedPlacementIndex.value !== null || showRecropModal.value || showWallRecropModal.value || showSaveLayoutModal.value)
})

watch(isAnyModalOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    pickerTab.value = 'public'
  }
  try {
    const fetchOwn = authStore.isAuthenticated ? picturesStore.fetchPictures() : Promise.resolve()
    await Promise.all([
      wallsStore.fetchWall(parseInt(route.params.id)),
      fetchOwn,
      picturesStore.fetchPublicPictures()
    ])
    if (!wallsStore.currentWall) {
      error.value = 'Wall not found'
    }
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'Wall not found'
    } else if (err.response?.status === 403) {
      error.value = 'This wall is private'
    } else {
      error.value = 'Failed to load wall'
    }
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
})

const wall = computed(() => wallsStore.currentWall)
const isOwner = computed(() =>
  authStore.isAuthenticated && authStore.user?.id === wall.value?.user_id
)

const allFrames = computed(() => {
  const frames = []
  const seenPictureIds = new Set()

  const addFromPicture = (picture, isPublic) => {
    if (seenPictureIds.has(picture.id)) return
    seenPictureIds.add(picture.id)
    if (picture.frames && picture.frames.length > 0) {
      picture.frames.forEach(frame => {
        frames.push({
          ...frame,
          pictureName: picture.name,
          pictureImage: picture.thumbnail_path || picture.image_path,
          isPublic
        })
      })
    } else {
      frames.push({
        id: null,
        pictureId: picture.id,
        pictureName: picture.name,
        pictureImage: picture.thumbnail_path || picture.image_path,
        dimensions: { cm: { width: 20, height: 25, depth: 2 } },
        styling: { frame_color: '#8B4513', frame_thickness: 1 },
        isPublic
      })
    }
  }

  if (authStore.isAuthenticated) {
    picturesStore.pictures.forEach(p => addFromPicture(p, false))
  }
  picturesStore.publicPictures.forEach(p => addFromPicture(p, true))

  return frames
})

const findFrameForPlacement = (placement) => {
  return allFrames.value.find(f =>
    placement.frame_id
      ? f.id === placement.frame_id
      : (placement.picture_id && f.pictureId === placement.picture_id)
  ) || null
}

// Frames available to add (not already placed on this wall)
const _placedIds = computed(() => ({
  frameIds: new Set((wall.value?.frame_placements || []).map(p => p.frame_id).filter(Boolean)),
  pictureIds: new Set((wall.value?.frame_placements || []).map(p => p.picture_id).filter(Boolean))
}))

const _isNotPlaced = (frame) => {
  return frame.pictureId
    ? !_placedIds.value.pictureIds.has(frame.pictureId)
    : !_placedIds.value.frameIds.has(frame.id)
}

const availableMyFrames = computed(() =>
  allFrames.value.filter(f => !f.isPublic && _isNotPlaced(f))
)

const availablePublicFrames = computed(() =>
  allFrames.value.filter(f => f.isPublic && _isNotPlaced(f))
)

const availableFrames = computed(() => {
  if (!authStore.isAuthenticated) return availablePublicFrames.value
  return pickerTab.value === 'my' ? availableMyFrames.value : availablePublicFrames.value
})

const addFrame = async (frame) => {
  try {
    saving.value = true
    const placement = frame.pictureId
      ? { picture_id: frame.pictureId, position: { x: 0, y: 0 }, rotation: { x: 0, y: 0, z: 0 }, scale: 1.0 }
      : { frame_id: frame.id, position: { x: 0, y: 0 }, rotation: { x: 0, y: 0, z: 0 }, scale: 1.0 }
    await wallsStore.addFramePlacement(wall.value.id, placement)
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

const toggleFrameVisibility = async (placementIndex) => {
  try {
    saving.value = true
    const placements = [...(wall.value.frame_placements || [])]
    const current = placements[placementIndex]
    placements[placementIndex] = { ...current, visible: current.visible === false }
    await wallsStore.updateWall(wall.value.id, { frame_placements: placements })
  } catch (err) {
    error.value = 'Failed to update frame visibility'
  } finally {
    saving.value = false
  }
}

const savedLayouts = computed(() => wall.value?.scene_config?.layouts || [])

const openSaveLayoutModal = () => {
  layoutName.value = `Layout ${savedLayouts.value.length + 1}`
  showSaveLayoutModal.value = true
}

const saveLayout = async () => {
  showSaveLayoutModal.value = false
  try {
    saving.value = true
    const thumbnail = wallViewerRef.value?.captureScreenshot() || null
    const layouts = JSON.parse(JSON.stringify(wall.value?.scene_config?.layouts || []))
    layouts.push({
      id: Date.now().toString(),
      name: layoutName.value.trim() || `Layout ${layouts.length + 1}`,
      created_at: new Date().toISOString(),
      frame_placements: JSON.parse(JSON.stringify(wall.value.frame_placements || [])),
      width_cm: wall.value.width_cm,
      height_cm: wall.value.height_cm,
      thumbnail
    })
    const scene_config = { ...(wall.value.scene_config || {}), layouts }
    await wallsStore.updateWall(wall.value.id, { scene_config })
  } catch (err) {
    error.value = 'Failed to save layout'
  } finally {
    saving.value = false
  }
}

const restoreLayout = async (layout) => {
  try {
    saving.value = true
    await wallsStore.updateWall(wall.value.id, {
      frame_placements: JSON.parse(JSON.stringify(layout.frame_placements)),
      width_cm: layout.width_cm,
      height_cm: layout.height_cm
    })
  } catch (err) {
    error.value = 'Failed to restore layout'
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
  return findFrameForPlacement(selectedPlacement.value)
})

// Get the picture for the selected frame
const selectedPicture = computed(() => {
  if (!selectedFrame.value) return null
  const allPictures = [...picturesStore.pictures, ...picturesStore.publicPictures]
  return allPictures.find(p =>
    (selectedFrame.value.id && p.frames?.some(f => f.id === selectedFrame.value.id)) ||
    (selectedFrame.value.pictureId && p.id === selectedFrame.value.pictureId)
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
    // Set initial label modes based on current position
    const wCm = wall.value?.width_cm || 0
    const hCm = wall.value?.height_cm || 0
    const xCm = (wCm / 2) + (pos.x * 100)
    const yCm = (hCm / 2) + (pos.y * 100)
    xLabelMode.value = (wCm > 0 && xCm / wCm > 0.6) ? 'right' : 'left'
    yLabelMode.value = (hCm > 0 && yCm / hCm > 0.6) ? 'ceiling' : 'floor'
  }
}

// Update frame position
const savePosition = async () => {
  if (selectedPlacementIndex.value === null) return

  savingPosition.value = true
  saveError.value = ''
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
    closeFrameEditor()
  } catch (err) {
    console.error('Failed to update position:', err)
    saveError.value = 'Failed to update position. Please try again.'
  } finally {
    savingPosition.value = false
  }
}

const resetPosition = () => {
  editingPosition.value = { ...savedPosition.value }
}

// Default wall size when dimensions are not explicitly set: 8 ft × 8 ft
const WALL_DEFAULT_CM = 8 * 30.48 // 243.84 cm

// Position display: convert internal meters (center-based) to wall-relative measurements
const wallWidthM = computed(() => ((wall.value?.width_cm || WALL_DEFAULT_CM) * 0.01))
const wallHeightM = computed(() => ((wall.value?.height_cm || WALL_DEFAULT_CM) * 0.01))
const wallWidthCmVal = computed(() => wall.value?.width_cm || WALL_DEFAULT_CM)
const wallHeightCmVal = computed(() => wall.value?.height_cm || WALL_DEFAULT_CM)

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

// Hysteresis-based label modes: flip at 60% going one way, flip back at 40% (60% from other side)
const xLabelMode = ref('left') // 'left' or 'right'
const yLabelMode = ref('floor') // 'floor' or 'ceiling'

// Watch position and apply hysteresis thresholds
watch(posFromLeftCm, (val) => {
  const w = wallWidthCmVal.value
  if (w <= 0) return
  const pct = val / w
  if (xLabelMode.value === 'left' && pct > 0.6) {
    xLabelMode.value = 'right'
  } else if (xLabelMode.value === 'right' && pct < 0.4) {
    xLabelMode.value = 'left'
  }
})

watch(posFromFloorCm, (val) => {
  const h = wallHeightCmVal.value
  if (h <= 0) return
  const pct = val / h
  if (yLabelMode.value === 'floor' && pct > 0.6) {
    yLabelMode.value = 'ceiling'
  } else if (yLabelMode.value === 'ceiling' && pct < 0.4) {
    yLabelMode.value = 'floor'
  }
})

// Display value: distance from the relevant edge in cm
const xDisplayCm = computed({
  get: () => xLabelMode.value === 'left' ? posFromLeftCm.value : +(wallWidthCmVal.value - posFromLeftCm.value).toFixed(1),
  set: (val) => {
    posFromLeftCm.value = xLabelMode.value === 'left' ? val : +(wallWidthCmVal.value - val).toFixed(1)
  }
})

const yDisplayCm = computed({
  get: () => yLabelMode.value === 'floor' ? posFromFloorCm.value : +(wallHeightCmVal.value - posFromFloorCm.value).toFixed(1),
  set: (val) => {
    posFromFloorCm.value = yLabelMode.value === 'floor' ? val : +(wallHeightCmVal.value - val).toFixed(1)
  }
})

const xLabel = computed(() => xLabelMode.value === 'left' ? 'from left' : 'from right')
const yLabel = computed(() => yLabelMode.value === 'floor' ? 'from floor' : 'from ceiling')

const posXFt = ref(0)
const posXIn = ref(0)
const posYFt = ref(0)
const posYIn = ref(0)

const syncFtInFromCm = () => {
  const xfi = cmToFtIn(Math.max(0, xDisplayCm.value))
  posXFt.value = xfi.ft
  posXIn.value = xfi.inches
  const yfi = cmToFtIn(Math.max(0, yDisplayCm.value))
  posYFt.value = yfi.ft
  posYIn.value = yfi.inches
}

const applyFtInToPosition = (axis) => {
  if (axis === 'x') {
    xDisplayCm.value = +ftInToCm(posXFt.value || 0, posXIn.value || 0).toFixed(1)
  } else {
    yDisplayCm.value = +ftInToCm(posYFt.value || 0, posYIn.value || 0).toFixed(1)
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

// Format a placement position as human-readable with smart left/right, floor/ceiling
const formatPlacementPosition = (placement) => {
  const wCm = wall.value?.width_cm || 0
  const hCm = wall.value?.height_cm || 0
  const xCm = (wCm / 2) + ((placement.position?.x || 0) * 100)
  const yCm = (hCm / 2) + ((placement.position?.y || 0) * 100)

  const useRight = wCm > 0 && (xCm / wCm) > 0.6
  const useCeiling = hCm > 0 && (yCm / hCm) > 0.6

  const xVal = useRight ? Math.max(0, wCm - xCm) : Math.max(0, xCm)
  const yVal = useCeiling ? Math.max(0, hCm - yCm) : Math.max(0, yCm)
  const xFtIn = cmToFtIn(xVal)
  const yFtIn = cmToFtIn(yVal)

  const xDir = useRight ? 'from right' : 'from left'
  const yDir = useCeiling ? 'from ceiling' : 'from floor'
  return `${xFtIn.ft}'${xFtIn.inches}" ${xDir}, ${yFtIn.ft}'${yFtIn.inches}" ${yDir}`
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
  // Default to ft & in
  const wFtIn = cmToFtIn(wall.value?.width_cm || 0)
  const hFtIn = cmToFtIn(wall.value?.height_cm || 0)
  wallEdit.value = {
    name: wall.value?.name || '',
    description: wall.value?.description || '',
    width: wall.value?.width_cm || 0,
    height: wall.value?.height_cm || 0,
    unit: 'ft',
    widthFt: wFtIn.ft,
    widthIn: wFtIn.inches,
    heightFt: hFtIn.ft,
    heightIn: hFtIn.inches
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

// Wall image editing (recrop and upload)
const startWallRecrop = () => {
  // Cache-bust so the browser fetches a fresh CORS-enabled copy (avoids opaque-cache canvas taint)
  const base = getImageUrl(wall.value.original_image_path || wall.value.image_path)
  wallRecropImageUrl.value = `${base}?t=${Date.now()}`
  wallCroppedImage.value = null
  showWallRecropModal.value = true
}

const handleWallCrop = (cropData) => {
  wallCroppedImage.value = cropData
}

const cancelWallRecrop = () => {
  showWallRecropModal.value = false
  wallCroppedImage.value = null
  saveError.value = ''
}

const saveWallRecrop = async () => {
  if (!wallCroppedImage.value?.blob) {
    saveError.value = 'Unable to export cropped image. Try uploading a new photo instead.'
    return
  }

  savingWallImage.value = true
  saveError.value = ''
  try {
    const file = new File([wallCroppedImage.value.blob], 'wall-recropped.jpg', { type: 'image/jpeg' })
    await wallsStore.updateWallImage(wall.value.id, file)
    showWallRecropModal.value = false
    wallCroppedImage.value = null
  } catch (err) {
    console.error('Failed to save wall image:', err)
    saveError.value = 'Failed to save wall image. Please try again.'
  } finally {
    savingWallImage.value = false
  }
}

const triggerWallImageUpload = () => {
  wallImageInput.value?.click()
}

const handleWallImageUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  savingWallImage.value = true
  try {
    await wallsStore.updateWallImage(wall.value.id, file)
  } catch (err) {
    console.error('Failed to upload wall image:', err)
    error.value = 'Failed to upload wall image'
  } finally {
    savingWallImage.value = false
    // Reset input so same file can be selected again
    if (wallImageInput.value) wallImageInput.value.value = ''
  }
}

// Frame dimension editing
const startEditFrameDimensions = () => {
  if (!selectedFrame.value) return
  const unit = 'cm' // Default to cm
  frameDimensionEdit.value = {
    width: selectedFrame.value.dimensions?.cm?.width || 0,
    height: selectedFrame.value.dimensions?.cm?.height || 0,
    unit: unit
  }
  // Load frame styling (thickness is stored in inches, convert to selected unit)
  const thicknessInches = selectedFrame.value.styling?.frame_thickness || 1
  frameStyleEdit.value = {
    color: selectedFrame.value.styling?.frame_color || '#000000',
    thickness: unit === 'cm' ? thicknessInches * 2.54 : thicknessInches
  }
  showCustomColorPicker.value = false
  editingFrameDimensions.value = true
}

const cancelEditFrameDimensions = () => {
  editingFrameDimensions.value = false
}

const saveFrameDimensions = async () => {
  if (!selectedFrame.value || !selectedPicture.value) return
  savingFrameEdit.value = true
  try {
    // Convert thickness to inches for API (thickness is always stored in inches on backend)
    const thicknessInches = frameDimensionEdit.value.unit === 'cm'
      ? frameStyleEdit.value.thickness / 2.54
      : frameStyleEdit.value.thickness

    await picturesStore.updateFrame(selectedPicture.value.id, selectedFrame.value.id, {
      width: frameDimensionEdit.value.width,
      height: frameDimensionEdit.value.height,
      unit: frameDimensionEdit.value.unit,
      frame_color: frameStyleEdit.value.color,
      frame_thickness: thicknessInches
    })
    editingFrameDimensions.value = false
    showCustomColorPicker.value = false
    await picturesStore.fetchPictures()
  } catch (err) {
    console.error('Failed to update frame dimensions:', err)
    error.value = 'Failed to update dimensions'
  } finally {
    savingFrameEdit.value = false
  }
}


// Recrop functionality
const startRecrop = () => {
  if (!selectedPicture.value) return
  const base = getImageUrl(selectedPicture.value.original_image_path || selectedPicture.value.image_path)
  recropImageUrl.value = `${base}?t=${Date.now()}`
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
  if (!croppedImage.value?.blob || !selectedPicture.value) {
    saveError.value = 'Unable to export cropped image. Try uploading a new photo instead.'
    return
  }

  savingRecrop.value = true
  saveError.value = ''
  try {
    const file = new File([croppedImage.value.blob], 'recropped.jpg', { type: 'image/jpeg' })
    const formData = new FormData()
    formData.append('image', file)

    await api.put(`/pictures/${selectedPicture.value.id}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

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
    saveError.value = 'Failed to save recropped image. Please try again.'
  } finally {
    savingRecrop.value = false
  }
}

// Reset frame edit states when closing editor
const closeFrameEditor = () => {
  selectedPlacementIndex.value = null
  editingFrameDimensions.value = false
  showCustomColorPicker.value = false
  showRecropModal.value = false
  saveError.value = ''
}

// Get frame dimensions for preview
const getFrameDimensions = (frame) => {
  if (frame?.dimensions?.cm) {
    // Use editing values if currently editing this frame
    if (editingFrameDimensions.value && frame.id === selectedFrame.value?.id) {
      return {
        widthCm: frameDimensionEdit.value.unit === 'cm'
          ? frameDimensionEdit.value.width
          : frameDimensionEdit.value.width * 2.54,
        heightCm: frameDimensionEdit.value.unit === 'cm'
          ? frameDimensionEdit.value.height
          : frameDimensionEdit.value.height * 2.54,
        frameColor: frameStyleEdit.value.color,
        frameThickness: frameDimensionEdit.value.unit === 'cm'
          ? frameStyleEdit.value.thickness / 2.54
          : frameStyleEdit.value.thickness
      }
    }

    return {
      widthCm: frame.dimensions.cm.width || 20,
      heightCm: frame.dimensions.cm.height || 25,
      frameColor: frame.styling?.frame_color || '#8B4513',
      frameThickness: frame.styling?.frame_thickness || 1
    }
  }
  return { widthCm: 20, heightCm: 25, frameColor: '#8B4513', frameThickness: 1 }
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
      <div class="flex gap-3 justify-center">
        <button @click="router.back()" class="btn btn-secondary">Go Back</button>
        <router-link to="/public-gallery" class="btn btn-secondary">Public Gallery</router-link>
      </div>
    </div>

    <!-- Editor -->
    <div v-else-if="wall">
      <!-- Guest / public-viewer banner -->
      <div v-if="!authStore.isAuthenticated" class="mb-4 p-3 bg-primary-900/40 border border-primary-600 rounded-lg text-sm text-primary-300 flex items-start gap-2">
        <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          You're viewing as a guest — add frames, rearrange, and save layouts freely.
          <router-link to="/register" class="underline hover:text-white ml-1">Create an account</router-link> to keep your walls private.
        </span>
      </div>

      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">{{ wall.name }}</h1>
          <p class="text-gray-400">Edit frame placements</p>
        </div>
        <div class="flex gap-3">
          <button @click="showFramePicker = true" class="btn btn-primary">
            Add Frame
          </button>
          <router-link v-if="authStore.isAuthenticated" :to="`/ar/${wall.id}`" class="btn btn-secondary">
            AR View
          </router-link>
        </div>
      </div>

      <!-- 3D Wall Viewer -->
      <div class="card mb-6">
        <div class="h-96">
          <WallViewer
            ref="wallViewerRef"
            :wallImageUrl="wall.image_path ? getImageUrl(wall.image_path) : null"
            :wallBackgroundColor="wall.background_color || null"
            :wallWidthCm="wall.width_cm || 0"
            :wallHeightCm="wall.height_cm || 0"
            :framePlacements="wall.frame_placements || []"
            :frames="allFrames"
            @frameSelected="selectFrame"
            @frameMoved="onFrameMoved"
          />
        </div>
        <p class="text-xs text-gray-500 mt-2 text-center">Left-click and drag frames to move them. Right-click and drag to rotate the view.</p>
        <div class="mt-3 flex justify-center">
          <button
            @click="openSaveLayoutModal"
            :disabled="saving"
            class="btn btn-secondary text-sm"
          >
            {{ saving ? 'Saving...' : 'Save Layout' }}
          </button>
        </div>
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
                  {{ (wall.width_cm / 2.54).toFixed(1) }}" x {{ (wall.height_cm / 2.54).toFixed(1) }}"
                  ({{ wall.width_cm.toFixed(1) }} x {{ wall.height_cm.toFixed(1) }} cm)
                </template>
                <template v-else>
                  8 ft × 8 ft (default)
                </template>
              </p>
            </template>
          </div>
          <button
            v-if="!editingWall && isOwner"
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
              :class="wallEdit.unit === 'ft' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              ft &amp; in
            </button>
            <button
              @click="toggleWallUnit"
              class="px-3 py-1 rounded text-xs font-medium transition"
              :class="wallEdit.unit === 'cm' ? 'bg-primary-500 text-white' : 'bg-dark-100 text-gray-400 border border-gray-600'"
            >
              cm
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

          <!-- Wall Image Actions -->
          <div class="border-t border-gray-700 pt-4 mt-4">
            <label class="block text-sm text-gray-400 mb-2">Wall Photo</label>
            <div class="flex gap-2">
              <button
                @click="startWallRecrop"
                :disabled="savingWallImage"
                class="btn btn-secondary flex-1 text-sm"
              >
                Recrop Photo
              </button>
              <button
                @click="triggerWallImageUpload"
                :disabled="savingWallImage"
                class="btn btn-secondary flex-1 text-sm"
              >
                {{ savingWallImage ? 'Uploading...' : 'Upload New Photo' }}
              </button>
            </div>
          </div>

          <div class="flex gap-3 mt-4">
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

      <!-- Hidden file input for wall image upload -->
      <input
        ref="wallImageInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handleWallImageUpload"
      />

      <!-- Placed frames list -->
      <div class="card mb-4">
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
            :class="{ 'opacity-50': placement.visible === false }"
          >
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-dark-100 rounded overflow-hidden flex-shrink-0">
                <img
                  v-if="findFrameForPlacement(placement)?.pictureImage"
                  :src="getImageUrl(findFrameForPlacement(placement).pictureImage)"
                  class="w-full h-full object-cover"
                />
              </div>
              <div>
                <p class="font-medium">
                  {{ findFrameForPlacement(placement)?.pictureName || 'Unknown' }}
                </p>
                <p class="text-sm text-gray-400">
                  {{ formatPlacementPosition(placement) }}
                </p>
              </div>
            </div>
            <button
              @click.stop="toggleFrameVisibility(index)"
              class="text-gray-400 hover:text-gray-200 transition-colors flex-shrink-0"
              :title="placement.visible === false ? 'Show frame' : 'Hide frame'"
            >
              <svg v-if="placement.visible === false" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Saved Layouts -->
      <div class="card">
        <h3 class="font-semibold mb-4">Saved Layouts ({{ savedLayouts.length }})</h3>

        <div v-if="!savedLayouts.length" class="text-center py-6 text-gray-400">
          No layouts saved yet. Click "Save Layout" above to capture the current arrangement.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="layout in savedLayouts"
            :key="layout.id"
            @click="restoreLayout(layout)"
            class="flex items-center gap-3 bg-dark-300 rounded-lg p-3 cursor-pointer hover:ring-2 hover:ring-primary-500 transition"
          >
            <div class="w-12 h-12 bg-dark-100 rounded overflow-hidden flex-shrink-0">
              <img
                v-if="layout.thumbnail"
                :src="layout.thumbnail"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="font-medium">{{ layout.name }}</p>
              <p class="text-sm text-gray-400">
                {{ layout.frame_placements?.length || 0 }} frame{{ (layout.frame_placements?.length || 0) !== 1 ? 's' : '' }}
                &middot;
                {{ new Date(layout.created_at).toLocaleDateString() }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fallback: wall is null after loading -->
    <div v-else class="text-center py-12">
      <p class="text-gray-400 mb-4">Wall not found or not accessible.</p>
      <div class="flex gap-3 justify-center">
        <button @click="router.back()" class="btn btn-secondary">Go Back</button>
        <router-link to="/public-gallery" class="btn btn-secondary">Public Gallery</router-link>
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

        <!-- My Frames / Public tabs (authenticated only) -->
        <div v-if="authStore.isAuthenticated" class="flex gap-2 mb-4">
          <button
            @click="pickerTab = 'my'"
            class="px-3 py-1.5 rounded-lg text-sm transition"
            :class="pickerTab === 'my' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
          >
            My Frames ({{ availableMyFrames.length }})
          </button>
          <button
            @click="pickerTab = 'public'"
            class="px-3 py-1.5 rounded-lg text-sm transition"
            :class="pickerTab === 'public' ? 'bg-primary-600 text-white' : 'bg-dark-300 text-gray-400 hover:text-white'"
          >
            Public ({{ availablePublicFrames.length }})
          </button>
        </div>

        <div v-if="availableFrames.length === 0" class="text-center py-6">
          <p class="text-gray-400 mb-4">
            <template v-if="!authStore.isAuthenticated">
              No public frames available yet. Capture a frame to add it here.
            </template>
            <template v-else-if="pickerTab === 'my' && availableMyFrames.length === 0">
              No personal frames available. Capture a frame first.
            </template>
            <template v-else>
              All frames are already placed on this wall.
            </template>
          </p>
          <div class="flex gap-2 justify-center">
            <router-link to="/capture/frame" class="btn btn-primary">
              Capture Frame
            </router-link>
            <router-link v-if="!authStore.isAuthenticated" to="/capture/wall" class="btn btn-secondary">
              Capture Wall
            </router-link>
          </div>
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
            :frameThickness="getFrameDimensions(selectedFrame).frameThickness"
            :maxWidth="300"
            :maxHeight="300"
          />
        </div>

        <!-- Recrop button (owner only) -->
        <div v-if="authStore.isAuthenticated" class="mb-4">
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

        <!-- Frame Properties (Dimensions, Thickness, Color) -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold">Frame Properties</h3>
            <button
              v-if="!editingFrameDimensions && authStore.isAuthenticated"
              @click="startEditFrameDimensions"
              class="text-gray-400 hover:text-primary-400 text-sm"
            >
              Edit
            </button>
          </div>
          <!-- Display mode -->
          <div v-if="!editingFrameDimensions" class="space-y-2">
            <div>
              <span class="text-xs text-gray-400">Dimensions:</span>
              <p class="text-sm text-gray-300">
                {{ selectedFrame.dimensions?.inches?.width?.toFixed(1) }}" x {{ selectedFrame.dimensions?.inches?.height?.toFixed(1) }}"
                ({{ selectedFrame.dimensions?.cm?.width?.toFixed(1) }} x {{ selectedFrame.dimensions?.cm?.height?.toFixed(1) }} cm)
              </p>
            </div>
            <div>
              <span class="text-xs text-gray-400">Thickness:</span>
              <p class="text-sm text-gray-300">{{ selectedFrame.styling?.frame_thickness || 1 }}"</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-400">Color:</span>
              <span
                class="w-5 h-5 rounded-full border border-gray-500 inline-block"
                :style="{ backgroundColor: selectedFrame.styling?.frame_color || '#8B4513' }"
              ></span>
              <span class="text-sm text-gray-300">{{ selectedFrame.styling?.frame_color || '#8B4513' }}</span>
            </div>
          </div>
          <!-- Edit mode -->
          <div v-else class="bg-dark-300 rounded-lg p-3 space-y-3">
            <!-- Dimensions -->
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

            <!-- Frame Thickness -->
            <div>
              <label class="block text-xs text-gray-400 mb-1">
                Frame Thickness ({{ frameDimensionEdit.unit }})
              </label>
              <input
                v-model.number="frameStyleEdit.thickness"
                type="number"
                :min="frameDimensionEdit.unit === 'cm' ? 0.6 : 0.25"
                :max="frameDimensionEdit.unit === 'cm' ? 12.7 : 5"
                :step="frameDimensionEdit.unit === 'cm' ? 0.1 : 0.25"
                class="w-full px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
              />
            </div>

            <!-- Frame Color -->
            <div>
              <label class="block text-xs text-gray-400 mb-2">Frame Color</label>
              <div class="flex gap-2 flex-wrap">
                <button
                  v-for="preset in presetColors"
                  :key="preset.value"
                  @click="frameStyleEdit.color = preset.value; showCustomColorPicker = false"
                  type="button"
                  class="flex items-center gap-2 px-2 py-1 rounded border-2 transition text-xs"
                  :class="frameStyleEdit.color === preset.value && !showCustomColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
                >
                  <span
                    class="w-4 h-4 rounded-full border border-gray-500"
                    :style="{ backgroundColor: preset.value }"
                  ></span>
                  <span>{{ preset.label }}</span>
                </button>
                <button
                  @click="showCustomColorPicker = !showCustomColorPicker"
                  type="button"
                  class="flex items-center gap-2 px-2 py-1 rounded border-2 transition text-xs"
                  :class="showCustomColorPicker ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
                >
                  <span
                    class="w-4 h-4 rounded-full border border-gray-500"
                    :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }"
                  ></span>
                  <span>Custom</span>
                </button>
              </div>
              <div v-if="showCustomColorPicker" class="mt-2">
                <input
                  type="color"
                  v-model="frameStyleEdit.color"
                  class="w-full h-8 rounded cursor-pointer bg-transparent border border-gray-600"
                />
              </div>
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

        <!-- Position editing -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Position on Wall</h3>
          <p class="text-sm text-gray-400 mb-3">Distance from wall edges</p>

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
            <!-- Left column: X slider + X input + Y input + buttons -->
            <div class="flex-1">
              <!-- X Position -->
              <div class="mb-3">
                <label class="block text-sm text-gray-400 mb-1">X Position <span class="text-gray-500">({{ xLabel }})</span></label>
                <input
                  type="range"
                  v-model.number="posFromLeftCm"
                  :min="0"
                  :max="wall?.width_cm || 300"
                  step="0.5"
                  class="w-full"
                  @input="positionUnit === 'ft' && syncFtInFromCm()"
                />
                <div v-if="positionUnit === 'cm'" class="mt-1">
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      v-model.number="xDisplayCm"
                      step="0.1"
                      min="0"
                      class="w-full px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400 whitespace-nowrap">cm {{ xLabel }}</span>
                  </div>
                </div>
                <div v-else class="mt-1 flex items-center gap-1">
                  <input
                    type="number"
                    v-model.number="posXFt"
                    min="0"
                    @input="applyFtInToPosition('x')"
                    class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-xs text-gray-400">ft</span>
                  <input
                    type="number"
                    v-model.number="posXIn"
                    step="0.1"
                    min="0"
                    max="11.9"
                    @input="applyFtInToPosition('x')"
                    class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                  />
                  <span class="text-xs text-gray-400 whitespace-nowrap">in {{ xLabel }}</span>
                </div>
              </div>

              <!-- Y Position input (below X) -->
              <div class="mb-3">
                <label class="block text-sm text-gray-400 mb-1">Y Position <span class="text-gray-500">({{ yLabel }})</span></label>
                <template v-if="positionUnit === 'cm'">
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      v-model.number="yDisplayCm"
                      step="0.1"
                      min="0"
                      class="w-full px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400 whitespace-nowrap">cm {{ yLabel }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      v-model.number="posYFt"
                      min="0"
                      @input="applyFtInToPosition('y')"
                      class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400">ft</span>
                    <input
                      type="number"
                      v-model.number="posYIn"
                      step="0.1"
                      min="0"
                      max="11.9"
                      @input="applyFtInToPosition('y')"
                      class="w-16 px-2 py-1 bg-dark-100 border border-gray-600 rounded text-sm"
                    />
                    <span class="text-xs text-gray-400 whitespace-nowrap">in {{ yLabel }}</span>
                  </div>
                </template>
              </div>

              <!-- Buttons -->
              <div class="space-y-2">
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
                <p v-if="saveError" class="text-red-400 text-xs mt-2">{{ saveError }}</p>
              </div>
            </div>

            <!-- Right column: Y vertical slider only -->
            <div class="flex flex-col items-center" style="width: 60px;">
              <span class="text-xs text-gray-500 mb-1">Y</span>
              <div class="flex items-center overflow-hidden" style="height: 180px; width: 60px;">
                <input
                  type="range"
                  v-model.number="posFromFloorCm"
                  :min="0"
                  :max="wall?.height_cm || 300"
                  step="0.5"
                  class="vertical-slider"
                  style="width: 180px; transform: rotate(-90deg); transform-origin: center center; margin-left: -60px;"
                  @input="positionUnit === 'ft' && syncFtInFromCm()"
                />
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
      <div class="card max-w-5xl w-full max-h-[95vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">Recrop Image</h2>
          <button @click="cancelRecrop" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p class="text-sm text-gray-400 mb-4">
          Drag the corners or edges to select the area you want to keep
        </p>

        <div class="mb-6">
          <ImageCropper
            :key="effectiveAspectRatio"
            :imageUrl="recropImageUrl"
            :aspectRatio="effectiveAspectRatio"
            @crop="handleCrop"
          />
        </div>

        <div v-if="recropAspectRatio" class="mb-6 flex items-center gap-2 bg-dark-300 rounded-lg p-3">
          <input
            type="checkbox"
            id="lockAspectRatioWall"
            v-model="lockAspectRatio"
            class="w-4 h-4 rounded border-gray-600 bg-dark-100 text-primary-500 focus:ring-primary-500"
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
            :disabled="!croppedImage?.blob || savingRecrop"
            class="btn btn-primary"
          >
            {{ savingRecrop ? 'Saving...' : 'Save Crop' }}
          </button>
        </div>
        <p v-if="saveError" class="text-red-400 text-xs mt-3 text-center">{{ saveError }}</p>
      </div>
    </div>

    <!-- Save Layout name modal -->
    <div
      v-if="showSaveLayoutModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click.self="showSaveLayoutModal = false"
    >
      <div class="card w-full max-w-sm">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold">Name This Layout</h2>
          <button @click="showSaveLayoutModal = false" class="text-gray-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <input
          v-model="layoutName"
          type="text"
          placeholder="e.g., Holiday arrangement"
          class="w-full px-3 py-2 bg-dark-100 border border-gray-600 rounded text-sm mb-4"
          @keyup.enter="saveLayout"
          autofocus
        />
        <div class="flex gap-3">
          <button @click="showSaveLayoutModal = false" class="btn btn-secondary flex-1 text-sm">
            Cancel
          </button>
          <button @click="saveLayout" class="btn btn-primary flex-1 text-sm">
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Wall Recrop modal -->
    <div
      v-if="showWallRecropModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-[60]"
      @click.self="cancelWallRecrop"
    >
      <div class="card max-w-5xl w-full max-h-[95vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">Recrop Wall Photo</h2>
          <button @click="cancelWallRecrop" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p class="text-sm text-gray-400 mb-4">
          Drag the corners or edges to select the wall area you want to keep
        </p>

        <div class="mb-6">
          <ImageCropper
            :imageUrl="wallRecropImageUrl"
            @crop="handleWallCrop"
          />
        </div>

        <div class="flex gap-3 justify-end">
          <button
            @click="cancelWallRecrop"
            class="btn bg-gray-600 hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            @click="saveWallRecrop"
            :disabled="!wallCroppedImage?.blob || savingWallImage"
            class="btn btn-primary"
          >
            {{ savingWallImage ? 'Saving...' : 'Save Crop' }}
          </button>
        </div>
        <p v-if="saveError" class="text-red-400 text-xs mt-3 text-center">{{ saveError }}</p>
      </div>
    </div>
  </div>
</template>
