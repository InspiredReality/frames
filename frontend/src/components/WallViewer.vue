<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { getUploadUrl } from '@/services/api'

const props = defineProps({
  wallImageUrl: String,
  wallBackgroundColor: {
    type: String,
    default: null
  },
  wallWidthCm: {
    type: Number,
    default: 0
  },
  wallHeightCm: {
    type: Number,
    default: 0
  },
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
let scene, camera, renderer, controls, wallMesh, animationId, raycaster, mouse
let dragPlane, dragOffset, draggedFrame, isDragging
const frameObjects = new Map()
const textureLoader = new THREE.TextureLoader()
textureLoader.crossOrigin = 'anonymous'

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // Camera – position will be set in createWall() to fit the wall
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
  camera.position.set(0, 0, 5)

  // Raycaster for click detection
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // Add mouse listeners for frame dragging (left-click) and selection
  renderer.domElement.addEventListener('mousedown', onMouseDown)
  renderer.domElement.addEventListener('mousemove', onMouseMove)
  renderer.domElement.addEventListener('mouseup', onMouseUp)

  // Three.js r152+ OrbitControls uses pointer events (pointerdown → setPointerCapture),
  // not touch events. setPointerCapture redirects all input to the canvas and kills native
  // scroll. We intercept in capture phase on the container so our handlers fire BEFORE
  // OrbitControls. We stopPropagation() to prevent OrbitControls from seeing the event at
  // all; only call preventDefault() when the finger lands on a frame.
  containerRef.value.addEventListener('pointerdown', onTouchPointerDown, { passive: false, capture: true })
  containerRef.value.addEventListener('pointermove', onTouchPointerMove, { passive: false, capture: true })
  containerRef.value.addEventListener('pointerup', onTouchPointerUp, { capture: true })
  containerRef.value.addEventListener('pointercancel', onTouchPointerCancel, { capture: true })

  // Drag state
  dragPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0)
  dragOffset = new THREE.Vector3()
  draggedFrame = null
  isDragging = false

  // Controls - only orbit with right-click, scroll to zoom
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.maxPolarAngle = Math.PI / 2
  controls.mouseButtons = {
    LEFT: null,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.ROTATE
  }
  // Disable single-finger rotation on mobile; keep two-finger pinch zoom + pan
  controls.touches = {
    ONE: -1,
    TWO: THREE.TOUCH.DOLLY_PAN
  }
  // OrbitControls sets touch-action:none on the canvas, which is correct here.
  // We implement manual page scroll below for non-frame touches.

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

let mouseDownPos = { x: 0, y: 0 }

const getMouseNDC = (event) => {
  const rect = renderer.domElement.getBoundingClientRect()
  return {
    x: ((event.clientX - rect.left) / rect.width) * 2 - 1,
    y: -((event.clientY - rect.top) / rect.height) * 2 + 1
  }
}

const findFrameGroup = (object) => {
  let obj = object
  while (obj && !obj.userData.frameId) {
    obj = obj.parent
  }
  return obj?.userData.frameId ? obj : null
}

const onMouseDown = (event) => {
  if (event.button !== 0 || !containerRef.value) return // Left click only

  const ndc = getMouseNDC(event)
  mouseDownPos = { x: event.clientX, y: event.clientY }
  mouse.set(ndc.x, ndc.y)
  raycaster.setFromCamera(mouse, camera)

  const frameArray = Array.from(frameObjects.values())
  const intersects = raycaster.intersectObjects(frameArray, true)

  if (intersects.length > 0) {
    const frameGroup = findFrameGroup(intersects[0].object)
    if (frameGroup) {
      draggedFrame = frameGroup
      isDragging = false

      // Calculate offset between frame position and intersection point on drag plane
      const intersectPoint = new THREE.Vector3()
      raycaster.ray.intersectPlane(dragPlane, intersectPoint)
      dragOffset.copy(frameGroup.position).sub(intersectPoint)

      // Disable orbit controls while dragging
      controls.enabled = false
    }
  }
}

const onMouseMove = (event) => {
  if (!draggedFrame || !containerRef.value) return

  // Check if actually dragging (moved more than 3px)
  const dx = event.clientX - mouseDownPos.x
  const dy = event.clientY - mouseDownPos.y
  if (!isDragging && Math.sqrt(dx * dx + dy * dy) < 3) return
  isDragging = true

  const ndc = getMouseNDC(event)
  mouse.set(ndc.x, ndc.y)
  raycaster.setFromCamera(mouse, camera)

  const intersectPoint = new THREE.Vector3()
  if (raycaster.ray.intersectPlane(dragPlane, intersectPoint)) {
    draggedFrame.position.x = intersectPoint.x + dragOffset.x
    draggedFrame.position.y = intersectPoint.y + dragOffset.y
  }
}

const onMouseUp = (event) => {
  if (event.button !== 0) return

  controls.enabled = true

  if (draggedFrame) {
    if (isDragging) {
      // Emit the new position (only x/y, z is always computed from frame depth)
      emit('frameMoved', {
        placementIndex: draggedFrame.userData.placementIndex,
        position: {
          x: parseFloat(draggedFrame.position.x.toFixed(4)),
          y: parseFloat(draggedFrame.position.y.toFixed(4))
        }
      })
    } else {
      // Was a click, not a drag - select the frame
      emit('frameSelected', {
        frameId: draggedFrame.userData.frameId,
        placementIndex: draggedFrame.userData.placementIndex
      })
    }
    draggedFrame = null
    isDragging = false
  }
}

// --- Touch handling via pointer events ---
// OrbitControls uses pointerdown → setPointerCapture internally, so we must intercept at
// the container in capture phase. Mouse pointer events are let through (pointerType !== 'touch')
// so OrbitControls right-click rotate and scroll-zoom still work on desktop.
//
// touch-action:none (set by OrbitControls) is kept — we implement page scroll manually with
// window.scrollBy() + inertia. Two-finger events are NOT stopped; OrbitControls sees both
// pointers and handles pinch zoom normally.

let touchScrolling = false
let touchScrollLastY = 0
let touchScrollVelocity = 0
let touchScrollAnimId = null
const activeTouchPointers = new Set() // tracks all active touch pointerIds
let singleTouchPointerId = null       // pointerId we treat as the single-finger

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
    // Second finger arrived — hand off to OrbitControls for pinch zoom.
    // Cancel any in-progress single-finger operation.
    touchScrolling = false
    touchScrollVelocity = 0
    if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }
    if (draggedFrame) { draggedFrame = null; isDragging = false; }
    controls.enabled = true
    singleTouchPointerId = null
    // Do NOT stopPropagation — OrbitControls must see this (and the earlier first finger) to
    // initiate its two-finger DOLLY_PAN state.
    return
  }

  // Single finger — our handler owns this gesture
  singleTouchPointerId = event.pointerId
  if (!containerRef.value) return

  if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }

  const ndc = getMouseNDC(event)
  mouseDownPos = { x: event.clientX, y: event.clientY }
  mouse.set(ndc.x, ndc.y)
  raycaster.setFromCamera(mouse, camera)

  const frameArray = Array.from(frameObjects.values())
  const intersects = raycaster.intersectObjects(frameArray, true)

  if (intersects.length > 0) {
    const frameGroup = findFrameGroup(intersects[0].object)
    if (frameGroup) {
      draggedFrame = frameGroup
      isDragging = false
      touchScrolling = false

      const intersectPoint = new THREE.Vector3()
      raycaster.ray.intersectPlane(dragPlane, intersectPoint)
      dragOffset.copy(frameGroup.position).sub(intersectPoint)

      controls.enabled = false
      return
    }
  }

  // Finger is on the canvas background — manual page scroll
  touchScrolling = true
  touchScrollLastY = event.clientY
  touchScrollVelocity = 0
}

const onTouchPointerMove = (event) => {
  if (event.pointerType !== 'touch') return
  // Ignore any pointer that isn't our tracked single-finger (incl. two-finger moves)
  if (event.pointerId !== singleTouchPointerId) return

  if (touchScrolling) {
    const dy = event.clientY - touchScrollLastY
    touchScrollVelocity = dy
    window.scrollBy(0, -dy)
    touchScrollLastY = event.clientY
    return
  }

  if (!draggedFrame || !containerRef.value) return

  const dx = event.clientX - mouseDownPos.x
  const dy = event.clientY - mouseDownPos.y
  if (!isDragging && Math.sqrt(dx * dx + dy * dy) < 5) return
  isDragging = true

  const ndc = getMouseNDC(event)
  mouse.set(ndc.x, ndc.y)
  raycaster.setFromCamera(mouse, camera)

  const intersectPoint = new THREE.Vector3()
  if (raycaster.ray.intersectPlane(dragPlane, intersectPoint)) {
    draggedFrame.position.x = intersectPoint.x + dragOffset.x
    draggedFrame.position.y = intersectPoint.y + dragOffset.y
  }
}

const onTouchPointerUp = (event) => {
  if (event.pointerType !== 'touch') return

  activeTouchPointers.delete(event.pointerId)

  if (event.pointerId !== singleTouchPointerId) {
    // A non-single-touch finger lifted; re-enable controls when all fingers are gone
    if (activeTouchPointers.size === 0) { controls.enabled = true; singleTouchPointerId = null }
    return
  }

  singleTouchPointerId = null

  if (touchScrolling) {
    touchScrolling = false
    touchScrollAnimId = requestAnimationFrame(applyScrollMomentum)
    return
  }

  controls.enabled = true

  if (draggedFrame) {
    if (isDragging) {
      emit('frameMoved', {
        placementIndex: draggedFrame.userData.placementIndex,
        position: {
          x: parseFloat(draggedFrame.position.x.toFixed(4)),
          y: parseFloat(draggedFrame.position.y.toFixed(4))
        }
      })
    } else {
      emit('frameSelected', {
        frameId: draggedFrame.userData.frameId,
        placementIndex: draggedFrame.userData.placementIndex
      })
    }
    draggedFrame = null
    isDragging = false
  }
}

const onTouchPointerCancel = (event) => {
  if (event.pointerType !== 'touch') return
  activeTouchPointers.delete(event.pointerId)
  if (activeTouchPointers.size === 0) {
    touchScrolling = false
    touchScrollVelocity = 0
    if (touchScrollAnimId) { cancelAnimationFrame(touchScrollAnimId); touchScrollAnimId = null }
    controls.enabled = true
    draggedFrame = null
    isDragging = false
    singleTouchPointerId = null
  }
}

const createWall = () => {
  if (wallMesh) {
    scene.remove(wallMesh)
    wallMesh.geometry.dispose()
    if (wallMesh.material.map) wallMesh.material.map.dispose()
    wallMesh.material.dispose()
  }

  // Use wall dimensions if available (cm -> scene units at 0.01 scale), fallback to 8 ft × 8 ft
  const defaultCm = 8 * 30.48 * 0.01 // 8 feet in scene units
  const wallW = (props.wallWidthCm > 0) ? props.wallWidthCm * 0.01 : defaultCm
  const wallH = (props.wallHeightCm > 0) ? props.wallHeightCm * 0.01 : defaultCm

  // Create wall plane
  const geometry = new THREE.PlaneGeometry(wallW, wallH)

  let material
  if (props.wallImageUrl) {
    const wallTextureLoader = new THREE.TextureLoader()
    wallTextureLoader.crossOrigin = 'anonymous'
    const texture = wallTextureLoader.load(props.wallImageUrl)
    texture.colorSpace = THREE.SRGBColorSpace
    material = new THREE.MeshStandardMaterial({
      map: texture,
      side: THREE.DoubleSide
    })
  } else {
    const fallbackColor = props.wallBackgroundColor
      ? new THREE.Color(props.wallBackgroundColor)
      : new THREE.Color(0xe0e0e0)
    material = new THREE.MeshStandardMaterial({
      color: fallbackColor,
      side: THREE.DoubleSide
    })
  }

  wallMesh = new THREE.Mesh(geometry, material)
  wallMesh.position.z = -0.1
  scene.add(wallMesh)

  // Position camera so the wall fills 90% of the container height
  if (camera && containerRef.value) {
    const containerWidth = containerRef.value.clientWidth
    const containerHeight = containerRef.value.clientHeight
    const aspect = containerWidth / containerHeight
    const fovRad = THREE.MathUtils.degToRad(camera.fov)

    // Distance needed so wall height fills 90% of vertical view
    let dist = (wallH / 0.9) / (2 * Math.tan(fovRad / 2))

    // Also check horizontal: wall width should fit within 90% of horizontal view
    const hFov = 2 * Math.atan(Math.tan(fovRad / 2) * aspect)
    const distH = (wallW / 0.9) / (2 * Math.tan(hFov / 2))

    // Use the larger distance so the wall fits in both dimensions
    dist = Math.max(dist, distH)

    camera.position.set(0, 0, dist)
    camera.lookAt(0, 0, 0)

    if (controls) {
      controls.target.set(0, 0, 0)
      controls.update()
    }
  }
}

const updateFrames = () => {
  // Clear existing frame objects
  frameObjects.forEach((obj) => {
    scene.remove(obj)
    // Dispose of all children's geometries and materials
    obj.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => {
            if (m.map) m.map.dispose()
            m.dispose()
          })
        } else {
          if (child.material.map) child.material.map.dispose()
          child.material.dispose()
        }
      }
    })
  })
  frameObjects.clear()

  // Sort by explicit zOrder if present, otherwise largest-area-first
  const sortedPlacements = props.framePlacements
    .map((placement, index) => {
      const frame = placement.frame_id
        ? props.frames.find(f => f.id === placement.frame_id)
        : placement.picture_id
          ? props.frames.find(f => f.pictureId === placement.picture_id)
          : null
      const dims = frame?.dimensions?.cm || { width: 20, height: 25 }
      return { placement, originalIndex: index, area: dims.width * dims.height }
    })
    .sort((a, b) =>
      a.placement.zOrder !== undefined && b.placement.zOrder !== undefined
        ? a.placement.zOrder - b.placement.zOrder
        : b.area - a.area
    )

  sortedPlacements.forEach(({ placement, originalIndex }, sortedIndex) => {
    const frame = placement.frame_id
      ? props.frames.find(f => f.id === placement.frame_id)
      : placement.picture_id
        ? props.frames.find(f => f.pictureId === placement.picture_id)
        : null
    if (!frame) return
    if (placement.visible === false) return

    const dims = frame.dimensions?.cm || { width: 20, height: 25, depth: 2 }
    const scale = 0.01 // Convert cm to scene units
    const frameWidth = dims.width * scale
    const frameHeight = dims.height * scale
    const frameDepth = (dims.depth || 2) * scale
    const hasFrameBorder = !!frame.styling?.frame_color
    const thicknessInches = hasFrameBorder ? (frame.styling?.frame_thickness ?? 1) : 0
    const borderWidth = thicknessInches * 2.54 * scale // inches → cm → scene units

    // Create a group to hold frame parts
    const frameGroup = new THREE.Group()
    frameGroup.userData = { frameId: frame.id ?? `picture_${frame.pictureId ?? originalIndex}`, placementIndex: originalIndex }

    // Frame color (null frame_color means no physical frame border)
    const frameColor = hasFrameBorder ? new THREE.Color(frame.styling.frame_color) : null

    // Create the picture plane (image in center)
    const pictureWidth = frameWidth - borderWidth * 2
    const pictureHeight = frameHeight - borderWidth * 2
    const pictureGeometry = new THREE.PlaneGeometry(pictureWidth, pictureHeight)

    const imageUrl = frame.pictureImage
      ? (frame.pictureImage.startsWith('data:') || frame.pictureImage.startsWith('blob:')
          ? frame.pictureImage
          : getUploadUrl(frame.pictureImage))
      : null
    let pictureMaterial

    if (imageUrl) {
      const loader = new THREE.TextureLoader()
      const texture = loader.load(imageUrl)
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
    pictureMesh.position.z = frameDepth / 2 + 0.001
    frameGroup.add(pictureMesh)

    // Create frame border (4 boxes around the picture)
    const frameMaterial = frameColor ? new THREE.MeshStandardMaterial({ color: frameColor }) : null

    if (borderWidth > 0 && frameMaterial) {
      // Top border
      const topGeom = new THREE.BoxGeometry(frameWidth, borderWidth, frameDepth)
      const topBorder = new THREE.Mesh(topGeom, frameMaterial)
      topBorder.position.set(0, frameHeight / 2 - borderWidth / 2, 0)
      frameGroup.add(topBorder)

      // Bottom border
      const bottomBorder = new THREE.Mesh(topGeom.clone(), frameMaterial)
      bottomBorder.position.set(0, -frameHeight / 2 + borderWidth / 2, 0)
      frameGroup.add(bottomBorder)

      // Left border
      const sideGeom = new THREE.BoxGeometry(borderWidth, frameHeight - borderWidth * 2, frameDepth)
      const leftBorder = new THREE.Mesh(sideGeom, frameMaterial)
      leftBorder.position.set(-frameWidth / 2 + borderWidth / 2, 0, 0)
      frameGroup.add(leftBorder)

      // Right border
      const rightBorder = new THREE.Mesh(sideGeom.clone(), frameMaterial)
      rightBorder.position.set(frameWidth / 2 - borderWidth / 2, 0, 0)
      frameGroup.add(rightBorder)
    }

    // Back panel
    const backGeom = new THREE.PlaneGeometry(frameWidth, frameHeight)
    const backMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.BackSide })
    const backPanel = new THREE.Mesh(backGeom, backMaterial)
    backPanel.position.z = -frameDepth / 2
    frameGroup.add(backPanel)

    // Smaller frames (higher sortedIndex) sit slightly in front of larger frames.
    // 0.002 scene units (2 mm) per layer — invisible at normal viewing distance but
    // guarantees correct depth ordering regardless of overlap.
    const zLayerOffset = sortedIndex * 0.002
    const frameZ = -0.1 + 0.01 + frameDepth / 2 + zLayerOffset
    frameGroup.position.set(
      placement.position?.x || 0,
      placement.position?.y || 0,
      frameZ
    )

    scene.add(frameGroup)
    frameObjects.set(originalIndex, frameGroup)
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
watch(() => props.wallBackgroundColor, createWall)
watch(() => props.wallWidthCm, createWall)
watch(() => props.wallHeightCm, createWall)
watch(() => props.framePlacements, updateFrames, { deep: true })
watch(() => props.frames, updateFrames, { deep: true })

const captureScreenshot = () => {
  if (!renderer || !scene || !camera) return null
  renderer.render(scene, camera)
  return renderer.domElement.toDataURL('image/jpeg', 0.7)
}

defineExpose({ captureScreenshot })

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)
  if (touchScrollAnimId) cancelAnimationFrame(touchScrollAnimId)

  frameObjects.forEach((obj) => {
    obj.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => {
            if (m.map) m.map.dispose()
            m.dispose()
          })
        } else {
          if (child.material.map) child.material.map.dispose()
          child.material.dispose()
        }
      }
    })
  })

  if (renderer) {
    renderer.domElement.removeEventListener('mousedown', onMouseDown)
    renderer.domElement.removeEventListener('mousemove', onMouseMove)
    renderer.domElement.removeEventListener('mouseup', onMouseUp)
    containerRef.value?.removeEventListener('pointerdown', onTouchPointerDown, { capture: true })
    containerRef.value?.removeEventListener('pointermove', onTouchPointerMove, { capture: true })
    containerRef.value?.removeEventListener('pointerup', onTouchPointerUp, { capture: true })
    containerRef.value?.removeEventListener('pointercancel', onTouchPointerCancel, { capture: true })
    renderer.dispose()
    containerRef.value?.removeChild(renderer.domElement)
  }
  if (controls) controls.dispose()
})
</script>

<template>
  <div ref="containerRef" class="viewer-container w-full h-full rounded-lg overflow-hidden"></div>
</template>
