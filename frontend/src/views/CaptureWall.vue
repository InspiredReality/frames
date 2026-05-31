<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import CameraCapture from '@/components/CameraCapture.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import QrCodeCard from '@/components/QrCodeCard.vue'
import { useWallsStore } from '@/store/walls'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const wallsStore = useWallsStore()
const authStore = useAuthStore()

const step = ref(1) // 1: capture/choose, 2: crop, 3: details
const capturedImage = ref(null)
const croppedImage = ref(null)
const wallName = ref('')
const wallDescription = ref('')
const wallUnit = ref('ft') // 'ft' or 'cm'
// Source of truth - always stored in cm. Default 5 ft × 5 ft.
const FT_5_IN_CM = 5 * 12 * 2.54 // 152.4
const wallWidthCm = ref(FT_5_IN_CM)
const wallHeightCm = ref(FT_5_IN_CM)
const loading = ref(false)
const error = ref('')
const lockAspectRatio = ref(false)

// Blank color wall state
const useBlankColor = ref(false)
const wallColor = ref('#e0e0e0')
const showCustomWallColor = ref(false)

const wallColorPresets = [
  { label: 'White', value: '#FFFFFF' },
  { label: 'Off-White', value: '#F5F5DC' },
  { label: 'Light Gray', value: '#D3D3D3' },
  { label: 'Gray', value: '#808080' },
  { label: 'Black', value: '#000000' },
  { label: 'Brown', value: '#8B4513' }
]

// Conversion constants
const INCHES_PER_FOOT = 12
const CM_PER_INCH = 2.54

// Computed display values for ft & in mode (derived from cm source of truth)
const displayWidthFt = computed({
  get: () => {
    if (!wallWidthCm.value) return ''
    const totalInches = wallWidthCm.value / CM_PER_INCH
    return Math.floor(totalInches / INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(val) || 0
    const inches = parseFloat(displayWidthIn.value) || 0
    wallWidthCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayWidthIn = computed({
  get: () => {
    if (!wallWidthCm.value) return ''
    const totalInches = wallWidthCm.value / CM_PER_INCH
    return Math.round(totalInches % INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(displayWidthFt.value) || 0
    const inches = parseFloat(val) || 0
    wallWidthCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayHeightFt = computed({
  get: () => {
    if (!wallHeightCm.value) return ''
    const totalInches = wallHeightCm.value / CM_PER_INCH
    return Math.floor(totalInches / INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(val) || 0
    const inches = parseFloat(displayHeightIn.value) || 0
    wallHeightCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

const displayHeightIn = computed({
  get: () => {
    if (!wallHeightCm.value) return ''
    const totalInches = wallHeightCm.value / CM_PER_INCH
    return Math.round(totalInches % INCHES_PER_FOOT) || ''
  },
  set: (val) => {
    const ft = parseFloat(displayHeightFt.value) || 0
    const inches = parseFloat(val) || 0
    wallHeightCm.value = (ft * INCHES_PER_FOOT + inches) * CM_PER_INCH
  }
})

// Computed display values for cm mode
const displayWidthCm = computed({
  get: () => wallWidthCm.value ? Math.round(wallWidthCm.value) : '',
  set: (val) => { wallWidthCm.value = parseFloat(val) || 0 }
})

const displayHeightCm = computed({
  get: () => wallHeightCm.value ? Math.round(wallHeightCm.value) : '',
  set: (val) => { wallHeightCm.value = parseFloat(val) || 0 }
})

// Toggle functions - just change display unit, no conversion needed
const selectFtIn = () => { wallUnit.value = 'ft' }
const selectCm = () => { wallUnit.value = 'cm' }

// Aspect ratio from wall dimensions — this is what the crop lock uses
const wallDimensionAspectRatio = computed(() => {
  if (wallWidthCm.value && wallHeightCm.value) {
    return wallWidthCm.value / wallHeightCm.value
  }
  return null
})

// Fallback: photo's own pixel ratio if no wall dimensions entered
const capturedAspectRatio = computed(() => {
  if (!capturedImage.value?.width || !capturedImage.value?.height) return null
  return capturedImage.value.width / capturedImage.value.height
})

const activeLockRatio = computed(() => wallDimensionAspectRatio.value ?? capturedAspectRatio.value)
const cropAspectRatio = computed(() => lockAspectRatio.value ? activeLockRatio.value : null)

// Reset lock when going back to capture
watch(step, (s) => { if (s === 1) lockAspectRatio.value = false })

// Get values in cm for saving (source of truth)
const getWidthInCm = () => wallWidthCm.value || null
const getHeightInCm = () => wallHeightCm.value || null

// ── Multi-photo & panorama ──────────────────────────────────────
const captureMode = ref('single') // 'single' | 'multi' | 'panorama'
const capturedImages = ref([])    // multi-photo mode accumulator
const panoramaFrames = ref([])    // panorama mode accumulator
const isPanoramaRecording = ref(false)
const panoramaProgress = ref(0)   // 0–100 drives the guide-line position
const stitching = ref(false)
const cameraCaptureRef = ref(null)
const multiFileInputRef = ref(null)

const MAX_MULTI = 10
const MAX_PANORAMA = 15
let guideIntervalId = null

const setMode = (mode) => {
  if (isPanoramaRecording.value) stopPanorama()
  captureMode.value = mode
  capturedImages.value = []
  panoramaFrames.value = []
  panoramaProgress.value = 0
  error.value = ''
}

const startPanorama = () => {
  panoramaFrames.value = []
  panoramaProgress.value = 0
  isPanoramaRecording.value = true
  cameraCaptureRef.value?.startAutoCapture(900)
  const start = Date.now()
  const dur = 20000 // guide crosses screen in 20 s
  guideIntervalId = setInterval(() => {
    if (!isPanoramaRecording.value) return
    panoramaProgress.value = Math.min(100, ((Date.now() - start) / dur) * 100)
    if (panoramaFrames.value.length >= MAX_PANORAMA) stopPanorama()
  }, 100)
}

const stopPanorama = () => {
  isPanoramaRecording.value = false
  cameraCaptureRef.value?.stopAutoCapture()
  if (guideIntervalId !== null) { clearInterval(guideIntervalId); guideIntervalId = null }
}

const moveImage = (idx, dir) => {
  const arr = [...capturedImages.value]
  ;[arr[idx], arr[idx + dir]] = [arr[idx + dir], arr[idx]]
  capturedImages.value = arr
}

const handleMultiFileUpload = async (event) => {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  const slots = MAX_MULTI - capturedImages.value.length
  const toProcess = files.slice(0, slots)

  const processFile = (file) => new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const c = document.createElement('canvas')
        c.width = img.width; c.height = img.height
        c.getContext('2d').drawImage(img, 0, 0)
        c.toBlob(
          blob => resolve({ blob, dataUrl: e.target.result, width: img.width, height: img.height }),
          'image/jpeg', 0.9
        )
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })

  const caps = await Promise.all(toProcess.map(processFile))
  capturedImages.value.push(...caps)
  event.target.value = ''
}

// Find the pixel overlap between the right edge of canvasA and left edge of canvasB.
// Samples a horizontal band in the middle, steps every 5 px to stay fast.
const findOverlap = (ca, cb) => {
  const ctxA = ca.getContext('2d')
  const ctxB = cb.getContext('2d')
  const sH = Math.min(ca.height, 60)
  const sy = Math.floor((ca.height - sH) / 2)
  const maxOv = Math.floor(Math.min(ca.width, cb.width) * 0.6)

  let best = 0, bestScore = Infinity
  for (let ov = 20; ov <= maxOv; ov += 5) {
    const dA = ctxA.getImageData(ca.width - ov, sy, ov, sH)
    const dB = ctxB.getImageData(0, sy, ov, sH)
    let score = 0
    for (let i = 0; i < dA.data.length; i += 16) {
      const dr = dA.data[i] - dB.data[i]
      const dg = dA.data[i + 1] - dB.data[i + 1]
      const db = dA.data[i + 2] - dB.data[i + 2]
      score += dr * dr + dg * dg + db * db
    }
    score /= dA.data.length / 16
    if (score < bestScore) { bestScore = score; best = ov }
  }
  // Only apply overlap when there is a confident match
  return bestScore < 4000 ? best : 0
}

const stitchHorizontally = async (frames, detectOverlap = false) => {
  if (!frames.length) return null
  if (frames.length === 1) return frames[0]

  const loadImg = (url) => new Promise((res) => {
    const img = new Image(); img.onload = () => res(img); img.src = url
  })
  const imgs = await Promise.all(frames.map(f => loadImg(f.dataUrl)))
  const targetH = Math.max(...imgs.map(i => i.naturalHeight))

  // Scale all images to the same height
  const canvases = imgs.map(img => {
    const s = targetH / img.naturalHeight
    const w = Math.round(img.naturalWidth * s)
    const c = document.createElement('canvas')
    c.width = w; c.height = targetH
    c.getContext('2d').drawImage(img, 0, 0, w, targetH)
    return c
  })

  const overlaps = detectOverlap
    ? canvases.slice(0, -1).map((ca, i) => findOverlap(ca, canvases[i + 1]))
    : canvases.slice(0, -1).map(() => 0)

  let totalW = canvases[0].width
  for (let i = 1; i < canvases.length; i++) totalW += canvases[i].width - overlaps[i - 1]

  const out = document.createElement('canvas')
  out.width = totalW; out.height = targetH
  const ctx = out.getContext('2d')
  let x = 0
  canvases.forEach((c, i) => {
    ctx.drawImage(c, x, 0)
    x += c.width - (i < overlaps.length ? overlaps[i] : 0)
  })

  return new Promise((res) => {
    out.toBlob(
      blob => res({ blob, dataUrl: out.toDataURL('image/jpeg', 0.9), width: out.width, height: out.height }),
      'image/jpeg', 0.9
    )
  })
}

const proceedWithStitching = async (frames, useOverlap = false) => {
  if (!frames.length) return
  stitching.value = true
  error.value = ''
  try {
    const result = await stitchHorizontally([...frames], useOverlap)
    if (!result) throw new Error('empty result')
    capturedImage.value = result
    croppedImage.value = result
    useBlankColor.value = false
    step.value = 2
  } catch {
    error.value = 'Failed to combine images. Please try again.'
  } finally {
    stitching.value = false
  }
}

onUnmounted(() => {
  if (isPanoramaRecording.value) stopPanorama()
})

// ── Event handlers ─────────────────────────────────────────────
const onCapture = (data) => {
  if (captureMode.value === 'single') {
    capturedImage.value = data
    croppedImage.value = data
    useBlankColor.value = false
    step.value = 2
  } else if (captureMode.value === 'multi') {
    if (capturedImages.value.length < MAX_MULTI) capturedImages.value.push(data)
  } else if (captureMode.value === 'panorama') {
    if (panoramaFrames.value.length < MAX_PANORAMA) panoramaFrames.value.push(data)
  }
}

const onCrop = (data) => {
  croppedImage.value = data
}

const confirmCrop = () => {
  step.value = 3
}

const onCameraError = (message) => {
  error.value = message
}

const selectBlankColor = () => {
  useBlankColor.value = true
  capturedImage.value = null
  croppedImage.value = null
  step.value = 2
}

const retake = () => {
  capturedImage.value = null
  croppedImage.value = null
  useBlankColor.value = false
  step.value = 1
  error.value = ''
  capturedImages.value = []
  panoramaFrames.value = []
  if (isPanoramaRecording.value) stopPanorama()
  panoramaProgress.value = 0
}

const saveWall = async () => {
  if (!wallName.value.trim()) {
    error.value = 'Please enter a name for your wall'
    return
  }

  loading.value = true
  error.value = ''

  try {
    let file = null
    let bgColor = null

    if (useBlankColor.value) {
      bgColor = wallColor.value
    } else {
      file = new File([croppedImage.value.blob], 'wall.jpg', { type: 'image/jpeg' })
    }

    await wallsStore.uploadWall(file, wallName.value, wallDescription.value, {
      width_cm: getWidthInCm(),
      height_cm: getHeightInCm()
    }, bgColor)

    router.push(authStore.isAuthenticated ? '/gallery' : '/public-gallery')
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save wall'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Guest notice -->
    <div v-if="!authStore.isAuthenticated" class="mb-4 p-3 bg-primary-900/40 border border-primary-600 rounded-lg text-sm text-primary-300 flex items-start gap-2">
      <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>
        You're capturing as a guest — this wall will be <strong>public</strong>.
        <router-link to="/register" class="underline hover:text-white">Create an account</router-link> to keep your captures private.
      </span>
    </div>

    <!-- Step indicator -->
    <div class="flex items-center justify-center mb-8">
      <div v-for="s in 3" :key="s" class="flex items-center">
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors"
          :class="step >= s ? 'bg-primary-500 text-white' : 'bg-dark-300 text-gray-400'"
        >{{ s }}</div>
        <div v-if="s < 3" class="w-12 h-1 mx-2" :class="step > s ? 'bg-primary-500' : 'bg-dark-300'"></div>
      </div>
    </div>

    <!-- Step labels -->
    <div class="flex justify-center gap-8 mb-6 text-sm text-gray-400">
      <span :class="step >= 1 ? 'text-primary-400' : ''">1. Take/Upload Photo</span>
      <span :class="step >= 2 ? 'text-primary-400' : ''">2. Crop & Size</span>
      <span :class="step >= 3 ? 'text-primary-400' : ''">3. Save to Gallery</span>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
      {{ error }}
    </div>

    <!-- ─── Step 1: Camera Capture ─────────────────────────────── -->
    <div v-if="step === 1">
      <h2 class="text-2xl font-bold mb-4 text-center">Capture Your Wall</h2>

      <!-- Capture mode tabs -->
      <div class="flex gap-1 mb-4 bg-dark-300 rounded-lg p-1">
        <button
          v-for="m in [
            { key: 'single',   label: 'Single Photo' },
            { key: 'multi',    label: 'Multi-Photo'  },
            { key: 'panorama', label: 'Panorama'     }
          ]"
          :key="m.key"
          @click="setMode(m.key)"
          class="flex-1 py-2 px-2 text-sm font-medium rounded-md transition-colors"
          :class="captureMode === m.key ? 'bg-primary-500 text-white' : 'text-gray-400 hover:text-white'"
        >{{ m.label }}</button>
      </div>

      <!-- Mode description -->
      <p class="text-gray-400 text-center mb-4 text-sm">
        <template v-if="captureMode === 'single'">Take or upload a photo of the wall or use a blank color background</template>
        <template v-else-if="captureMode === 'multi'">Capture multiple photos and combine them into a wider image — great for large walls</template>
        <template v-else>Pan your camera slowly left → right to stitch a panoramic shot of your wall</template>
      </p>

      <!-- Camera view wrapper (panorama overlay is positioned relative to this) -->
      <div class="relative">
        <CameraCapture ref="cameraCaptureRef" :default-zoom="0.5" @capture="onCapture" @error="onCameraError" />

        <!-- Panorama overlays -->
        <template v-if="captureMode === 'panorama'">
          <!-- Guide line that advances as the user pans -->
          <div class="absolute inset-0 pointer-events-none">
            <div
              class="absolute top-0 bottom-0 w-0.5 bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.7)]"
              :style="{ left: panoramaProgress + '%', transition: 'left 100ms linear' }"
            ></div>
          </div>

          <!-- Recording badge -->
          <div v-if="isPanoramaRecording" class="absolute top-3 left-0 right-0 flex justify-center pointer-events-none">
            <div class="flex items-center gap-2 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full">
              <span class="w-2 h-2 bg-red-500 rounded-full animate-pulse flex-shrink-0"></span>
              <span class="text-white text-sm font-medium">{{ panoramaFrames.length }} frames captured</span>
            </div>
          </div>

          <!-- Pan direction hint (shown when idle) -->
          <div v-else class="absolute bottom-20 left-0 right-0 flex justify-center pointer-events-none">
            <div class="flex items-center gap-2 bg-black/50 backdrop-blur-sm px-4 py-2 rounded-full text-yellow-300 text-sm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
              Pan slowly left to right
            </div>
          </div>
        </template>

        <!-- Stitching progress overlay -->
        <div v-if="stitching" class="absolute inset-0 flex flex-col items-center justify-center bg-black/75">
          <div class="spinner mb-3"></div>
          <p class="text-white text-sm">Combining images…</p>
        </div>
      </div>

      <!-- ── Panorama controls ─────────────────────────────────── -->
      <div v-if="captureMode === 'panorama'" class="mt-4 space-y-3">
        <div class="flex gap-2">
          <button
            v-if="!isPanoramaRecording"
            @click="startPanorama"
            class="btn btn-primary flex-1 flex items-center justify-center gap-2"
          >
            <span class="w-3 h-3 rounded-full bg-white inline-block"></span>
            Start Recording
          </button>
          <button
            v-else
            @click="stopPanorama"
            class="btn flex-1 flex items-center justify-center gap-2"
            style="background-color:#dc2626"
          >
            <span class="w-3 h-3 rounded bg-white inline-block"></span>
            Stop ({{ panoramaFrames.length }} frames)
          </button>
          <button
            v-if="panoramaFrames.length > 0 && !isPanoramaRecording"
            @click="panoramaFrames = []; panoramaProgress = 0"
            class="btn btn-secondary px-4"
          >Clear</button>
        </div>

        <!-- Panorama filmstrip -->
        <div v-if="panoramaFrames.length > 0" class="space-y-2">
          <p class="text-xs text-gray-400">Tap a frame to remove it</p>
          <div class="flex gap-1.5 overflow-x-auto pb-1">
            <div
              v-for="(frame, i) in panoramaFrames"
              :key="i"
              class="relative flex-shrink-0 cursor-pointer group"
              @click="panoramaFrames.splice(i, 1)"
              title="Click to remove"
            >
              <img :src="frame.dataUrl" class="h-14 w-auto rounded object-cover border border-gray-600 group-hover:border-red-500 group-hover:opacity-60 transition-all" />
              <span class="absolute bottom-0 left-0 bg-black/60 text-white text-xs px-1 rounded-bl leading-tight">{{ i + 1 }}</span>
            </div>
          </div>
        </div>

        <button
          v-if="panoramaFrames.length >= 2 && !isPanoramaRecording"
          @click="proceedWithStitching(panoramaFrames, true)"
          :disabled="stitching"
          class="btn btn-primary w-full"
        >
          {{ stitching ? 'Combining…' : `Stitch Panorama (${panoramaFrames.length} frames) →` }}
        </button>
        <p v-else-if="!isPanoramaRecording && panoramaFrames.length < 2" class="text-xs text-center text-gray-500">
          Capture at least 2 frames to stitch
        </p>
      </div>

      <!-- ── Multi-photo controls ──────────────────────────────── -->
      <div v-if="captureMode === 'multi'" class="mt-4 space-y-3">
        <!-- Hidden multi-file input -->
        <input
          ref="multiFileInputRef"
          type="file"
          accept="image/*"
          multiple
          class="hidden"
          @change="handleMultiFileUpload"
        />

        <button
          @click="multiFileInputRef?.click()"
          :disabled="capturedImages.length >= MAX_MULTI"
          class="btn btn-secondary w-full flex items-center justify-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Upload Multiple from Camera Roll
        </button>

        <!-- Captured photos grid -->
        <div v-if="capturedImages.length > 0" class="space-y-2">
          <div class="flex items-center justify-between">
            <p class="text-xs text-gray-400">{{ capturedImages.length }} photo{{ capturedImages.length !== 1 ? 's' : '' }} · left to right order</p>
            <button @click="capturedImages = []" class="text-xs text-gray-500 hover:text-red-400 transition-colors">Clear all</button>
          </div>
          <div class="flex gap-2 flex-wrap">
            <div
              v-for="(img, i) in capturedImages"
              :key="i"
              class="relative group"
            >
              <img :src="img.dataUrl" class="h-20 w-auto rounded object-cover border border-gray-600" />
              <!-- Remove button -->
              <button
                @click="capturedImages.splice(i, 1)"
                class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity leading-none text-sm font-bold"
              >×</button>
              <!-- Position number -->
              <span class="absolute bottom-0 left-0 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded-bl font-medium">{{ i + 1 }}</span>
              <!-- Reorder arrows (hover) -->
              <div class="absolute bottom-0 right-0 flex gap-0.5 p-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  v-if="i > 0"
                  @click.stop="moveImage(i, -1)"
                  class="bg-black/70 hover:bg-black text-white text-xs px-1.5 py-0.5 rounded"
                >←</button>
                <button
                  v-if="i < capturedImages.length - 1"
                  @click.stop="moveImage(i, 1)"
                  class="bg-black/70 hover:bg-black text-white text-xs px-1.5 py-0.5 rounded"
                >→</button>
              </div>
            </div>
          </div>
        </div>

        <button
          v-if="capturedImages.length >= 1"
          @click="proceedWithStitching(capturedImages, false)"
          :disabled="stitching"
          class="btn btn-primary w-full"
        >
          {{ stitching ? 'Combining…' : capturedImages.length === 1 ? 'Continue →' : `Combine ${capturedImages.length} Photos & Continue →` }}
        </button>
        <p v-else class="text-xs text-center text-gray-500">
          Tap the shutter or upload photos — each one is added to the row above
        </p>
      </div>

      <!-- QR helper (all modes) -->
      <div class="mt-6">
        <QrCodeCard />
      </div>

      <!-- Blank color option -->
      <div class="mt-6 text-center">
        <div class="flex items-center gap-4 mb-4">
          <div class="flex-1 h-px bg-gray-600"></div>
          <span class="text-gray-400 text-sm">or</span>
          <div class="flex-1 h-px bg-gray-600"></div>
        </div>
        <button @click="selectBlankColor" class="btn btn-secondary w-full">
          Use Blank Color Background
        </button>
      </div>
    </div>

    <!-- ─── Step 2: Crop & Size ────────────────────────────────── -->
    <div v-if="step === 2" class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-4 text-center">{{ useBlankColor ? 'Color & Size' : 'Crop & Size' }}</h2>
      <p class="text-gray-400 text-center mb-6">
        {{ useBlankColor ? 'Choose wall color and enter dimensions' : 'Crop your wall photo and enter dimensions' }}
      </p>

      <!-- Photo cropping -->
      <div v-if="!useBlankColor && capturedImage" class="card mb-4">
        <ImageCropper
          :imageUrl="capturedImage.dataUrl"
          :aspectRatio="cropAspectRatio"
          @crop="onCrop"
        />
        <div class="flex items-center gap-2 mt-3 p-3 bg-dark-300 rounded-lg">
          <input
            type="checkbox"
            id="lockRatio"
            v-model="lockAspectRatio"
            class="w-4 h-4 rounded border-gray-600 bg-dark-100 text-primary-500 focus:ring-primary-500 cursor-pointer"
          />
          <label for="lockRatio" class="text-sm text-gray-300 cursor-pointer select-none">
            Lock aspect ratio
            <span v-if="activeLockRatio" class="text-gray-500">({{ activeLockRatio.toFixed(2) }})</span>
          </label>
        </div>
      </div>

      <!-- Color selection -->
      <div v-if="useBlankColor" class="card mb-4">
        <h3 class="font-semibold mb-3">Wall Color</h3>
        <div
          class="w-full h-32 rounded-lg border border-gray-600 mb-3"
          :style="{ backgroundColor: wallColor }"
        ></div>
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="preset in wallColorPresets"
            :key="preset.value"
            @click="wallColor = preset.value; showCustomWallColor = false"
            class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
            :class="wallColor === preset.value && !showCustomWallColor ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
          >
            <span class="w-5 h-5 rounded-full border border-gray-500" :style="{ backgroundColor: preset.value }"></span>
            <span class="text-sm">{{ preset.label }}</span>
          </button>
          <button
            @click="showCustomWallColor = !showCustomWallColor"
            class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition"
            :class="showCustomWallColor ? 'border-primary-500' : 'border-gray-600 hover:border-gray-500'"
          >
            <span class="w-5 h-5 rounded-full border border-gray-500" :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }"></span>
            <span class="text-sm">Custom</span>
          </button>
        </div>
        <div v-if="showCustomWallColor" class="mt-2">
          <input type="color" v-model="wallColor" class="w-full h-10 rounded cursor-pointer bg-transparent border border-gray-600" />
        </div>
      </div>

      <!-- Wall Dimensions -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold">Wall Dimensions (optional)</h3>
          <div class="flex gap-2">
            <button @click="selectFtIn" class="px-3 py-1 text-sm rounded-full transition" :class="wallUnit === 'ft' ? 'bg-primary-500 text-white' : 'bg-dark-300 hover:bg-dark-100'">ft & in</button>
            <button @click="selectCm" class="px-3 py-1 text-sm rounded-full transition" :class="wallUnit === 'cm' ? 'bg-primary-500 text-white' : 'bg-dark-300 hover:bg-dark-100'">cm</button>
          </div>
        </div>

        <!-- ft & in inputs -->
        <div v-if="wallUnit === 'ft'" class="space-y-3">
          <div>
            <label class="block text-xs text-gray-400 mb-1">Width</label>
            <div class="flex gap-2">
              <div class="flex-1"><input v-model="displayWidthFt" type="number" min="0" placeholder="ft" class="w-full" /></div>
              <div class="flex-1"><input v-model="displayWidthIn" type="number" min="0" max="11" placeholder="in" class="w-full" /></div>
            </div>
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Height</label>
            <div class="flex gap-2">
              <div class="flex-1"><input v-model="displayHeightFt" type="number" min="0" placeholder="ft" class="w-full" /></div>
              <div class="flex-1"><input v-model="displayHeightIn" type="number" min="0" max="11" placeholder="in" class="w-full" /></div>
            </div>
          </div>
        </div>

        <!-- cm inputs -->
        <div v-else class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1">Width (cm)</label>
            <input v-model="displayWidthCm" type="number" min="0" placeholder="e.g., 300" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Height (cm)</label>
            <input v-model="displayHeightCm" type="number" min="0" placeholder="e.g., 250" />
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">Providing wall dimensions helps with accurate frame placement</p>
      </div>

      <!-- Cropped Result Preview -->
      <div v-if="!useBlankColor && croppedImage?.dataUrl" class="card mb-4">
        <h3 class="font-semibold mb-2">Cropped Result</h3>
        <img :src="croppedImage.dataUrl" alt="Cropped preview" class="w-full rounded-lg" />
        <div class="mt-2 text-xs text-gray-500 text-center">{{ croppedImage.width }} x {{ croppedImage.height }} pixels</div>
      </div>

      <div class="flex gap-4">
        <button @click="retake" class="btn btn-secondary flex-1">
          {{ useBlankColor ? 'Go Back' : 'Retake Photo' }}
        </button>
        <button @click="confirmCrop" class="btn btn-primary flex-1">Continue</button>
      </div>
    </div>

    <!-- ─── Step 3: Save to Gallery ───────────────────────────── -->
    <div v-if="step === 3" class="card">
      <h2 class="text-2xl font-bold mb-4 text-center">Save to Gallery</h2>
      <p class="text-gray-400 text-center mb-6">Give your wall a name and save it</p>

      <!-- Preview -->
      <div v-if="!useBlankColor && croppedImage" class="mb-6">
        <img :src="croppedImage.dataUrl" alt="Cropped wall" class="w-full max-h-64 object-contain rounded-lg bg-dark-300" />
      </div>
      <div v-else class="mb-6">
        <div class="w-full h-40 rounded-lg border border-gray-600" :style="{ backgroundColor: wallColor }"></div>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Wall Name *</label>
          <input v-model="wallName" type="text" placeholder="e.g., Living Room, Bedroom, Office" />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">Description (optional)</label>
          <textarea v-model="wallDescription" rows="2" placeholder="Any notes about this wall…" class="w-full px-4 py-2 bg-dark-300 border border-gray-600 rounded-lg text-white resize-none"></textarea>
        </div>
      </div>

      <div class="flex gap-4 mt-6">
        <button @click="step = 2" class="btn btn-secondary flex-1">
          {{ useBlankColor ? 'Edit Color & Size' : 'Edit Crop & Size' }}
        </button>
        <button @click="saveWall" :disabled="loading" class="btn btn-primary flex-1">
          <span v-if="loading">Saving…</span>
          <span v-else>Save Wall</span>
        </button>
      </div>
    </div>
  </div>
</template>

