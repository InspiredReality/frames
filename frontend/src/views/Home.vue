<script setup>
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="max-w-4xl mx-auto text-center py-12">
    <!-- Hero Section -->
    <h1 class="text-4xl md:text-5xl font-bold mb-6">
      Visualize Your Art on <span class="text-primary-500">Any Wall</span>
    </h1>
    <p class="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
      Take a photo of your picture frame, capture your wall, and see exactly how it looks before hanging. Perfect for galleries, home decor, and interior design.
    </p>

    <!-- CTA Buttons -->
    <div class="flex flex-col sm:flex-row gap-4 justify-center mb-16">
      <template v-if="authStore.isAuthenticated">
        <router-link to="/capture/frame" class="btn btn-primary text-lg px-8 py-3">
          Capture a Frame
        </router-link>
        <router-link to="/capture/wall" class="btn btn-secondary text-lg px-8 py-3">
          Capture a Wall
        </router-link>
      </template>
      <template v-else>
        <router-link to="/register" class="btn btn-primary text-lg px-8 py-3">
          Get Started Free
        </router-link>
        <router-link to="/login" class="btn btn-secondary text-lg px-8 py-3">
          Sign In
        </router-link>
      </template>
    </div>

    <!-- Features -->
    <div class="grid md:grid-cols-3 gap-8 mt-12">
      <div class="card text-center">
        <div class="w-16 h-16 mx-auto mb-4 bg-primary-500/20 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <h3 class="text-xl font-semibold mb-2">Capture Frames</h3>
        <p class="text-gray-400">
          Take a photo of any picture frame and specify its real-world dimensions in inches or centimeters.
        </p>
      </div>

      <div class="card text-center">
        <div class="w-16 h-16 mx-auto mb-4 bg-primary-500/20 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-semibold mb-2">Create 3D Models</h3>
        <p class="text-gray-400">
          Automatically generate accurate 3D models of your frames for realistic visualization.
        </p>
      </div>

      <div class="card text-center">
        <div class="w-16 h-16 mx-auto mb-4 bg-primary-500/20 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-semibold mb-2">Visualize on Walls</h3>
        <p class="text-gray-400">
          Place your framed pictures on captured walls and see how they look before committing.
        </p>
      </div>
    </div>

    <!-- How it works -->
    <div class="mt-20">
      <h2 class="text-3xl font-bold mb-12">How It Works</h2>
      <div class="grid md:grid-cols-4 gap-6">
        <div class="text-center">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-500 rounded-full flex items-center justify-center text-xl font-bold">
            1
          </div>
          <h4 class="font-semibold mb-1">Capture Frame</h4>
          <p class="text-sm text-gray-400">Photo your picture frame</p>
        </div>
        <div class="text-center">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-500 rounded-full flex items-center justify-center text-xl font-bold">
            2
          </div>
          <h4 class="font-semibold mb-1">Set Dimensions</h4>
          <p class="text-sm text-gray-400">Enter size in inches or cm</p>
        </div>
        <div class="text-center">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-500 rounded-full flex items-center justify-center text-xl font-bold">
            3
          </div>
          <h4 class="font-semibold mb-1">Capture Wall</h4>
          <p class="text-sm text-gray-400">Photo your empty wall</p>
        </div>
        <div class="text-center">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-500 rounded-full flex items-center justify-center text-xl font-bold">
            4
          </div>
          <h4 class="font-semibold mb-1">Place & Preview</h4>
          <p class="text-sm text-gray-400">Arrange frames in 3D</p>
        </div>
      </div>
    </div>
  </div>
</template>
