import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const usePicturesStore = defineStore('pictures', () => {
  const pictures = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchPictures() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/pictures')
      pictures.value = response.data.pictures
      return pictures.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadPicture(file, name, description = '', wallId = null) {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('name', name)
    formData.append('description', description)
    if (wallId) {
      formData.append('wall_id', wallId)
    }

    const response = await api.post('/pictures', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    pictures.value.unshift(response.data.picture)
    return response.data.picture
  }

  async function updatePicture(pictureId, updates) {
    const response = await api.put(`/pictures/${pictureId}`, updates)

    // Update local state
    const index = pictures.value.findIndex(p => p.id === pictureId)
    if (index !== -1) {
      pictures.value[index] = response.data.picture
    }

    return response.data.picture
  }

  // Get frames by wall ID
  function getFramesByWall(wallId) {
    if (!wallId) {
      return pictures.value.filter(p => !p.wall_id)
    }
    return pictures.value.filter(p => p.wall_id === wallId)
  }

  async function createFrame(pictureId, dimensions) {
    const response = await api.post(`/pictures/${pictureId}/frames`, dimensions)

    // Update local state
    const picture = pictures.value.find(p => p.id === pictureId)
    if (picture) {
      if (!picture.frames) picture.frames = []
      picture.frames.push(response.data.frame)
    }

    return response.data.frame
  }

  async function updateFrame(pictureId, frameId, updates) {
    const response = await api.put(`/pictures/${pictureId}/frames/${frameId}`, updates)

    // Update local state
    const picture = pictures.value.find(p => p.id === pictureId)
    if (picture && picture.frames) {
      const frameIndex = picture.frames.findIndex(f => f.id === frameId)
      if (frameIndex !== -1) {
        picture.frames[frameIndex] = response.data.frame
      }
    }

    return response.data.frame
  }

  async function deletePicture(pictureId) {
    await api.delete(`/pictures/${pictureId}`)
    pictures.value = pictures.value.filter(p => p.id !== pictureId)
  }

  function getPictureById(id) {
    return pictures.value.find(p => p.id === id)
  }

  return {
    pictures,
    loading,
    error,
    fetchPictures,
    uploadPicture,
    updatePicture,
    createFrame,
    updateFrame,
    deletePicture,
    getPictureById,
    getFramesByWall
  }
})
