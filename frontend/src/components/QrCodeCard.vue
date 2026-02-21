<script setup>
import { ref, watch, onMounted } from 'vue'
import QRCode from 'qrcode'

const props = defineProps({
  url: {
    type: String,
    default: () => window.location.href
  }
})

const qrDataUrl = ref(null)

const generateQr = async () => {
  try {
    qrDataUrl.value = await QRCode.toDataURL(props.url, {
      width: 200,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff'
      }
    })
  } catch (err) {
    console.error('QR code generation failed:', err)
  }
}

onMounted(generateQr)
watch(() => props.url, generateQr)
</script>

<template>
  <div class="hidden md:block card text-center max-w-xs mx-auto">
    <img
      v-if="qrDataUrl"
      :src="qrDataUrl"
      alt="QR code to open this page on your phone"
      class="mx-auto rounded-lg"
    />
    <p class="text-sm text-gray-400 mt-2">
      Scan with your phone to continue on mobile
    </p>
  </div>
</template>
