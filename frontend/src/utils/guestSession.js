import api from '@/services/api'

const STORAGE_KEY = 'frames_guest_session_id'

function getSessionId() {
  let id = localStorage.getItem(STORAGE_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(STORAGE_KEY, id)
  }
  return id
}

/**
 * Log an activity event for unauthenticated users.
 * Pass isAuthenticated from the auth store to skip logging for real users.
 * Silently swallows all errors — never interrupts the caller.
 */
export async function logGuestEvent(isAuthenticated, action, metadata = {}) {
  if (isAuthenticated) return
  try {
    await api.post('/guest-events', {
      session_id: getSessionId(),
      action,
      metadata,
    })
  } catch {
    // intentionally ignored
  }
}
