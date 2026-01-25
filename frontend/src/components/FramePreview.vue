<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps({
  imageUrl: String,
  dimensions: {
    type: Object,
    default: () => ({ width: 10, height: 8, depth: 1 })
  },
  frameColor: {
    type: String,
    default: '#8B4513'
  }
})

const containerRef = ref(null)
let scene, camera, renderer, controls, frameMesh, animationId

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // Camera
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(0, 0, 30)

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // Controls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(10, 10, 10)
  scene.add(directionalLight)

  createFrame()
  animate()
}

const createFrame = () => {
  if (frameMesh) {
    scene.remove(frameMesh)
    frameMesh.geometry.dispose()
    if (frameMesh.material.map) frameMesh.material.map.dispose()
    frameMesh.material.dispose()
  }

  const { width, height, depth } = props.dimensions

  // Create frame geometry (simple box for now)
  const geometry = new THREE.BoxGeometry(width, height, depth)

  // Create material
  let material
  if (props.imageUrl) {
    const textureLoader = new THREE.TextureLoader()
    const texture = textureLoader.load(props.imageUrl)
    material = new THREE.MeshStandardMaterial({
      map: texture,
      color: 0xffffff
    })
  } else {
    material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(props.frameColor)
    })
  }

  frameMesh = new THREE.Mesh(geometry, material)
  scene.add(frameMesh)

  // Adjust camera to fit frame
  const maxDim = Math.max(width, height)
  camera.position.z = maxDim * 2
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

const handleResize = () => {
  if (!containerRef.value || !camera || !renderer) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

watch(() => props.dimensions, createFrame, { deep: true })
watch(() => props.imageUrl, createFrame)
watch(() => props.frameColor, createFrame)

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)

  if (renderer) {
    renderer.dispose()
    containerRef.value?.removeChild(renderer.domElement)
  }
  if (controls) controls.dispose()
})
</script>

<template>
  <div ref="containerRef" class="viewer-container w-full h-64 rounded-lg overflow-hidden"></div>
</template>
