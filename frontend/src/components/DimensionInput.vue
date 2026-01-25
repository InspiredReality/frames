<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ width: '', height: '', depth: 1, unit: 'inches' })
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

const commonSizes = computed(() => {
  if (localValue.value.unit === 'inches') {
    return [
      { label: '4x6', width: 4, height: 6 },
      { label: '5x7', width: 5, height: 7 },
      { label: '8x10', width: 8, height: 10 },
      { label: '11x14', width: 11, height: 14 },
      { label: '16x20', width: 16, height: 20 },
      { label: '24x36', width: 24, height: 36 },
    ]
  } else {
    return [
      { label: '10x15', width: 10, height: 15 },
      { label: '13x18', width: 13, height: 18 },
      { label: '20x25', width: 20, height: 25 },
      { label: '28x36', width: 28, height: 36 },
      { label: '40x50', width: 40, height: 50 },
      { label: '60x90', width: 60, height: 90 },
    ]
  }
})

const selectSize = (size) => {
  localValue.value.width = size.width
  localValue.value.height = size.height
  updateValue()
}
</script>

<template>
  <div class="space-y-4">
    <!-- Unit toggle -->
    <div class="flex items-center justify-between">
      <span class="text-sm text-gray-400">Dimensions</span>
      <button
        @click="toggleUnit"
        class="px-3 py-1 text-sm bg-dark-300 rounded-full hover:bg-dark-100 transition"
      >
        {{ localValue.unit === 'inches' ? 'Switch to cm' : 'Switch to inches' }}
      </button>
    </div>

    <!-- Common sizes -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="size in commonSizes"
        :key="size.label"
        @click="selectSize(size)"
        class="px-3 py-1 text-sm bg-dark-300 rounded-lg hover:bg-primary-600 transition"
        :class="{ 'bg-primary-600': localValue.width == size.width && localValue.height == size.height }"
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
