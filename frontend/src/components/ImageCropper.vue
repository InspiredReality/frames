<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

const props = defineProps({
  imageUrl: {
    type: String,
    required: true
  },
  aspectRatio: {
    type: Number,
    default: null // null = free aspect ratio
  }
})

const emit = defineEmits(['crop'])

const containerRef = ref(null)
const imageRef = ref(null)
const isDragging = ref(false)
const isResizing = ref(false)
const resizeHandle = ref(null)

// Crop box state (in percentage of image)
const cropBox = ref({
  x: 10,
  y: 10,
  width: 80,
  height: 80
})

// Drag state
const dragStart = ref({ x: 0, y: 0 })
const cropStart = ref({ x: 0, y: 0, width: 0, height: 0 })

// Image dimensions
const imageDimensions = ref({ width: 0, height: 0 })

const cropStyle = computed(() => ({
  left: `${cropBox.value.x}%`,
  top: `${cropBox.value.y}%`,
  width: `${cropBox.value.width}%`,
  height: `${cropBox.value.height}%`
}))

// Overlay masks (darkened areas outside crop)
const overlayStyles = computed(() => {
  const { x, y, width, height } = cropBox.value
  return {
    top: { height: `${y}%` },
    bottom: { height: `${100 - y - height}%` },
    left: { top: `${y}%`, height: `${height}%`, width: `${x}%` },
    right: { top: `${y}%`, height: `${height}%`, width: `${100 - x - width}%` }
  }
})

const onImageLoad = () => {
  if (imageRef.value) {
    imageDimensions.value = {
      width: imageRef.value.naturalWidth,
      height: imageRef.value.naturalHeight
    }

    // If aspect ratio is set, adjust initial crop box
    if (props.aspectRatio) {
      adjustToAspectRatio()
    }

    emitCrop()
  }
}

const adjustToAspectRatio = () => {
  if (!props.aspectRatio || !imageDimensions.value.width) return

  const imgWidth = imageDimensions.value.width
  const imgHeight = imageDimensions.value.height
  const targetAspect = props.aspectRatio

  // Get current crop box center and area
  const centerX = cropBox.value.x + cropBox.value.width / 2
  const centerY = cropBox.value.y + cropBox.value.height / 2

  // Calculate current area in percentage units
  const currentArea = cropBox.value.width * cropBox.value.height

  // Calculate new dimensions that maintain the same area but with new aspect ratio
  // Area = width * height
  // Aspect = (width% * imgW) / (height% * imgH) = targetAspect
  // So: width% = height% * targetAspect * imgH / imgW
  // And: Area = height%^2 * targetAspect * imgH / imgW
  // So: height% = sqrt(Area * imgW / (targetAspect * imgH))

  const aspectFactor = targetAspect * imgHeight / imgWidth
  let newHeight = Math.sqrt(currentArea / aspectFactor)
  let newWidth = newHeight * aspectFactor

  // Ensure minimum size
  newWidth = Math.max(newWidth, 15)
  newHeight = Math.max(newHeight, 15)

  // Calculate new position to keep center
  let newX = centerX - newWidth / 2
  let newY = centerY - newHeight / 2

  // Constrain to bounds
  if (newX < 0) {
    newX = 0
  }
  if (newY < 0) {
    newY = 0
  }
  if (newX + newWidth > 100) {
    newX = 100 - newWidth
    if (newX < 0) {
      newX = 0
      newWidth = 100
      newHeight = newWidth / aspectFactor
    }
  }
  if (newY + newHeight > 100) {
    newY = 100 - newHeight
    if (newY < 0) {
      newY = 0
      newHeight = 100
      newWidth = newHeight * aspectFactor
    }
  }

  cropBox.value = {
    x: newX,
    y: newY,
    width: newWidth,
    height: newHeight
  }
}

const startDrag = (e) => {
  if (e.target.classList.contains('resize-handle')) return

  isDragging.value = true
  const rect = containerRef.value.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  dragStart.value = { x: clientX, y: clientY }
  cropStart.value = { ...cropBox.value }

  e.preventDefault()
}

const startResize = (e, handle) => {
  isResizing.value = true
  resizeHandle.value = handle

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  dragStart.value = { x: clientX, y: clientY }
  cropStart.value = { ...cropBox.value }

  e.preventDefault()
  e.stopPropagation()
}

const onMouseMove = (e) => {
  if (!isDragging.value && !isResizing.value) return

  const rect = containerRef.value.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  const deltaX = ((clientX - dragStart.value.x) / rect.width) * 100
  const deltaY = ((clientY - dragStart.value.y) / rect.height) * 100

  if (isDragging.value) {
    // Move crop box
    let newX = cropStart.value.x + deltaX
    let newY = cropStart.value.y + deltaY

    // Constrain to image bounds
    newX = Math.max(0, Math.min(newX, 100 - cropBox.value.width))
    newY = Math.max(0, Math.min(newY, 100 - cropBox.value.height))

    cropBox.value.x = newX
    cropBox.value.y = newY
  } else if (isResizing.value) {
    // Resize crop box
    let { x, y, width, height } = cropStart.value

    const handle = resizeHandle.value

    if (handle.includes('e')) {
      width = Math.max(10, Math.min(cropStart.value.width + deltaX, 100 - x))
    }
    if (handle.includes('w')) {
      const newWidth = Math.max(10, cropStart.value.width - deltaX)
      const maxMove = cropStart.value.x + cropStart.value.width - 10
      x = Math.max(0, Math.min(cropStart.value.x + deltaX, maxMove))
      width = cropStart.value.width + (cropStart.value.x - x)
    }
    if (handle.includes('s')) {
      height = Math.max(10, Math.min(cropStart.value.height + deltaY, 100 - y))
    }
    if (handle.includes('n')) {
      const newHeight = Math.max(10, cropStart.value.height - deltaY)
      const maxMove = cropStart.value.y + cropStart.value.height - 10
      y = Math.max(0, Math.min(cropStart.value.y + deltaY, maxMove))
      height = cropStart.value.height + (cropStart.value.y - y)
    }

    // Apply aspect ratio constraint if set
    if (props.aspectRatio) {
      const imgAspect = imageDimensions.value.width / imageDimensions.value.height
      const targetAspect = props.aspectRatio

      // Adjust height based on width
      const actualWidth = (width / 100) * imageDimensions.value.width
      const targetHeight = actualWidth / targetAspect
      height = (targetHeight / imageDimensions.value.height) * 100

      // Ensure it fits
      if (y + height > 100) {
        height = 100 - y
        const actualHeight = (height / 100) * imageDimensions.value.height
        width = (actualHeight * targetAspect / imageDimensions.value.width) * 100
      }
    }

    cropBox.value = { x, y, width, height }
  }

  e.preventDefault()
}

const onMouseUp = () => {
  if (isDragging.value || isResizing.value) {
    emitCrop()
  }
  isDragging.value = false
  isResizing.value = false
  resizeHandle.value = null
}

const emitCrop = () => {
  // Create cropped image data
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const img = imageRef.value

  if (!img) return

  // Calculate actual pixel coordinates
  const sx = (cropBox.value.x / 100) * img.naturalWidth
  const sy = (cropBox.value.y / 100) * img.naturalHeight
  const sw = (cropBox.value.width / 100) * img.naturalWidth
  const sh = (cropBox.value.height / 100) * img.naturalHeight

  canvas.width = sw
  canvas.height = sh

  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh)

  canvas.toBlob((blob) => {
    emit('crop', {
      blob,
      dataUrl: canvas.toDataURL('image/jpeg', 0.9),
      width: Math.round(sw),
      height: Math.round(sh),
      cropBox: { ...cropBox.value }
    })
  }, 'image/jpeg', 0.9)
}

// Reset crop to full image
const resetCrop = () => {
  cropBox.value = { x: 5, y: 5, width: 90, height: 90 }
  emitCrop()
}

watch(() => props.aspectRatio, () => {
  if (props.aspectRatio) {
    adjustToAspectRatio()
    emitCrop()
  }
})

onMounted(() => {
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.addEventListener('touchmove', onMouseMove, { passive: false })
  document.addEventListener('touchend', onMouseUp)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  document.removeEventListener('touchmove', onMouseMove)
  document.removeEventListener('touchend', onMouseUp)
})

defineExpose({ resetCrop, emitCrop })
</script>

<template>
  <div class="cropper-wrapper">
    <div ref="containerRef" class="cropper-container">
      <!-- Original image -->
      <img
        ref="imageRef"
        :src="imageUrl"
        @load="onImageLoad"
        class="cropper-image"
        draggable="false"
      />

      <!-- Overlay masks -->
      <div class="overlay overlay-top" :style="overlayStyles.top"></div>
      <div class="overlay overlay-bottom" :style="overlayStyles.bottom"></div>
      <div class="overlay overlay-left" :style="overlayStyles.left"></div>
      <div class="overlay overlay-right" :style="overlayStyles.right"></div>

      <!-- Crop box -->
      <div
        class="crop-box"
        :style="cropStyle"
        @mousedown="startDrag"
        @touchstart="startDrag"
      >
        <!-- Grid lines -->
        <div class="grid-line grid-line-h1"></div>
        <div class="grid-line grid-line-h2"></div>
        <div class="grid-line grid-line-v1"></div>
        <div class="grid-line grid-line-v2"></div>

        <!-- Resize handles -->
        <div class="resize-handle handle-n" @mousedown="(e) => startResize(e, 'n')" @touchstart="(e) => startResize(e, 'n')"></div>
        <div class="resize-handle handle-s" @mousedown="(e) => startResize(e, 's')" @touchstart="(e) => startResize(e, 's')"></div>
        <div class="resize-handle handle-e" @mousedown="(e) => startResize(e, 'e')" @touchstart="(e) => startResize(e, 'e')"></div>
        <div class="resize-handle handle-w" @mousedown="(e) => startResize(e, 'w')" @touchstart="(e) => startResize(e, 'w')"></div>
        <div class="resize-handle handle-ne" @mousedown="(e) => startResize(e, 'ne')" @touchstart="(e) => startResize(e, 'ne')"></div>
        <div class="resize-handle handle-nw" @mousedown="(e) => startResize(e, 'nw')" @touchstart="(e) => startResize(e, 'nw')"></div>
        <div class="resize-handle handle-se" @mousedown="(e) => startResize(e, 'se')" @touchstart="(e) => startResize(e, 'se')"></div>
        <div class="resize-handle handle-sw" @mousedown="(e) => startResize(e, 'sw')" @touchstart="(e) => startResize(e, 'sw')"></div>
      </div>
    </div>

    <!-- Reset button -->
    <button @click="resetCrop" class="reset-btn">
      Reset Crop
    </button>
  </div>
</template>

<style scoped>
.cropper-wrapper {
  width: 100%;
}

.cropper-container {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 0.5rem;
  background: #0f0f0f;
}

.cropper-image {
  display: block;
  width: 100%;
  height: auto;
  user-select: none;
  pointer-events: none;
}

.overlay {
  position: absolute;
  background: rgba(0, 0, 0, 0.6);
  pointer-events: none;
}

.overlay-top {
  top: 0;
  left: 0;
  right: 0;
}

.overlay-bottom {
  bottom: 0;
  left: 0;
  right: 0;
}

.overlay-left {
  left: 0;
}

.overlay-right {
  right: 0;
}

.crop-box {
  position: absolute;
  border: 2px solid #0ea5e9;
  cursor: move;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0);
}

/* Rule of thirds grid */
.grid-line {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  pointer-events: none;
}

.grid-line-h1, .grid-line-h2 {
  left: 0;
  right: 0;
  height: 1px;
}

.grid-line-h1 { top: 33.33%; }
.grid-line-h2 { top: 66.66%; }

.grid-line-v1, .grid-line-v2 {
  top: 0;
  bottom: 0;
  width: 1px;
}

.grid-line-v1 { left: 33.33%; }
.grid-line-v2 { left: 66.66%; }

/* Resize handles */
.resize-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  background: #0ea5e9;
  border: 2px solid #fff;
  border-radius: 50%;
  z-index: 10;
}

.handle-n { top: -10px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.handle-s { bottom: -10px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.handle-e { right: -10px; top: 50%; transform: translateY(-50%); cursor: e-resize; }
.handle-w { left: -10px; top: 50%; transform: translateY(-50%); cursor: w-resize; }
.handle-ne { top: -10px; right: -10px; cursor: ne-resize; }
.handle-nw { top: -10px; left: -10px; cursor: nw-resize; }
.handle-se { bottom: -10px; right: -10px; cursor: se-resize; }
.handle-sw { bottom: -10px; left: -10px; cursor: sw-resize; }

/* Touch-friendly larger handles on mobile */
@media (max-width: 640px) {
  .resize-handle {
    width: 28px;
    height: 28px;
  }

  .handle-n { top: -14px; }
  .handle-s { bottom: -14px; }
  .handle-e { right: -14px; }
  .handle-w { left: -14px; }
  .handle-ne { top: -14px; right: -14px; }
  .handle-nw { top: -14px; left: -14px; }
  .handle-se { bottom: -14px; right: -14px; }
  .handle-sw { bottom: -14px; left: -14px; }
}

.reset-btn {
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: #9ca3af;
  background: transparent;
  border: 1px solid #4b5563;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  color: #fff;
  border-color: #0ea5e9;
}
</style>
