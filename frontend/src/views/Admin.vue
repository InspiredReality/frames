<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'
import { useWallsStore } from '@/store/walls'
import { usePicturesStore } from '@/store/pictures'
import api, { getUploadUrl } from '@/services/api'

const authStore = useAuthStore()
const wallsStore = useWallsStore()
const picturesStore = usePicturesStore()
const router = useRouter()

const users = ref([])
const loading = ref(true)
const error = ref('')
const expandedUserId = ref(null)
const userDetail = ref({})
const loadingDetail = ref(null)
const deletingId = ref(null)

const guestSessions = ref([])
const guestLoading = ref(true)
const expandedSessionId = ref(null)

onMounted(async () => {
  if (!authStore.user?.is_admin) {
    router.push('/')
    return
  }
  await Promise.all([loadUsers(), loadGuestSessions()])
})

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.get('/admin/users')
    users.value = res.data.users
  } catch (e) {
    error.value = 'Failed to load users'
  } finally {
    loading.value = false
  }
}

async function loadGuestSessions() {
  guestLoading.value = true
  try {
    const res = await api.get('/admin/guest-sessions')
    guestSessions.value = res.data.sessions
  } catch {
    guestSessions.value = []
  } finally {
    guestLoading.value = false
  }
}

async function toggleUser(userId) {
  if (expandedUserId.value === userId) {
    expandedUserId.value = null
    return
  }
  expandedUserId.value = userId
  if (userDetail.value[userId]) return
  loadingDetail.value = userId
  try {
    const res = await api.get(`/admin/users/${userId}`)
    userDetail.value[userId] = { walls: res.data.walls, frames: res.data.frames }
  } catch {
    userDetail.value[userId] = { walls: [], frames: [] }
  } finally {
    loadingDetail.value = null
  }
}

async function deleteWall(wallId, userId) {
  if (!confirm('Delete this wall? This cannot be undone.')) return
  deletingId.value = `wall-${wallId}`
  try {
    await wallsStore.deleteWall(wallId)
    if (userDetail.value[userId]) {
      userDetail.value[userId].walls = userDetail.value[userId].walls.filter(w => w.id !== wallId)
    }
    const u = users.value.find(u => u.id === userId)
    if (u) u.wall_count = Math.max(0, (u.wall_count || 1) - 1)
  } catch {
    alert('Failed to delete wall')
  } finally {
    deletingId.value = null
  }
}

async function deleteFrame(frameId, userId) {
  if (!confirm('Delete this frame? This cannot be undone.')) return
  deletingId.value = `frame-${frameId}`
  try {
    await picturesStore.deletePicture(frameId)
    if (userDetail.value[userId]) {
      userDetail.value[userId].frames = userDetail.value[userId].frames.filter(f => f.id !== frameId)
    }
    const u = users.value.find(u => u.id === userId)
    if (u) u.frame_count = Math.max(0, (u.frame_count || 1) - 1)
  } catch {
    alert('Failed to delete frame')
  } finally {
    deletingId.value = null
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
function formatDateTime(iso) {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}

const ACTION_LABELS = {
  wall_created: 'Wall created',
  frame_created: 'Frame created',
  frame_added_to_wall: 'Frame added to wall',
  frame_rearranged: 'Frame rearranged',
  layout_saved: 'Layout saved',
}

function actionLabel(action) {
  return ACTION_LABELS[action] || action
}

function shortId(sessionId) {
  return sessionId?.slice(0, 8) || '—'
}
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <h1 class="text-2xl font-bold mb-6 text-white">Admin Dashboard</h1>

    <div v-if="loading" class="text-gray-400 text-center py-12">Loading users…</div>
    <div v-else-if="error" class="text-red-400 text-center py-12">{{ error }}</div>

    <div v-else>
      <!-- Stats bar -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div class="bg-dark-200 rounded-lg p-4 text-center">
          <p class="text-3xl font-bold text-primary-400">{{ users.length }}</p>
          <p class="text-sm text-gray-400 mt-1">Registered Users</p>
        </div>
        <div class="bg-dark-200 rounded-lg p-4 text-center">
          <p class="text-3xl font-bold text-primary-400">{{ users.reduce((s, u) => s + (u.wall_count || 0), 0) }}</p>
          <p class="text-sm text-gray-400 mt-1">Total Walls</p>
        </div>
        <div class="bg-dark-200 rounded-lg p-4 text-center">
          <p class="text-3xl font-bold text-primary-400">{{ users.reduce((s, u) => s + (u.frame_count || 0), 0) }}</p>
          <p class="text-sm text-gray-400 mt-1">Total Frames</p>
        </div>
        <div class="bg-dark-200 rounded-lg p-4 text-center">
          <p class="text-3xl font-bold text-primary-400">{{ guestSessions.length }}</p>
          <p class="text-sm text-gray-400 mt-1">Guest Sessions</p>
        </div>
      </div>

      <!-- Users table -->
      <div class="bg-dark-200 rounded-lg overflow-hidden mb-8">
        <div class="px-4 py-3 border-b border-gray-700">
          <h2 class="font-semibold text-white">Users</h2>
        </div>

        <div v-for="user in users" :key="user.id" class="border-b border-gray-700 last:border-b-0">
          <!-- User row -->
          <button
            class="w-full flex items-center gap-3 px-4 py-3 hover:bg-dark-300 transition text-left"
            @click="toggleUser(user.id)"
          >
            <div class="w-9 h-9 rounded-full bg-primary-700 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {{ user.username[0].toUpperCase() }}
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-white truncate">{{ user.username }}</span>
                <span v-if="user.is_admin" class="text-xs bg-yellow-600 text-yellow-100 px-1.5 py-0.5 rounded">Admin</span>
              </div>
              <p class="text-xs text-gray-400 truncate">{{ user.email }}</p>
            </div>

            <div class="hidden sm:flex items-center gap-6 text-sm text-gray-400 flex-shrink-0">
              <div class="text-center">
                <p class="font-semibold text-white">{{ user.wall_count }}</p>
                <p class="text-xs">Walls</p>
              </div>
              <div class="text-center">
                <p class="font-semibold text-white">{{ user.frame_count }}</p>
                <p class="text-xs">Frames</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">Last login</p>
                <p class="text-xs">{{ formatDateTime(user.last_login) }}</p>
              </div>
            </div>

            <svg class="w-4 h-4 text-gray-500 flex-shrink-0 transition-transform" :class="expandedUserId === user.id ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Expanded detail -->
          <div v-if="expandedUserId === user.id" class="bg-dark-300 px-4 pb-4 pt-2">
            <div class="flex gap-4 mb-3 sm:hidden text-sm text-gray-400">
              <span>{{ user.wall_count }} walls · {{ user.frame_count }} frames</span>
              <span>· Last login: {{ formatDateTime(user.last_login) }}</span>
            </div>
            <p class="text-xs text-gray-500 mb-3">Member since {{ formatDate(user.created_at) }}</p>

            <div v-if="loadingDetail === user.id" class="text-gray-400 text-sm py-4 text-center">Loading…</div>

            <div v-else-if="userDetail[user.id]">
              <!-- Walls -->
              <div class="mb-4">
                <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Walls ({{ userDetail[user.id].walls.length }})</h3>
                <div v-if="userDetail[user.id].walls.length === 0" class="text-sm text-gray-500 italic">No walls</div>
                <div class="space-y-2">
                  <div
                    v-for="wall in userDetail[user.id].walls"
                    :key="wall.id"
                    class="flex items-center gap-3 bg-dark-200 rounded-lg p-2"
                  >
                    <img v-if="wall.thumbnail_path" :src="getUploadUrl(wall.thumbnail_path)" class="w-12 h-9 object-cover rounded flex-shrink-0" />
                    <div v-else class="w-12 h-9 bg-dark-100 rounded flex-shrink-0" :style="wall.background_color ? `background:${wall.background_color}` : ''" />
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-white truncate">{{ wall.name }}</p>
                      <p class="text-xs text-gray-400">{{ wall.is_private !== false ? 'Private' : 'Public' }} · {{ formatDate(wall.created_at) }}</p>
                    </div>
                    <button @click="deleteWall(wall.id, user.id)" :disabled="deletingId === `wall-${wall.id}`" class="text-red-400 hover:text-red-300 disabled:opacity-40 flex-shrink-0 p-1" title="Delete wall">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Frames -->
              <div>
                <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Frames ({{ userDetail[user.id].frames.length }})</h3>
                <div v-if="userDetail[user.id].frames.length === 0" class="text-sm text-gray-500 italic">No frames</div>
                <div class="space-y-2">
                  <div
                    v-for="frame in userDetail[user.id].frames"
                    :key="frame.id"
                    class="flex items-center gap-3 bg-dark-200 rounded-lg p-2"
                  >
                    <img v-if="frame.thumbnail_path" :src="getUploadUrl(frame.thumbnail_path)" class="w-12 h-9 object-cover rounded flex-shrink-0" />
                    <div v-else class="w-12 h-9 bg-dark-100 rounded flex-shrink-0" />
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-white truncate">{{ frame.name }}</p>
                      <p class="text-xs text-gray-400">{{ frame.is_private !== false ? 'Private' : 'Public' }} · {{ formatDate(frame.created_at) }}</p>
                    </div>
                    <button @click="deleteFrame(frame.id, user.id)" :disabled="deletingId === `frame-${frame.id}`" class="text-red-400 hover:text-red-300 disabled:opacity-40 flex-shrink-0 p-1" title="Delete frame">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Guest Sessions table -->
      <div class="bg-dark-200 rounded-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
          <h2 class="font-semibold text-white">Unauth Guest Sessions</h2>
          <span class="text-xs text-gray-400">{{ guestSessions.length }} session{{ guestSessions.length !== 1 ? 's' : '' }}</span>
        </div>

        <div v-if="guestLoading" class="text-gray-400 text-sm text-center py-6">Loading…</div>
        <div v-else-if="guestSessions.length === 0" class="text-gray-500 text-sm italic text-center py-6">No guest activity yet</div>

        <div v-for="session in guestSessions" :key="session.session_id" class="border-b border-gray-700 last:border-b-0">
          <!-- Session row -->
          <button
            class="w-full flex items-center gap-3 px-4 py-3 hover:bg-dark-300 transition text-left"
            @click="expandedSessionId = expandedSessionId === session.session_id ? null : session.session_id"
          >
            <!-- Avatar -->
            <div class="w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 font-bold text-sm flex-shrink-0">
              ?
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-white font-mono text-sm">unauth:{{ shortId(session.session_id) }}</span>
              </div>
              <p class="text-xs text-gray-400">
                First seen {{ formatDateTime(session.first_seen) }} · Last active {{ formatDateTime(session.last_seen) }}
              </p>
            </div>

            <!-- Event count chips -->
            <div class="hidden sm:flex items-center gap-2 flex-shrink-0 flex-wrap justify-end max-w-xs">
              <span v-if="session.event_counts.wall_created" class="text-xs bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded-full">
                {{ session.event_counts.wall_created }} wall{{ session.event_counts.wall_created !== 1 ? 's' : '' }}
              </span>
              <span v-if="session.event_counts.frame_created" class="text-xs bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded-full">
                {{ session.event_counts.frame_created }} frame{{ session.event_counts.frame_created !== 1 ? 's' : '' }}
              </span>
              <span v-if="session.event_counts.frame_added_to_wall" class="text-xs bg-green-900/60 text-green-300 px-2 py-0.5 rounded-full">
                {{ session.event_counts.frame_added_to_wall }} added
              </span>
              <span v-if="session.event_counts.frame_rearranged" class="text-xs bg-yellow-900/60 text-yellow-300 px-2 py-0.5 rounded-full">
                {{ session.event_counts.frame_rearranged }} moved
              </span>
              <span v-if="session.event_counts.layout_saved" class="text-xs bg-orange-900/60 text-orange-300 px-2 py-0.5 rounded-full">
                {{ session.event_counts.layout_saved }} layout{{ session.event_counts.layout_saved !== 1 ? 's' : '' }}
              </span>
            </div>

            <svg class="w-4 h-4 text-gray-500 flex-shrink-0 transition-transform ml-2" :class="expandedSessionId === session.session_id ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Expanded event timeline -->
          <div v-if="expandedSessionId === session.session_id" class="bg-dark-300 px-4 pb-4 pt-2">
            <p class="text-xs text-gray-500 mb-3 font-mono">Session: {{ session.session_id }}</p>

            <!-- Mobile chips -->
            <div class="flex flex-wrap gap-2 mb-3 sm:hidden">
              <span v-if="session.event_counts.wall_created" class="text-xs bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded-full">{{ session.event_counts.wall_created }} wall{{ session.event_counts.wall_created !== 1 ? 's' : '' }}</span>
              <span v-if="session.event_counts.frame_created" class="text-xs bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded-full">{{ session.event_counts.frame_created }} frame{{ session.event_counts.frame_created !== 1 ? 's' : '' }}</span>
              <span v-if="session.event_counts.frame_added_to_wall" class="text-xs bg-green-900/60 text-green-300 px-2 py-0.5 rounded-full">{{ session.event_counts.frame_added_to_wall }} added to wall</span>
              <span v-if="session.event_counts.frame_rearranged" class="text-xs bg-yellow-900/60 text-yellow-300 px-2 py-0.5 rounded-full">{{ session.event_counts.frame_rearranged }} rearranged</span>
              <span v-if="session.event_counts.layout_saved" class="text-xs bg-orange-900/60 text-orange-300 px-2 py-0.5 rounded-full">{{ session.event_counts.layout_saved }} layout{{ session.event_counts.layout_saved !== 1 ? 's' : '' }} saved</span>
            </div>

            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Activity Timeline</h3>
            <div class="space-y-1">
              <div v-for="(ev, i) in session.events" :key="i" class="flex items-start gap-3 text-sm">
                <span class="text-xs text-gray-500 flex-shrink-0 w-36">{{ formatDateTime(ev.created_at) }}</span>
                <span class="text-gray-300">{{ actionLabel(ev.action) }}</span>
                <span v-if="ev.metadata?.wall_name" class="text-gray-500 text-xs truncate">– {{ ev.metadata.wall_name }}</span>
                <span v-else-if="ev.metadata?.frame_name" class="text-gray-500 text-xs truncate">– {{ ev.metadata.frame_name }}</span>
                <span v-else-if="ev.metadata?.layout_name" class="text-gray-500 text-xs truncate">– {{ ev.metadata.layout_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
