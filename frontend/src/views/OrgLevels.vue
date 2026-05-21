<template>
  <!-- Fixed below the sticky navbar (top-16 = 64px = h-16). Owns its own scroll. -->
  <div class="fixed inset-x-0 bottom-0 top-16 bg-dark-400 text-white flex flex-col z-10">
    <div class="max-w-4xl mx-auto w-full flex flex-col flex-1 min-h-0 px-4">

      <!-- Header -->
      <div class="flex items-center gap-3 py-4 shrink-0">
        <button
          @click="$router.push('/realities')"
          class="text-gray-400 hover:text-white transition text-sm shrink-0"
        >
          ← Realities
        </button>
        <div class="flex-1 min-w-0">
          <OrgBreadcrumb
            v-if="store.currentReality"
            :reality-name="store.currentReality.name"
            :path="selectedPath"
            @navigate="navigateTo"
          />
        </div>
      </div>

      <!-- Loading -->
      <div v-if="store.loading && !store.currentReality" class="text-center py-20 text-gray-400">
        Loading…
      </div>

      <!-- Error -->
      <div v-else-if="store.error" class="text-center py-20 text-red-400">
        {{ store.error }}
      </div>

      <!-- Reality not found -->
      <div v-else-if="!store.currentReality" class="text-center py-20 text-gray-400">
        Reality not found.
      </div>

      <!-- Panels — the ONLY scroll area on this page -->
      <div v-else class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 pb-6">
        <OrgObPanel
          v-for="panel in panels"
          :key="panel.level"
          :panel="panel"
          :is-active="panel.level === panels.length - 1"
          @select="selectOrgOb(panel.level, $event)"
          @add="addOrgOb(panel, $event)"
          @edit="openEditModal($event)"
          @delete="confirmDelete($event, panel)"
          @reorder="reorderPanel(panel, $event)"
        />

        <!-- Loading next panel -->
        <div v-if="loadingChildren" class="rounded-xl border border-gray-700 bg-dark-300 p-6 animate-pulse" />
      </div>
    </div>

    <!-- Edit modal -->
    <div
      v-if="editingOrgOb"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4"
      @click.self="editingOrgOb = null"
    >
      <div class="bg-dark-200 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h2 class="text-lg font-semibold mb-4">Edit</h2>
        <div class="flex flex-col gap-3">
          <input
            v-model="editForm.name"
            type="text"
            placeholder="Name"
            maxlength="200"
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
          <button @click="saveEdit" class="btn btn-primary flex-1" :disabled="!editForm.name.trim()">
            Save
          </button>
          <button @click="editingOrgOb = null" class="btn btn-secondary">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRealitiesStore } from '@/store/realities'
import OrgObPanel from '@/components/OrgObPanel.vue'
import OrgBreadcrumb from '@/components/OrgBreadcrumb.vue'

const route = useRoute()
const store = useRealitiesStore()

const realityId = Number(route.params.id)

// selectedPath[i] = the OrgOb selected at panel level i
const selectedPath = ref([])
const loadingChildren = ref(false)

// Edit modal state
const editingOrgOb = ref(null)
const editForm = ref({ name: '', description: '' })

// ----------------------------
// Computed panels
// ----------------------------
const panels = computed(() => {
  const result = [{
    level: 0,
    parentOrgOb: null,
    nodes: store.getChildren(realityId, null),
    selectedNode: selectedPath.value[0] ?? null,
  }]

  for (let i = 0; i < selectedPath.value.length; i++) {
    const parent = selectedPath.value[i]
    result.push({
      level: i + 1,
      parentOrgOb: parent,
      nodes: store.getChildren(realityId, parent.id),
      selectedNode: selectedPath.value[i + 1] ?? null,
    })
  }

  return result
})

// ----------------------------
// Lifecycle
// ----------------------------
onMounted(async () => {
  store.clearCache()
  await store.fetchReality(realityId)
  await store.fetchTopLevel(realityId)
})

// ----------------------------
// Interactions
// ----------------------------
async function selectOrgOb(level, orgOb) {
  // Truncate path at this level and set new selection
  selectedPath.value = [...selectedPath.value.slice(0, level), orgOb]

  // Lazy-load children if not already cached
  if (!store.orgObCache[orgOb.id]) {
    loadingChildren.value = true
    try {
      await store.fetchOrgOb(orgOb.id)
    } finally {
      loadingChildren.value = false
    }
  }
}

function navigateTo(pathIndex) {
  // pathIndex = -1 → collapse to top-level only; >= 0 → truncate at that index
  if (pathIndex < 0) {
    selectedPath.value = []
  } else {
    selectedPath.value = selectedPath.value.slice(0, pathIndex + 1)
  }
}

async function addOrgOb(panel, { name, description, parentOrgOb }) {
  const parentId = parentOrgOb ? parentOrgOb.id : null
  await store.createOrgOb(realityId, {
    name,
    description,
    parent_id: parentId,
    order_index: store.getChildren(realityId, parentId).length,
  })
}

function openEditModal(orgOb) {
  editingOrgOb.value = orgOb
  editForm.value = { name: orgOb.name, description: orgOb.description || '' }
}

async function saveEdit() {
  if (!editForm.value.name.trim()) return
  const updated = await store.updateOrgOb(editingOrgOb.value.id, {
    name: editForm.value.name.trim(),
    description: editForm.value.description.trim() || null,
  })
  // Refresh selectedPath so the breadcrumb and panel headers reflect the new name
  const pathIdx = selectedPath.value.findIndex(n => n.id === updated.id)
  if (pathIdx !== -1) {
    selectedPath.value = selectedPath.value.map((n, i) => i === pathIdx ? updated : n)
  }
  editingOrgOb.value = null
}

async function reorderPanel(panel, orderedIds) {
  const parentId = panel.parentOrgOb ? panel.parentOrgOb.id : null
  await store.reorderOrgObs(realityId, parentId, orderedIds)
}

async function confirmDelete(orgOb, panel) {
  if (!confirm(`Delete "${orgOb.name}" and all its children?`)) return
  await store.deleteOrgOb(orgOb.id, orgOb.parent_id, realityId)

  // If the deleted item was in the selected path, truncate there
  const pathIdx = selectedPath.value.findIndex(n => n.id === orgOb.id)
  if (pathIdx !== -1) {
    selectedPath.value = selectedPath.value.slice(0, pathIdx)
  }
}
</script>
