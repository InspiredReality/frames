import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useWallsStore = defineStore('walls', () => {
  const walls = ref([])
  const currentWall = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchWalls() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/walls')
      walls.value = response.data.walls
      return walls.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchWall(wallId) {
    loading.value = true
    try {
      const response = await api.get(`/walls/${wallId}`)
      currentWall.value = response.data.wall
      return currentWall.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadWall(file, name, description = '', dimensions = {}) {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('name', name)
    formData.append('description', description)
    if (dimensions.width_cm) formData.append('width_cm', dimensions.width_cm)
    if (dimensions.height_cm) formData.append('height_cm', dimensions.height_cm)

    const response = await api.post('/walls', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    walls.value.unshift(response.data.wall)
    return response.data.wall
  }

  async function updateWall(wallId, updates) {
    const response = await api.put(`/walls/${wallId}`, updates)

    // Update local state
    const index = walls.value.findIndex(w => w.id === wallId)
    if (index !== -1) {
      walls.value[index] = response.data.wall
    }
    if (currentWall.value?.id === wallId) {
      currentWall.value = response.data.wall
    }

    return response.data.wall
  }

  async function addFramePlacement(wallId, placement) {
    const response = await api.post(`/walls/${wallId}/placements`, placement)

    if (currentWall.value?.id === wallId) {
      currentWall.value = response.data.wall
    }

    return response.data.wall
  }

  async function deleteWall(wallId) {
    await api.delete(`/walls/${wallId}`)
    walls.value = walls.value.filter(w => w.id !== wallId)
    if (currentWall.value?.id === wallId) {
      currentWall.value = null
    }
  }

  function getWallById(id) {
    return walls.value.find(w => w.id === id)
  }

  return {
    walls,
    currentWall,
    loading,
    error,
    fetchWalls,
    fetchWall,
    uploadWall,
    updateWall,
    addFramePlacement,
    deleteWall,
    getWallById
  }
})
