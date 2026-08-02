import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { getSupabase, demoMode } from '../lib/supabase'

const AuthContext = createContext(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

/* Normalize a supabase user (or demo user) into our app shape. */
function normalizeUser(raw) {
  if (!raw) return null
  return {
    id: raw.id,
    email: raw.email,
    displayName:
      raw.user_metadata?.display_name || (raw.email ? raw.email.split('@')[0] : 'Drafter'),
    emailConfirmed: Boolean(raw.email_confirmed_at),
    provider: raw.app_metadata?.provider || 'email',
  }
}

/* Map supabase error messages to friendly copy. */
export function mapAuthError(error) {
  const msg = error?.message || 'Something went wrong. Please try again.'
  if (/invalid login credentials/i.test(msg)) return 'Wrong password or email — check both and try again.'
  if (/already registered/i.test(msg)) return 'An account with this email already exists. Sign in instead.'
  if (/email not confirmed|confirm your email/i.test(msg)) return 'Verify your email first — check your inbox for the link.'
  if (/password should be at least/i.test(msg)) return 'Password must be at least 6 characters.'
  if (/network/i.test(msg)) return 'Network error — check your connection and try again.'
  if (/cancelled|popup.*closed|user.*closed/i.test(msg)) return 'Google sign-in was cancelled.'
  if (/no active session|session missing/i.test(msg)) return 'Your session expired — sign in again.'
  if (/current password is incorrect/i.test(msg)) return 'Current password is incorrect.'
  return msg
}

export default function AuthProvider({ children }) {
  const supabase = getSupabase()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [recoveryPending, setRecoveryPending] = useState(false)

  // Toast lives here so auth actions anywhere (modal, settings, dropdown) can use it.
  const [toast, setToast] = useState(null)
  const toastTimer = useRef(null)

  const showToast = useCallback((msg, opts = {}) => {
    const { duration = 2600, tone = 'ok' } = opts
    setToast({ id: Date.now(), msg, tone })
    window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToast(null), duration)
  }, [])

  // Session restore + subscribe.
  useEffect(() => {
    let sub
    ;(async () => {
      try {
        const { data } = await supabase.auth.getSession()
        setUser(normalizeUser(data?.session?.user))
      } catch {
        setUser(null)
      } finally {
        setLoading(false)
      }
    })()

    try {
      const { data } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(normalizeUser(session?.user))
      })
      sub = data?.subscription
    } catch {
      /* no-op */
    }

    // Real Supabase: a recovery link arrives as #access_token&type=recovery.
    if (!demoMode) {
      try {
        const params = new URLSearchParams(window.location.hash.slice(1))
        if (params.get('type') === 'recovery' && params.get('access_token')) {
          setRecoveryPending(true)
          // supabase-js consumes the tokens and sets the session for updateUser().
        }
      } catch {
        /* ignore */
      }
    }

    return () => sub?.unsubscribe?.()
  }, [supabase])

  const signIn = useCallback(
    async ({ email, password, remember }) => {
      const { error } = await supabase.auth.signInWithPassword({ email, password, remember })
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const signUp = useCallback(
    async ({ name, email, password }) => {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { display_name: name },
          emailRedirectTo: typeof window !== 'undefined' ? window.location.origin : undefined,
        },
      })
      if (error) throw new Error(mapAuthError(error))
      // Returns true when a session exists (email confirmation off), false when verification is required.
      return Boolean(data?.session)
    },
    [supabase],
  )

  const signInWithGoogle = useCallback(async () => {
    if (demoMode) {
      const { error } = await supabase.auth.demoGoogleSignIn()
      if (error) throw new Error(mapAuthError(error))
      return
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: typeof window !== 'undefined' ? window.location.origin : undefined },
    })
    if (error) throw new Error(mapAuthError(error))
  }, [supabase])

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
    setUser(null)
  }, [supabase])

  const sendResetLink = useCallback(
    async (email) => {
      const { error } = await supabase.auth.resetPasswordForEmail(email)
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const updatePassword = useCallback(
    async (newPassword) => {
      // Real mode: the recovery link established the session, so updateUser works.
      // Demo mode: updatePassword() on the demo adapter applies to the pending reset email.
      const { error } = await supabase.auth.updatePassword(newPassword)
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const changePassword = useCallback(
    async (current, next) => {
      if (demoMode) {
        const { error } = await supabase.auth.changePassword(current, next)
        if (error) throw new Error(mapAuthError(error))
        return true
      }
      // Real Supabase requires reauthentication to change password without a fresh login.
      const { error } = await supabase.auth.updateUser({ password: next })
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const updateProfile = useCallback(
    async ({ displayName }) => {
      if (demoMode) {
        const { error } = await supabase.auth.updateProfile({ display_name: displayName })
        if (error) throw new Error(mapAuthError(error))
        return true
      }
      // Real Supabase stores profile fields as user metadata.
      const { error } = await supabase.auth.updateUser({ data: { display_name: displayName } })
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const verifyEmail = useCallback(
    async (email) => {
      if (demoMode) {
        const { error } = await supabase.auth.verifyDemoEmail(email)
        if (error) throw new Error(mapAuthError(error))
        return true
      }
      // Real mode: sign-up confirmation links arrive by email; this mirrors
      // the resend action for the demo path and stays harmless when unused.
      const { error } = await supabase.auth.resend({ type: 'signup', email })
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const resendEmail = useCallback(
    async (type = 'signup', email) => {
      if (demoMode) {
        await supabase.auth.resendConfirmation()
        return true
      }
      // 'signup' for verification emails, 'recovery' for reset links.
      // supabase-js requires the email for resend.
      const { error } = await supabase.auth.resend({ type, email })
      if (error) throw new Error(mapAuthError(error))
      return true
    },
    [supabase],
  )

  const checkEmail = useCallback(
    async (email) => {
      try {
        if (demoMode) return await supabase.auth.checkEmail(email)
        return { status: 'available' } // real check happens at sign-up
      } catch {
        return { status: 'available' }
      }
    },
    [supabase],
  )

  const clearRecovery = useCallback(() => setRecoveryPending(false), [])

  const value = {
    user,
    loading,
    demoMode,
    isConfigured: !demoMode,
    recoveryPending,
    clearRecovery,
    showToast,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    sendResetLink,
    updatePassword,
    changePassword,
    updateProfile,
    verifyEmail,
    resendEmail,
    checkEmail,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
      {toast && (
        <div className="toast" role="status" key={toast.id} data-tone={toast.tone}>
          <span className="toast-check">{toast.tone === 'ok' ? '✓' : '!'}</span>
          {toast.msg}
        </div>
      )}
    </AuthContext.Provider>
  )
}
