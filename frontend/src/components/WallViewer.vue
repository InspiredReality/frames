<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps({
  wallImageUrl: String,
  framePlacements: {
    type: Array,
    default: () => []
  },
  frames: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['frameSelected', 'frameMoved'])

const containerRef = ref(null)
let scene, camera, renderer, controls, wallMesh, animationId
const frameObjects = new Map()

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // Camera
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
  camera.position.set(0, 0, 5)

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // Controls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.maxPolarAngle = Math.PI / 2

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5)
  directionalLight.position.set(5, 10, 7)
  scene.add(directionalLight)

  createWall()
  updateFrames()
  animate()
}

const createWall = () => {
  if (wallMesh) {
    scene.remove(wallMesh)
    wallMesh.geometry.dispose()
    if (wallMesh.material.map) wallMesh.material.map.dispose()
    wallMesh.material.dispose()
  }

  // Create wall plane
  const geometry = new THREE.PlaneGeometry(8, 6)

  let material
  if (props.wallImageUrl) {
    const textureLoader = new THREE.TextureLoader()
    const texture = textureLoader.load(props.wallImageUrl)
    texture.colorSpace = THREE.SRGBColorSpace
    material = new THREE.MeshStandardMaterial({
      map: texture,
      side: THREE.DoubleSide
    })
  } else {
    material = new THREE.MeshStandardMaterial({
      color: 0xe0e0e0,
      side: THREE.DoubleSide
    })
  }

  wallMesh = new THREE.Mesh(geometry, material)
  wallMesh.position.z = -0.1
  scene.add(wallMesh)
}

const updateFrames = () => {
  // Clear existing frame objects
  frameObjects.forEach((obj) => {
    scene.remove(obj)
    obj.geometry.dispose()
    obj.material.dispose()
  })
  frameObjects.clear()

  // Add frames based on placements
  props.framePlacements.forEach((placement, index) => {
    const frame = props.frames.find(f => f.id === placement.frame_id)
    if (!frame) return

    const dims = frame.dimensions?.cm || { width: 20, height: 25, depth: 2 }
    const scale = 0.01 // Convert cm to scene units

    const geometry = new THREE.BoxGeometry(
      dims.width * scale,
      dims.height * scale,
      dims.depth * scale
    )

    const material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(frame.styling?.frame_color || '#8B4513')
    })

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(
      placement.position?.x || 0,
      placement.position?.y || 0,
      placement.position?.z || 0.05
    )
    mesh.userData = { frameId: frame.id, placementIndex: index }

    scene.add(mesh)
    frameObjects.set(index, mesh)
  })
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

watch(() => props.wallImageUrl, createWall)
watch(() => props.framePlacements, updateFrames, { deep: true })
watch(() => props.frames, updateFrames, { deep: true })

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)

  frameObjects.forEach((obj) => {
    obj.geometry.dispose()
    obj.material.dispose()
  })

  if (renderer) {
    renderer.dispose()
    containerRef.value?.removeChild(renderer.domElement)
  }
  if (controls) controls.dispose()
})
</script>

<template>
  <div ref="containerRef" class="viewer-container w-full h-96 rounded-lg overflow-hidden"></div>
</template>
