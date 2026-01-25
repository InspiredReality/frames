import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/capture/frame',
    name: 'capture-frame',
    component: () => import('@/views/CaptureFrame.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/capture/wall',
    name: 'capture-wall',
    component: () => import('@/views/CaptureWall.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/gallery',
    name: 'gallery',
    component: () => import('@/views/Gallery.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/walls',
    name: 'saved-walls',
    component: () => import('@/views/SavedWalls.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/wall/:id',
    name: 'wall-editor',
    component: () => import('@/views/WallEditor.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ar/:wallId?',
    name: 'ar-view',
    component: () => import('@/views/ARView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for auth
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
