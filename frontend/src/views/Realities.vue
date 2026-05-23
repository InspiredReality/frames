<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Realities</h1>
      <button @click="showCreateModal = true" class="btn btn-primary">
        New Reality
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="store.realities.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h3 class="text-xl font-semibold mb-2">No realities yet</h3>
      <p class="text-gray-400 mb-4">Create a Reality to start building your org hierarchy</p>
      <button @click="showCreateModal = true" class="btn btn-primary">
        Create Reality
      </button>
    </div>

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="reality in store.realities"
        :key="reality.id"
        class="card cursor-pointer hover:border-primary-500/50 transition-colors border border-transparent"
        @click="$router.push(`/reality/${reality.id}`)"
      >
        <!-- Cover image / placeholder -->
        <div class="aspect-video bg-dark-300 rounded-lg flex items-center justify-center mb-3 overflow-hidden">
          <img
            v-if="reality.image_path"
            :src="store.getRealityImageUrl(reality.image_path)"
            class="w-full h-full object-cover"
            :alt="reality.name"
          />
          <svg v-else class="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>

        <h3 class="font-semibold text-lg mb-1">{{ reality.name }}</h3>
        <p v-if="reality.description" class="text-sm text-gray-400 mb-2 line-clamp-2">
          {{ reality.description }}
        </p>

        <!-- Dimensions badge -->
        <p v-if="reality.width_m || reality.length_m" class="text-xs text-gray-500 mb-2">
          {{ reality.length_m ? reality.length_m + ' m' : '—' }} × {{ reality.width_m ? reality.width_m + ' m' : '—' }}
        </p>

        <!-- Tags -->
        <div v-if="reality.tags && reality.tags.length" class="flex flex-wrap gap-1 mb-3">
          <span
            v-for="tag in reality.tags"
            :key="tag.id"
            class="text-xs px-2 py-0.5 rounded-full font-medium"
            :style="{ backgroundColor: tag.color + '33', color: tag.color }"
          >{{ tag.name }}</span>
        </div>

        <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
          <span>{{ reality.org_ob_count }} item{{ reality.org_ob_count !== 1 ? 's' : '' }}</span>
          <span>{{ formatDate(reality.created_at) }}</span>
        </div>

        <div class="flex gap-2">
          <router-link
            :to="`/reality/${reality.id}`"
            class="btn btn-primary flex-1 text-center"
            @click.stop
          >
            Open
          </router-link>
          <button
            @click.stop="startEdit(reality)"
            class="btn btn-secondary"
            title="Edit"
          >
            ✎
          </button>
          <button
            @click.stop="deleteReality(reality.id)"
            class="btn bg-red-600/20 text-red-400 hover:bg-red-600 hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4"
      @click.self="closeCreateModal"
    >
      <div class="bg-dark-200 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h2 class="text-lg font-semibold mb-4">New Reality</h2>
        <div class="flex flex-col gap-3">
          <input
            v-model="createForm.name"
            type="text"
            placeholder="Name *"
            maxlength="100"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
            @keydown.enter="submitCreate"
          />
          <textarea
            v-model="createForm.description"
            placeholder="Description (optional)"
            rows="3"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 resize-none"
          />
        </div>
        <p v-if="createError" class="text-red-400 text-sm mt-3">{{ createError }}</p>
        <div class="flex gap-3 mt-5">
          <button
            @click="submitCreate"
            class="btn btn-primary flex-1"
            :disabled="!createForm.name.trim() || creating"
          >
            {{ creating ? 'Creating…' : 'Create' }}
          </button>
          <button @click="closeCreateModal" class="btn btn-secondary">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div
      v-if="editingReality"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4 overflow-y-auto py-8"
      @click.self="closeEditModal"
    >
      <div class="bg-dark-200 rounded-2xl p-6 w-full max-w-md shadow-2xl my-auto">
        <h2 class="text-lg font-semibold mb-4">Edit Reality</h2>

        <!-- Photo area -->
        <div
          class="aspect-video bg-dark-300 rounded-lg flex items-center justify-center mb-4 overflow-hidden relative cursor-pointer group"
          @click="triggerPhotoInput"
        >
          <img
            v-if="editPhotoPreview || editingReality.image_path"
            :src="editPhotoPreview || store.getRealityImageUrl(editingReality.image_path)"
            class="w-full h-full object-cover"
            alt="Cover photo"
          />
          <div v-else class="flex flex-col items-center gap-2 text-gray-500">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="text-sm">Add photo</span>
          </div>
          <div
            v-if="editPhotoPreview || editingReality.image_path"
            class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
          >
            <span class="text-white text-sm font-medium">Change photo</span>
          </div>
        </div>

        <input
          ref="photoInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="onPhotoSelected"
        />

        <div class="flex flex-col gap-3">
          <!-- Name -->
          <input
            v-model="editForm.name"
            type="text"
            placeholder="Name *"
            maxlength="100"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />

          <!-- Description -->
          <textarea
            v-model="editForm.description"
            placeholder="Description (optional)"
            rows="2"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 resize-none"
          />

          <!-- Dimensions -->
          <div class="flex gap-2">
            <div class="flex-1">
              <label class="text-xs text-gray-400 mb-1 block">Length (m)</label>
              <input
                v-model.number="editForm.length_m"
                type="number"
                min="0"
                step="0.1"
                placeholder="e.g. 10"
                class="w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div class="flex-1">
              <label class="text-xs text-gray-400 mb-1 block">Width (m)</label>
              <input
                v-model.number="editForm.width_m"
                type="number"
                min="0"
                step="0.1"
                placeholder="e.g. 8"
                class="w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          <!-- Tags -->
          <div>
            <label class="text-xs text-gray-400 mb-2 block">Tags</label>

            <!-- Selected tags -->
            <div v-if="editForm.selectedTags.length" class="flex flex-wrap gap-1 mb-2">
              <button
                v-for="tag in editForm.selectedTags"
                :key="tag.id"
                type="button"
                class="text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1"
                :style="{ backgroundColor: tag.color + '33', color: tag.color }"
                @click="removeTag(tag)"
              >
                {{ tag.name }}
                <span class="text-xs opacity-70">✕</span>
              </button>
            </div>

            <!-- Tag search / add -->
            <div class="relative">
              <input
                v-model="tagSearch"
                type="text"
                placeholder="Search or create tag…"
                class="w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
                @focus="showTagDropdown = true"
                @blur="onTagBlur"
                @keydown.enter.prevent="onTagEnter"
              />
              <div
                v-if="showTagDropdown && (filteredTags.length || tagSearch.trim())"
                class="absolute z-10 w-full mt-1 bg-dark-100 border border-gray-600 rounded-lg shadow-xl overflow-hidden"
              >
                <button
                  v-for="tag in filteredTags"
                  :key="tag.id"
                  type="button"
                  class="w-full text-left px-3 py-2 text-sm hover:bg-dark-300 flex items-center gap-2"
                  @mousedown.prevent="selectTag(tag)"
                >
                  <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: tag.color }"></span>
                  {{ tag.name }}
                </button>
                <button
                  v-if="tagSearch.trim() && !exactTagMatch"
                  type="button"
                  class="w-full text-left px-3 py-2 text-sm text-primary-400 hover:bg-dark-300 flex items-center gap-2"
                  @mousedown.prevent="createAndSelectTag"
                >
                  <span class="text-lg leading-none">+</span>
                  Create "{{ tagSearch.trim() }}"
                </button>
              </div>
            </div>
          </div>
        </div>

        <p v-if="editError" class="text-red-400 text-sm mt-3">{{ editError }}</p>
        <div class="flex gap-3 mt-5">
          <button
            @click="submitEdit"
            class="btn btn-primary flex-1"
            :disabled="!editForm.name.trim() || editSaving"
          >
            {{ editSaving ? 'Saving…' : 'Save' }}
          </button>
          <button @click="closeEditModal" class="btn btn-secondary">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRealitiesStore } from '@/store/realities'
import { useTagsStore } from '@/store/tags'

const store = useRealitiesStore()
const tagsStore = useTagsStore()
const loading = ref(true)

// Create modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = ref({ name: '', description: '' })

// Edit modal
const editingReality = ref(null)
const editForm = ref({ name: '', description: '', length_m: null, width_m: null, selectedTags: [] })
const editSaving = ref(false)
const editError = ref('')
const editPhotoPreview = ref(null)
const editPhotoFile = ref(null)
const photoInputRef = ref(null)

// Tag picker
const tagSearch = ref('')
const showTagDropdown = ref(false)

const filteredTags = computed(() => {
  const q = tagSearch.value.trim().toLowerCase()
  const selectedIds = new Set(editForm.value.selectedTags.map(t => t.id))
  return tagsStore.tags.filter(t =>
    !selectedIds.has(t.id) && (!q || t.name.toLowerCase().includes(q))
  )
})

const exactTagMatch = computed(() =>
  tagsStore.tags.some(t => t.name.toLowerCase() === tagSearch.value.trim().toLowerCase())
)

onMounted(async () => {
  try {
    await Promise.all([store.fetchRealities(), tagsStore.fetchTags()])
  } finally {
    loading.value = false
  }
})

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function closeCreateModal() {
  showCreateModal.value = false
  createError.value = ''
  createForm.value = { name: '', description: '' }
}

async function submitCreate() {
  if (!createForm.value.name.trim()) return
  creating.value = true
  createError.value = ''
  try {
    await store.createReality({
      name: createForm.value.name.trim(),
      description: createForm.value.description.trim() || null,
    })
    closeCreateModal()
  } catch (err) {
    createError.value = err.response?.data?.detail || err.message || 'Failed to create reality'
  } finally {
    creating.value = false
  }
}

function startEdit(reality) {
  editingReality.value = reality
  editForm.value = {
    name: reality.name,
    description: reality.description || '',
    length_m: reality.length_m ?? null,
    width_m: reality.width_m ?? null,
    selectedTags: [...(reality.tags || [])],
  }
  editPhotoPreview.value = null
  editPhotoFile.value = null
  editError.value = ''
  tagSearch.value = ''
  showTagDropdown.value = false
}

function closeEditModal() {
  editingReality.value = null
  editPhotoPreview.value = null
  editPhotoFile.value = null
  editError.value = ''
  tagSearch.value = ''
  showTagDropdown.value = false
}

function triggerPhotoInput() {
  photoInputRef.value?.click()
}

function onPhotoSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  editPhotoFile.value = file
  editPhotoPreview.value = URL.createObjectURL(file)
  event.target.value = ''
}

// Tag helpers
function selectTag(tag) {
  if (!editForm.value.selectedTags.find(t => t.id === tag.id)) {
    editForm.value.selectedTags.push(tag)
  }
  tagSearch.value = ''
  showTagDropdown.value = false
}

function removeTag(tag) {
  editForm.value.selectedTags = editForm.value.selectedTags.filter(t => t.id !== tag.id)
}

async function createAndSelectTag() {
  const name = tagSearch.value.trim()
  if (!name) return
  try {
    const tag = await tagsStore.createTag(name)
    selectTag(tag)
  } catch (err) {
    // ignore
  }
}

function onTagEnter() {
  if (filteredTags.value.length) {
    selectTag(filteredTags.value[0])
  } else if (tagSearch.value.trim() && !exactTagMatch.value) {
    createAndSelectTag()
  }
}

function onTagBlur() {
  setTimeout(() => { showTagDropdown.value = false }, 150)
}

async function submitEdit() {
  if (!editForm.value.name.trim()) return
  editSaving.value = true
  editError.value = ''
  try {
    await store.updateReality(editingReality.value.id, {
      name: editForm.value.name.trim(),
      description: editForm.value.description.trim() || null,
      length_m: editForm.value.length_m || null,
      width_m: editForm.value.width_m || null,
      tag_ids: editForm.value.selectedTags.map(t => t.id),
    })
    if (editPhotoFile.value) {
      await store.uploadRealityImage(editingReality.value.id, editPhotoFile.value)
    }
    closeEditModal()
  } catch (err) {
    editError.value = err.response?.data?.detail || err.message || 'Failed to save'
  } finally {
    editSaving.value = false
  }
}

async function deleteReality(id) {
  if (!confirm('Delete this Reality and all its contents?')) return
  await store.deleteReality(id)
}
</script>
