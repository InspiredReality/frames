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
    default: '#000000'
  },
  frameThickness: {
    type: Number,
    default: 1
  }
})

const containerRef = ref(null)
let scene, camera, renderer, controls, frameGroup, animationId
const textureLoader = new THREE.TextureLoader()

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(0, 0, 30)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(10, 10, 10)
  scene.add(directionalLight)

  createFrame()
  animate()
}

const createFrame = () => {
  if (frameGroup) {
    scene.remove(frameGroup)
    frameGroup.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) {
        if (child.material.map) child.material.map.dispose()
        child.material.dispose()
      }
    })
  }

  const { width, height, depth } = props.dimensions
  const borderWidth = props.frameThickness

  frameGroup = new THREE.Group()

  const frameColor = new THREE.Color(props.frameColor)
  const frameMaterial = new THREE.MeshStandardMaterial({ color: frameColor })

  // Picture plane (image in center)
  const pictureGeometry = new THREE.PlaneGeometry(width, height)

  let pictureMaterial
  if (props.imageUrl) {
    const texture = textureLoader.load(props.imageUrl)
    texture.colorSpace = THREE.SRGBColorSpace
    pictureMaterial = new THREE.MeshStandardMaterial({
      map: texture,
      side: THREE.FrontSide
    })
  } else {
    pictureMaterial = new THREE.MeshStandardMaterial({
      color: 0xcccccc,
      side: THREE.FrontSide
    })
  }

  const pictureMesh = new THREE.Mesh(pictureGeometry, pictureMaterial)
  pictureMesh.position.z = depth / 2 + 0.01
  frameGroup.add(pictureMesh)

  // Total frame dimensions (picture + border on each side)
  const totalWidth = width + borderWidth * 2
  const totalHeight = height + borderWidth * 2

  // Top border
  const topGeom = new THREE.BoxGeometry(totalWidth, borderWidth, depth)
  const topBorder = new THREE.Mesh(topGeom, frameMaterial)
  topBorder.position.set(0, (height + borderWidth) / 2, 0)
  frameGroup.add(topBorder)

  // Bottom border
  const bottomBorder = new THREE.Mesh(topGeom.clone(), frameMaterial)
  bottomBorder.position.set(0, -(height + borderWidth) / 2, 0)
  frameGroup.add(bottomBorder)

  // Left border
  const sideGeom = new THREE.BoxGeometry(borderWidth, height, depth)
  const leftBorder = new THREE.Mesh(sideGeom, frameMaterial)
  leftBorder.position.set(-(width + borderWidth) / 2, 0, 0)
  frameGroup.add(leftBorder)

  // Right border
  const rightBorder = new THREE.Mesh(sideGeom.clone(), frameMaterial)
  rightBorder.position.set((width + borderWidth) / 2, 0, 0)
  frameGroup.add(rightBorder)

  // Back panel
  const backGeom = new THREE.PlaneGeometry(totalWidth, totalHeight)
  const backMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.BackSide })
  const backPanel = new THREE.Mesh(backGeom, backMaterial)
  backPanel.position.z = -depth / 2
  frameGroup.add(backPanel)

  scene.add(frameGroup)

  // Adjust camera to fit
  const maxDim = Math.max(totalWidth, totalHeight)
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
watch(() => props.frameThickness, createFrame)

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)

  if (frameGroup) {
    frameGroup.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) {
        if (child.material.map) child.material.map.dispose()
        child.material.dispose()
      }
    })
  }

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
