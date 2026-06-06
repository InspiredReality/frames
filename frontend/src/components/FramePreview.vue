<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const emit = defineEmits(['update:totalDimensions'])

const props = defineProps({
  imageUrl: String,
  dimensions: {
    type: Object,
    default: () => ({ width: 10, height: 8, depth: 1 })
  },
  frameColor: {
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

// --- Touch scroll state (single-finger scrolls page; two-finger handled by OrbitControls) ---
let touchScrolling = false
let touchScrollLastY = 0
let touchScrollVelocity = 0
let touchScrollAnimId = null
const activeTouchPointers = new Set()
let singleTouchPointerId = null

const applyScrollMomentum = () => {
  if (Math.abs(touchScrollVelocity) < 0.5) { touchScrollAnimId = null; return }
  window.scrollBy(0, -touchScrollVelocity)
  touchScrollVelocity *= 0.88
  touchScrollAnimId = requestAnimationFrame(applyScrollMomentum)
}

const onTouchPointerDown = (event) => {
  if (event.pointerType !== 'touch') return
  activeTouchPointers.add(event.pointerId)

  if (activeTouchPointers.size > 1) {
    touchScrolling = false
    touchScrollVelocity = 0
    if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }
    singleTouchPointerId = null
    return
  }

  singleTouchPointerId = event.pointerId
  if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }
  touchScrolling = true
  touchScrollLastY = event.clientY
  touchScrollVelocity = 0
}

const onTouchPointerMove = (event) => {
  if (event.pointerType !== 'touch' || event.pointerId !== singleTouchPointerId || !touchScrolling) return
  const dy = event.clientY - touchScrollLastY
  touchScrollVelocity = dy
  window.scrollBy(0, -dy)
  touchScrollLastY = event.clientY
}

const onTouchPointerUp = (event) => {
  if (event.pointerType !== 'touch') return
  activeTouchPointers.delete(event.pointerId)

  if (event.pointerId !== singleTouchPointerId) {
    if (activeTouchPointers.size === 0) singleTouchPointerId = null
    return
  }

  singleTouchPointerId = null
  if (touchScrolling) {
    touchScrolling = false
    touchScrollAnimId = requestAnimationFrame(applyScrollMomentum)
  }
}

const onTouchPointerCancel = (event) => {
  if (event.pointerType !== 'touch') return
  activeTouchPointers.delete(event.pointerId)
  if (activeTouchPointers.size === 0) {
    touchScrolling = false
    touchScrollVelocity = 0
    if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }
    singleTouchPointerId = null
  }
}

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
  // Single-finger scrolls the page; two-finger pinch/pan stays with OrbitControls
  controls.touches = { ONE: -1, TWO: THREE.TOUCH.DOLLY_PAN }

  // Intercept touch events in capture phase (before OrbitControls) to implement page scroll
  containerRef.value.addEventListener('pointerdown', onTouchPointerDown, { passive: false, capture: true })
  containerRef.value.addEventListener('pointermove', onTouchPointerMove, { passive: false, capture: true })
  containerRef.value.addEventListener('pointerup', onTouchPointerUp, { capture: true })
  containerRef.value.addEventListener('pointercancel', onTouchPointerCancel, { capture: true })

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

  if (borderWidth > 0 && props.frameColor) {
    const frameMaterial = new THREE.MeshStandardMaterial({ color: new THREE.Color(props.frameColor) })

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
  }

  // Back panel
  const backGeom = new THREE.PlaneGeometry(totalWidth, totalHeight)
  const backMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.BackSide })
  const backPanel = new THREE.Mesh(backGeom, backMaterial)
  backPanel.position.z = -depth / 2
  frameGroup.add(backPanel)

  scene.add(frameGroup)

  emit('update:totalDimensions', { width: totalWidth, height: totalHeight })

  // Adjust camera to fit - base on picture size so the image doesn't
  // appear to shrink when frame thickness increases
  const maxPicDim = Math.max(width, height)
  camera.position.z = maxPicDim * 2.5
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

// Watch a serialized snapshot of all props that affect the frame.
// This avoids infinite loops caused by parent re-renders passing new
// object references for dimensions (which would re-trigger deep watchers).
let pendingUpdate = false
watch(
  () => JSON.stringify([
    props.dimensions.width,
    props.dimensions.height,
    props.dimensions.depth,
    props.imageUrl,
    props.frameColor,
    props.frameThickness
  ]),
  () => {
    if (pendingUpdate) return
    pendingUpdate = true
    nextTick(() => {
      pendingUpdate = false
      if (scene) createFrame()
    })
  }
)

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)

  if (containerRef.value) {
    containerRef.value.removeEventListener('pointerdown', onTouchPointerDown, { capture: true })
    containerRef.value.removeEventListener('pointermove', onTouchPointerMove, { capture: true })
    containerRef.value.removeEventListener('pointerup', onTouchPointerUp, { capture: true })
    containerRef.value.removeEventListener('pointercancel', onTouchPointerCancel, { capture: true })
  }
  if (touchScrollAnimId) cancelAnimationFrame(touchScrollAnimId)

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
