<script setup>
import { computed } from 'vue'

const props = defineProps({
  imageUrl: {
    type: String,
    required: true
  },
  widthCm: {
    type: Number,
    default: 20
  },
  heightCm: {
    type: Number,
    default: 25
  },
  frameColor: {
    type: String,
    default: '#8B4513'
  },
  matColor: {
    type: String,
    default: '#FFFFFF'
  },
  matWidthPercent: {
    type: Number,
    default: 5
  },
  maxWidth: {
    type: Number,
    default: 400
  },
  maxHeight: {
    type: Number,
    default: 400
  },
  showDimensions: {
    type: Boolean,
    default: false
  }
})

const frameBorderWidth = computed(() => 12)

const containerStyle = computed(() => {
  const aspectRatio = props.widthCm / props.heightCm
  let width, height
  const borderTotal = frameBorderWidth.value * 2 + (props.matWidthPercent > 0 ? 8 : 0)

  if (aspectRatio > 1) {
    width = props.maxWidth - borderTotal
    height = width / aspectRatio
    if (height > props.maxHeight - borderTotal) {
      height = props.maxHeight - borderTotal
      width = height * aspectRatio
    }
  } else {
    height = props.maxHeight - borderTotal
    width = height * aspectRatio
    if (width > props.maxWidth - borderTotal) {
      width = props.maxWidth - borderTotal
      height = width / aspectRatio
    }
  }

  return {
    width: Math.max(width, 50) + 'px',
    height: Math.max(height, 50) + 'px'
  }
})

const frameStyle = computed(() => {
  const bw = frameBorderWidth.value
  return {
    padding: bw + 'px',
    background: 'linear-gradient(135deg, ' + lightenColor(props.frameColor, 20) + ' 0%, ' + props.frameColor + ' 50%, ' + darkenColor(props.frameColor, 20) + ' 100%)',
    boxShadow: 'inset 2px 2px 3px rgba(255,255,255,0.25), inset -2px -2px 3px rgba(0,0,0,0.25), 4px 4px 10px rgba(0,0,0,0.4)',
    borderRadius: '2px'
  }
})

const matStyle = computed(() => {
  if (props.matWidthPercent <= 0) return { padding: '0' }
  return {
    padding: '4px',
    background: props.matColor,
    boxShadow: 'inset 1px 1px 2px rgba(0,0,0,0.1)'
  }
})

const dimensionsText = computed(() => {
  const widthIn = (props.widthCm / 2.54).toFixed(1)
  const heightIn = (props.heightCm / 2.54).toFixed(1)
  return widthIn + '" x ' + heightIn + '" (' + props.widthCm.toFixed(0) + ' x ' + props.heightCm.toFixed(0) + ' cm)'
})

function lightenColor(color, percent) {
  const num = parseInt(color.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.min(255, (num >> 16) + amt)
  const G = Math.min(255, ((num >> 8) & 0x00FF) + amt)
  const B = Math.min(255, (num & 0x0000FF) + amt)
  return '#' + (1 << 24 | R << 16 | G << 8 | B).toString(16).slice(1)
}

function darkenColor(color, percent) {
  const num = parseInt(color.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.max(0, (num >> 16) - amt)
  const G = Math.max(0, ((num >> 8) & 0x00FF) - amt)
  const B = Math.max(0, (num & 0x0000FF) - amt)
  return '#' + (1 << 24 | R << 16 | G << 8 | B).toString(16).slice(1)
}
</script>

<template>
  <div class="frame-preview-wrapper">
    <div class="frame-outer" :style="frameStyle">
      <div class="frame-mat" :style="matStyle">
        <div class="frame-image" :style="containerStyle">
          <img :src="imageUrl" alt="Framed picture" />
        </div>
      </div>
    </div>
    <p v-if="showDimensions" class="dimensions-label">
      {{ dimensionsText }}
    </p>
  </div>
</template>

<style scoped>
.frame-preview-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.frame-outer {
  display: inline-block;
}

.frame-mat {
  display: inline-block;
}

.frame-image {
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.frame-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.dimensions-label {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #9ca3af;
  text-align: center;
}
</style>
