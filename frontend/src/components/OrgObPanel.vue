<template>
  <div
    class="rounded-xl border transition-colors"
    :class="isActive ? 'border-primary-500/60 bg-dark-200' : 'border-gray-700 bg-dark-300'"
  >
    <!-- Panel header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700/50">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-400">
        {{ panel.parentOrgOb ? panel.parentOrgOb.name : 'Top Level' }}
      </h3>
      <button
        v-if="!showForm"
        @click="showForm = true"
        class="text-xs text-primary-400 hover:text-primary-300 transition flex items-center gap-1"
      >
        <span class="text-base leading-none">+</span> Add
      </button>
    </div>

    <!-- Node list -->
    <div class="px-3 py-2 flex flex-col gap-1">
      <div
        v-if="panel.nodes.length === 0 && !showForm"
        class="text-gray-500 text-sm py-2 text-center"
      >
        Empty — add the first item above
      </div>

      <div
        v-for="node in panel.nodes"
        :key="node.id"
        class="flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer transition group"
        :class="
          panel.selectedNode?.id === node.id
            ? 'bg-primary-500/20 border border-primary-500/50'
            : 'hover:bg-dark-100 border border-transparent'
        "
        @click="$emit('select', node)"
      >
        <div class="flex items-center gap-2 min-w-0">
          <span class="font-medium text-sm text-white truncate">{{ node.name }}</span>
          <span
            v-if="node.children_count > 0"
            class="text-xs text-gray-500 shrink-0"
          >
            {{ node.children_count }}
          </span>
        </div>
        <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            @click.stop="$emit('edit', node)"
            class="text-gray-400 hover:text-white text-xs px-1"
            title="Edit"
          >
            ✎
          </button>
          <button
            @click.stop="$emit('delete', node)"
            class="text-red-500 hover:text-red-400 text-xs px-1"
            title="Delete"
          >
            ✕
          </button>
        </div>
        <span
          v-if="panel.selectedNode?.id === node.id"
          class="text-primary-400 text-xs ml-1 shrink-0"
        >▶</span>
      </div>

      <!-- Inline add form -->
      <AddOrgObForm
        v-if="showForm"
        @submit="handleAdd"
        @cancel="showForm = false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AddOrgObForm from './AddOrgObForm.vue'

const props = defineProps({
  panel: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'add', 'edit', 'delete'])

const showForm = ref(false)

function handleAdd(data) {
  showForm.value = false
  emit('add', { ...data, parentOrgOb: props.panel.parentOrgOb })
}
</script>
