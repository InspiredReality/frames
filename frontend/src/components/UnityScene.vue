<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  buildPath: {
    type: String,
    default: '/unity'
  },
  buildName: {
    type: String,
    default: 'Build'
  },
  sceneData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['loaded', 'error', 'message'])

const containerRef = ref(null)
const canvasRef = ref(null)
const loading = ref(true)
const loadingProgress = ref(0)
const error = ref(null)

let unityInstance = null

const initUnity = async () => {
  if (!window.createUnityInstance) {
    // Load Unity loader script
    const script = document.createElement('script')
    script.src = `${props.buildPath}/${props.buildName}.loader.js`
    script.onload = () => loadUnity()
    script.onerror = () => {
      error.value = 'Failed to load Unity loader'
      loading.value = false
      emit('error', error.value)
    }
    document.body.appendChild(script)
  } else {
    loadUnity()
  }
}

const loadUnity = async () => {
  if (!canvasRef.value) return

  const config = {
    dataUrl: `${props.buildPath}/${props.buildName}.data`,
    frameworkUrl: `${props.buildPath}/${props.buildName}.framework.js`,
    codeUrl: `${props.buildPath}/${props.buildName}.wasm`,
    streamingAssetsUrl: `${props.buildPath}/StreamingAssets`,
    companyName: 'Frames',
    productName: 'Frames AR',
    productVersion: '1.0.0'
  }

  try {
    unityInstance = await window.createUnityInstance(canvasRef.value, config, (progress) => {
      loadingProgress.value = Math.round(progress * 100)
    })

    loading.value = false
    emit('loaded', unityInstance)

    // Send initial data to Unity
    if (props.sceneData && Object.keys(props.sceneData).length > 0) {
      sendToUnity('ReceiveSceneData', JSON.stringify(props.sceneData))
    }
  } catch (err) {
    error.value = err.message || 'Failed to initialize Unity'
    loading.value = false
    emit('error', error.value)
  }
}

const sendToUnity = (methodName, data) => {
  if (unityInstance) {
    unityInstance.SendMessage('GameManager', methodName, data)
  }
}

// Function to receive messages from Unity (exposed globally)
const setupUnityCallbacks = () => {
  window.unityToVue = (message) => {
    try {
      const data = JSON.parse(message)
      emit('message', data)
    } catch {
      emit('message', { raw: message })
    }
  }
}

onMounted(() => {
  setupUnityCallbacks()
  // Only try to load Unity if the build exists
  // For now, show a placeholder message
  if (import.meta.env.PROD) {
    initUnity()
  } else {
    loading.value = false
    error.value = 'Unity WebGL build not available in development. Place your build in /public/unity/'
  }
})

onUnmounted(() => {
  if (unityInstance) {
    unityInstance.Quit()
  }
  delete window.unityToVue
})

defineExpose({ sendToUnity })
</script>

<template>
  <div ref="containerRef" class="unity-container relative bg-black">
    <canvas ref="canvasRef" class="w-full h-full"></canvas>

    <!-- Loading overlay -->
    <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-dark-100">
      <div class="spinner mb-4"></div>
      <p class="text-gray-300">Loading Unity Scene... {{ loadingProgress }}%</p>
      <div class="w-48 h-2 bg-dark-300 rounded-full mt-2 overflow-hidden">
        <div
          class="h-full bg-primary-500 transition-all duration-300"
          :style="{ width: `${loadingProgress}%` }"
        ></div>
      </div>
    </div>

    <!-- Error overlay -->
    <div v-if="error" class="absolute inset-0 flex flex-col items-center justify-center bg-dark-100 p-4">
      <svg class="w-12 h-12 text-yellow-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <p class="text-gray-300 text-center">{{ error }}</p>
      <p class="text-gray-500 text-sm mt-2 text-center">
        To use AR features, build your Unity WebXR project and place it in the /public/unity/ folder.
      </p>
    </div>
  </div>
</template>
