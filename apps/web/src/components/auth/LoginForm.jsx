import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { useEmailValidation } from './ValidationHook'
import { TextField, PasswordField, CheckField, ErrorBanner } from './fields'
import LoadingButton from './LoadingButton'
import GoogleButton from './GoogleButton'
import { IconMail } from '../icons'

export default function LoginForm({ onNavigate, onSuccess }) {
  const { signIn, signInWithGoogle, checkEmail, demoMode, showToast } = useAuth()
  const email = useEmailValidation(checkEmail)
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [googleBusy, setGoogleBusy] = useState(false)

  const canSubmit = email.hasValidFormat && password.length >= 1 && !busy

  async function submit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      await signIn({ email: email.value, password, remember })
      showToast('Signed in — welcome back.')
      onSuccess()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  async function google() {
    setGoogleBusy(true)
    setError(null)
    try {
      await signInWithGoogle()
      showToast(demoMode ? 'Signed in with Google (demo).' : 'Signed in with Google.')
      onSuccess()
    } catch (err) {
      setError(err.message)
      setGoogleBusy(false)
    }
  }

  return (
    <div className="auth-view">
      <h2 className="auth-title">Welcome back</h2>
      <p className="auth-sub">Sign in to continue designing with AI.</p>

      <form onSubmit={submit} noValidate>
        <TextField
          id="login-email"
          label="Email"
          icon={IconMail}
          type="email"
          placeholder="you@studio.com"
          autoComplete="email"
          value={email.value}
          onChange={(e) => email.onChange(e.target.value)}
          error={email.status === 'invalid' ? 'Enter a valid email address.' : null}
        />

        <PasswordField
          id="login-password"
          label="Password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <div className="auth-row">
          <CheckField
            label="Remember me"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
          />
          <button type="button" className="auth-link" onClick={() => onNavigate('forgot')}>
            Forgot password?
          </button>
        </div>

        <ErrorBanner message={error} />

        <LoadingButton loading={busy} loadingText="Signing you in…">
          Sign In
        </LoadingButton>
      </form>

      <div className="auth-divider">
        <span>OR</span>
      </div>

      <GoogleButton onClick={google} loading={googleBusy} />

      <p className="auth-switch">
        Don&rsquo;t have an account?{' '}
        <button type="button" className="auth-link" onClick={() => onNavigate('register')}>
          Create Account
        </button>
      </p>
    </div>
  )
}
