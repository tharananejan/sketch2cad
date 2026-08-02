import { createClient } from '@supabase/supabase-js'

/* ============================================================
   Supabase auth layer for sketch2cad.

   Two modes:
   - REAL  — set VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY in
     apps/web/.env to use the actual Supabase Auth service
     (email, Google OAuth, magic reset links, persistent sessions).
   - DEMO  — no env vars configured yet: a local adapter that
     mirrors the supabase-js API surface, backed by the browser's
     storage, so the full premium auth flow works end-to-end today.
     It is clearly a demo: passwords are obfuscated only, never
     leave the machine, and "emails" are simulated.
   ============================================================ */

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const isSupabaseConfigured = Boolean(url && anonKey)
export const demoMode = !isSupabaseConfigured

const USERS_KEY = 's2c-demo-users'
const SESSION_KEY = 's2c-demo-session'

const delay = (ms) => new Promise((r) => setTimeout(r, ms))
const uid = () =>
  (crypto?.randomUUID?.() ||
    Math.random().toString(36).slice(2) + Date.now().toString(36))

/* ---------------- demo storage ---------------- */

const listeners = new Set()
let pendingResetEmail = null

function emit(event, session) {
  listeners.forEach((cb) => {
    try {
      cb(event, session)
    } catch {
      /* a subscriber threw — ignore */
    }
  })
}

function loadUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY)) || []
  } catch {
    return []
  }
}

function saveUsers(users) {
  try {
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
  } catch {
    /* storage unavailable */
  }
}

function loadSession() {
  for (const store of [localStorage, sessionStorage]) {
    try {
      const raw = store.getItem(SESSION_KEY)
      if (raw) return { session: JSON.parse(raw), remember: store === localStorage }
    } catch {
      /* corrupt entry — skip */
    }
  }
  return { session: null, remember: false }
}

function saveSession(session, remember) {
  try {
    ;[localStorage, sessionStorage].forEach((s) => s.removeItem(SESSION_KEY))
    ;(remember ? localStorage : sessionStorage).setItem(SESSION_KEY, JSON.stringify(session))
  } catch {
    /* storage unavailable */
  }
}

function clearSession() {
  try {
    ;[localStorage, sessionStorage].forEach((s) => s.removeItem(SESSION_KEY))
  } catch {
    /* storage unavailable */
  }
}

// Demo-only obfuscation — NOT real security. Replace with real Supabase for production.
function hashPassword(pw) {
  try {
    return 's2c$' + btoa(unescape(encodeURIComponent('sketch2cad:' + pw)))
  } catch {
    return 's2c$' + pw
  }
}

function toSession(user, remember) {
  return {
    access_token: 'demo-' + Math.random().toString(36).slice(2) + Date.now().toString(36),
    expires_at: Date.now() + 1000 * 60 * 60 * 24 * 30,
    user: {
      id: user.id,
      email: user.email,
      user_metadata: { display_name: user.displayName },
      app_metadata: { provider: user.provider || 'email' },
      email_confirmed_at: user.emailConfirmed ? new Date().toISOString() : null,
    },
  }
}

/* ---------------- demo auth client ----------------
   Mirrors the subset of supabase-js auth we use.        */

export const demoAuth = {
  async getSession() {
    await delay(60)
    const { session } = loadSession()
    return { data: { session }, error: null }
  },

  onAuthStateChange(cb) {
    listeners.add(cb)
    const { session } = loadSession()
    if (session) cb('INITIAL_SESSION', session)
    return {
      data: {
        subscription: {
          unsubscribe() {
            listeners.delete(cb)
          },
        },
      },
    }
  },

  async signUp({ email, password, options }) {
    await delay(750)
    const norm = String(email || '').trim().toLowerCase()
    if (loadUsers().some((u) => u.email === norm)) {
      return { data: { user: null, session: null }, error: { message: 'User already registered' } }
    }
    const user = {
      id: uid(),
      email: norm,
      passwordHash: hashPassword(password),
      displayName: options?.data?.display_name || norm.split('@')[0],
      emailConfirmed: false,
      provider: 'email',
      createdAt: Date.now(),
    }
    saveUsers([...loadUsers(), user])
    return {
      data: {
        user: {
          id: user.id,
          email: user.email,
          user_metadata: { display_name: user.displayName },
          app_metadata: { provider: 'email' },
        },
        session: null,
      },
      error: null,
    }
  },

  async signInWithPassword({ email, password, remember }) {
    await delay(650)
    const user = loadUsers().find((u) => u.email === String(email || '').trim().toLowerCase())
    if (!user || user.passwordHash !== hashPassword(password)) {
      return { data: { session: null }, error: { message: 'Invalid login credentials' } }
    }
    if (!user.emailConfirmed) {
      return { data: { session: null }, error: { message: 'Email not confirmed' } }
    }
    const session = toSession(user, remember)
    saveSession(session, Boolean(remember))
    emit('SIGNED_IN', session)
    return { data: { session }, error: null }
  },

  // Demo Google: signs in as a fixed demo Google account.
  async demoGoogleSignIn() {
    await delay(950)
    let user = loadUsers().find((u) => u.provider === 'google')
    if (!user) {
      user = {
        id: uid(),
        email: 'drafter.google@gmail.com',
        passwordHash: '',
        displayName: 'Ari Drafter',
        emailConfirmed: true,
        provider: 'google',
        createdAt: Date.now(),
      }
      saveUsers([...loadUsers(), user])
    }
    const session = toSession(user, true)
    saveSession(session, true)
    emit('SIGNED_IN', session)
    return { data: { session }, error: null }
  },

  async signOut() {
    await delay(140)
    clearSession()
    emit('SIGNED_OUT', null)
    return { error: null }
  },

  async resetPasswordForEmail(email) {
    await delay(650)
    pendingResetEmail = String(email || '').trim().toLowerCase()
    return { data: {}, error: null }
  },

  async updatePassword(newPassword) {
    await delay(650)
    const { session } = loadSession()
    const email = pendingResetEmail || session?.user?.email
    const users = loadUsers()
    const user = users.find((u) => u.email === email)
    if (!user) return { data: null, error: { message: 'Account not found' } }
    user.passwordHash = hashPassword(newPassword)
    saveUsers(users)
    pendingResetEmail = null
    const s = toSession(user, true)
    saveSession(s, true)
    emit('SIGNED_IN', s)
    return { data: { user: s.user }, error: null }
  },

  async changePassword(current, next) {
    await delay(650)
    const { session } = loadSession()
    const user = loadUsers().find((u) => u.id === session?.user?.id)
    if (!user) return { data: null, error: { message: 'No active session' } }
    if (user.passwordHash !== hashPassword(current)) {
      return { data: null, error: { message: 'Current password is incorrect' } }
    }
    const users = loadUsers()
    const idx = users.findIndex((u) => u.id === user.id)
    users[idx] = { ...user, passwordHash: hashPassword(next) }
    saveUsers(users)
    return { data: { user: { id: user.id } }, error: null }
  },

  async updateProfile({ display_name }) {
    await delay(420)
    const { session } = loadSession()
    const users = loadUsers()
    const user = users.find((u) => u.id === session?.user?.id)
    if (!user) return { data: null, error: { message: 'No active session' } }
    user.displayName = display_name
    saveUsers(users)
    const s = {
      ...session,
      user: { ...session.user, user_metadata: { ...session.user.user_metadata, display_name } },
    }
    saveSession(s, true)
    emit('USER_UPDATED', s)
    return { data: { user: s.user }, error: null }
  },

  async verifyDemoEmail(email) {
    await delay(500)
    const users = loadUsers()
    const user = users.find((u) => u.email === String(email || '').trim().toLowerCase())
    if (!user) return { data: null, error: { message: 'Account not found' } }
    user.emailConfirmed = true
    saveUsers(users)
    const session = toSession(user, true)
    saveSession(session, true)
    emit('SIGNED_IN', session)
    return { data: { session }, error: null }
  },

  async resendConfirmation() {
    await delay(500)
    return { data: {}, error: null }
  },

  async checkEmail(email) {
    await delay(140)
    const exists = loadUsers().some((u) => u.email === String(email || '').trim().toLowerCase())
    return { status: exists ? 'exists' : 'available' }
  },
}

/* ---------------- client factory ----------------
   Both clients are module-level singletons so callers can rely on a
   stable reference (AuthProvider keys effects off it).               */

let realClient = null
const demoClient = { auth: demoAuth }

export function getSupabase() {
  if (isSupabaseConfigured) {
    if (!realClient) {
      realClient = createClient(url, anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
          storageKey: 's2c-auth',
        },
      })
    }
    return realClient
  }
  return demoClient
}
