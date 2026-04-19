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
        <!-- Icon placeholder -->
        <div class="aspect-video bg-dark-300 rounded-lg flex items-center justify-center mb-3">
          <svg class="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>

        <h3 class="font-semibold text-lg mb-1">{{ reality.name }}</h3>
        <p v-if="reality.description" class="text-sm text-gray-400 mb-2 line-clamp-2">
          {{ reality.description }}
        </p>

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
            title="Edit name/description"
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
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4"
      @click.self="editingReality = null"
    >
      <div class="bg-dark-200 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h2 class="text-lg font-semibold mb-4">Edit Reality</h2>
        <div class="flex flex-col gap-3">
          <input
            v-model="editForm.name"
            type="text"
            placeholder="Name *"
            maxlength="100"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />
          <textarea
            v-model="editForm.description"
            placeholder="Description (optional)"
            rows="3"
            class="bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 resize-none"
          />
        </div>
        <div class="flex gap-3 mt-5">
          <button
            @click="submitEdit"
            class="btn btn-primary flex-1"
            :disabled="!editForm.name.trim()"
          >
            Save
          </button>
          <button @click="editingReality = null" class="btn btn-secondary">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRealitiesStore } from '@/store/realities'

const store = useRealitiesStore()
const loading = ref(true)

// Create modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = ref({ name: '', description: '' })

// Edit modal
const editingReality = ref(null)
const editForm = ref({ name: '', description: '' })

onMounted(async () => {
  try {
    await store.fetchRealities()
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
  editForm.value = { name: reality.name, description: reality.description || '' }
}

async function submitEdit() {
  if (!editForm.value.name.trim()) return
  await store.updateReality(editingReality.value.id, {
    name: editForm.value.name.trim(),
    description: editForm.value.description.trim() || null,
  })
  editingReality.value = null
}

async function deleteReality(id) {
  if (!confirm('Delete this Reality and all its contents?')) return
  await store.deleteReality(id)
}
</script>
