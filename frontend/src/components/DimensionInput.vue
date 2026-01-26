<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ width: '', height: '', depth: 1, unit: 'inches', orientation: 'portrait' })
  }
})

const emit = defineEmits(['update:modelValue'])

const localValue = ref({ ...props.modelValue })

const INCHES_TO_CM = 2.54

watch(() => props.modelValue, (newVal) => {
  localValue.value = { ...newVal }
}, { deep: true })

const updateValue = () => {
  emit('update:modelValue', { ...localValue.value })
}

const toggleUnit = () => {
  const newUnit = localValue.value.unit === 'inches' ? 'cm' : 'inches'

  if (localValue.value.width) {
    localValue.value.width = newUnit === 'cm'
      ? (parseFloat(localValue.value.width) * INCHES_TO_CM).toFixed(1)
      : (parseFloat(localValue.value.width) / INCHES_TO_CM).toFixed(1)
  }

  if (localValue.value.height) {
    localValue.value.height = newUnit === 'cm'
      ? (parseFloat(localValue.value.height) * INCHES_TO_CM).toFixed(1)
      : (parseFloat(localValue.value.height) / INCHES_TO_CM).toFixed(1)
  }

  if (localValue.value.depth) {
    localValue.value.depth = newUnit === 'cm'
      ? (parseFloat(localValue.value.depth) * INCHES_TO_CM).toFixed(1)
      : (parseFloat(localValue.value.depth) / INCHES_TO_CM).toFixed(1)
  }

  localValue.value.unit = newUnit
  updateValue()
}

const toggleOrientation = () => {
  // Toggle orientation state
  const newOrientation = localValue.value.orientation === 'portrait' ? 'landscape' : 'portrait'
  localValue.value.orientation = newOrientation

  // Swap width and height if they exist
  if (localValue.value.width || localValue.value.height) {
    const temp = localValue.value.width
    localValue.value.width = localValue.value.height
    localValue.value.height = temp
  }

  updateValue()
}

const isPortrait = computed(() => {
  // Use explicit orientation state, not just dimension comparison
  return localValue.value.orientation === 'portrait'
})

// Base sizes (always stored as portrait - smaller dimension first)
const baseSizes = computed(() => {
  if (localValue.value.unit === 'inches') {
    return [
      { label: '4x6', small: 4, large: 6 },
      { label: '5x7', small: 5, large: 7 },
      { label: '8x10', small: 8, large: 10 },
      { label: '11x14', small: 11, large: 14 },
      { label: '16x20', small: 16, large: 20 },
      { label: '24x36', small: 24, large: 36 },
    ]
  } else {
    return [
      { label: '10x15', small: 10, large: 15 },
      { label: '13x18', small: 13, large: 18 },
      { label: '20x25', small: 20, large: 25 },
      { label: '28x36', small: 28, large: 36 },
      { label: '40x50', small: 40, large: 50 },
      { label: '60x90', small: 60, large: 90 },
    ]
  }
})

const selectSize = (size) => {
  // Apply based on current orientation state
  if (localValue.value.orientation === 'portrait') {
    localValue.value.width = size.small
    localValue.value.height = size.large
  } else {
    localValue.value.width = size.large
    localValue.value.height = size.small
  }
  updateValue()
}

const isSizeSelected = (size) => {
  const w = parseFloat(localValue.value.width) || 0
  const h = parseFloat(localValue.value.height) || 0
  return (w === size.small && h === size.large) || (w === size.large && h === size.small)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Unit and Orientation toggles -->
    <div class="flex items-center justify-between gap-2">
      <span class="text-sm text-gray-400">Dimensions</span>
      <div class="flex gap-2">
        <!-- Orientation toggle -->
        <button
          @click="toggleOrientation"
          class="flex items-center gap-1 px-3 py-1 text-sm bg-dark-300 rounded-full hover:bg-dark-100 transition"
          :title="isPortrait ? 'Switch to Landscape' : 'Switch to Portrait'"
        >
          <svg
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-90': !isPortrait }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <rect x="5" y="3" width="14" height="18" rx="2" stroke-width="2"/>
          </svg>
          <span>{{ isPortrait ? 'Portrait' : 'Landscape' }}</span>
        </button>
        <!-- Unit toggle -->
        <button
          @click="toggleUnit"
          class="px-3 py-1 text-sm bg-dark-300 rounded-full hover:bg-dark-100 transition"
        >
          {{ localValue.unit === 'inches' ? 'Switch to cm' : 'Switch to inches' }}
        </button>
      </div>
    </div>

    <!-- Common sizes -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="size in baseSizes"
        :key="size.label"
        @click="selectSize(size)"
        class="px-3 py-1 text-sm bg-dark-300 rounded-lg hover:bg-primary-600 transition"
        :class="{ 'bg-primary-600': isSizeSelected(size) }"
      >
        {{ size.label }}
      </button>
    </div>

    <!-- Manual input -->
    <div class="grid grid-cols-3 gap-3">
      <div>
        <label class="block text-xs text-gray-400 mb-1">Width ({{ localValue.unit }})</label>
        <input
          v-model="localValue.width"
          type="number"
          step="0.1"
          min="0"
          @input="updateValue"
          class="w-full"
          placeholder="Width"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-400 mb-1">Height ({{ localValue.unit }})</label>
        <input
          v-model="localValue.height"
          type="number"
          step="0.1"
          min="0"
          @input="updateValue"
          class="w-full"
          placeholder="Height"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-400 mb-1">Depth ({{ localValue.unit }})</label>
        <input
          v-model="localValue.depth"
          type="number"
          step="0.1"
          min="0"
          @input="updateValue"
          class="w-full"
          placeholder="Depth"
        />
      </div>
    </div>
  </div>
</template>
