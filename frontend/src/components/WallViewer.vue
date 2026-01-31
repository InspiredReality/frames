<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { getUploadUrl } from '@/services/api'

const props = defineProps({
  wallImageUrl: String,
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
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // Add mouse listeners for frame dragging (left-click) and selection
  renderer.domElement.addEventListener('mousedown', onMouseDown)
  renderer.domElement.addEventListener('mousemove', onMouseMove)
  renderer.domElement.addEventListener('mouseup', onMouseUp)

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

const createWall = () => {
  if (wallMesh) {
    scene.remove(wallMesh)
    wallMesh.geometry.dispose()
    if (wallMesh.material.map) wallMesh.material.map.dispose()
    wallMesh.material.dispose()
  }

  // Use wall dimensions if available (cm -> scene units at 0.01 scale), fallback to default
  const wallW = (props.wallWidthCm > 0) ? props.wallWidthCm * 0.01 : 8
  const wallH = (props.wallHeightCm > 0) ? props.wallHeightCm * 0.01 : 6

  // Create wall plane
  const geometry = new THREE.PlaneGeometry(wallW, wallH)

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

  // Add frames based on placements
  props.framePlacements.forEach((placement, index) => {
    const frame = props.frames.find(f => f.id === placement.frame_id)
    if (!frame) return

    const dims = frame.dimensions?.cm || { width: 20, height: 25, depth: 2 }
    const scale = 0.01 // Convert cm to scene units
    const frameWidth = dims.width * scale
    const frameHeight = dims.height * scale
    const frameDepth = (dims.depth || 2) * scale
    const borderWidth = 0.02 // Frame border width in scene units

    // Create a group to hold frame parts
    const frameGroup = new THREE.Group()
    frameGroup.userData = { frameId: frame.id, placementIndex: index }

    // Frame color
    const frameColor = new THREE.Color(frame.styling?.frame_color || '#8B4513')

    // Create the picture plane (image in center)
    const pictureWidth = frameWidth - borderWidth * 2
    const pictureHeight = frameHeight - borderWidth * 2
    const pictureGeometry = new THREE.PlaneGeometry(pictureWidth, pictureHeight)

    // Load the image texture
    const imageUrl = frame.pictureImage ? getUploadUrl(frame.pictureImage) : null
    let pictureMaterial

    if (imageUrl) {
      const texture = textureLoader.load(imageUrl)
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
    const frameMaterial = new THREE.MeshStandardMaterial({ color: frameColor })

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

    // Back panel
    const backGeom = new THREE.PlaneGeometry(frameWidth, frameHeight)
    const backMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.BackSide })
    const backPanel = new THREE.Mesh(backGeom, backMaterial)
    backPanel.position.z = -frameDepth / 2
    frameGroup.add(backPanel)

    // Position the frame group: back of frame sits 1 cm (0.01 units) in front of wall (z=-0.1)
    const frameZ = -0.1 + 0.01 + frameDepth / 2
    frameGroup.position.set(
      placement.position?.x || 0,
      placement.position?.y || 0,
      frameZ
    )

    scene.add(frameGroup)
    frameObjects.set(index, frameGroup)
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
watch(() => props.wallWidthCm, createWall)
watch(() => props.wallHeightCm, createWall)
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
    renderer.dispose()
    containerRef.value?.removeChild(renderer.domElement)
  }
  if (controls) controls.dispose()
})
</script>

<template>
  <div ref="containerRef" class="viewer-container w-full h-96 rounded-lg overflow-hidden"></div>
</template>
