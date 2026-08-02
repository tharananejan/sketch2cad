import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { useEmailValidation } from './ValidationHook'
import { TextField, PasswordField, CheckField, ErrorBanner } from './fields'
import LoadingButton from './LoadingButton'
import GoogleButton from './GoogleButton'
import PasswordStrength from './PasswordStrength'
import { IconUser, IconMail } from '../icons'

export default function RegisterForm({ onNavigate, onSuccess, onRequireVerification }) {
  const { signUp, signInWithGoogle, checkEmail, demoMode, showToast } = useAuth()
  const [name, setName] = useState('')
  const [confirm, setConfirm] = useState('')
  const [agree, setAgree] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [googleBusy, setGoogleBusy] = useState(false)
  const email = useEmailValidation(checkEmail)
  const [password, setPassword] = useState('')

  const emailError =
    email.status === 'invalid'
      ? 'Enter a valid email address.'
      : email.status === 'exists'
        ? 'An account with this email already exists.'
        : null
  const emailHint =
    email.status === 'available' ? { text: 'Available — this email is free to use.', tone: 'ok' } : null
  const confirmError = confirm && confirm !== password ? 'Passwords do not match.' : null

  const canSubmit =
    name.trim().length >= 2 &&
    email.isValid &&
    password.length >= 8 &&
    confirm === password &&
    agree &&
    !busy

  async function submit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      const hasSession = await signUp({ name: name.trim(), email: email.value, password })
      if (hasSession) {
        showToast('Account created — welcome to the desk.')
        onSuccess()
      } else {
        onRequireVerification(email.value, 'signup')
      }
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
      showToast(demoMode ? 'Account created with Google (demo).' : 'Signed in with Google.')
      onSuccess()
    } catch (err) {
      setError(err.message)
      setGoogleBusy(false)
    }
  }

  return (
    <div className="auth-view">
      <h2 className="auth-title">Create your account</h2>
      <p className="auth-sub">Set up your drafting desk in under a minute.</p>

      <form onSubmit={submit} noValidate>
        <TextField
          id="reg-name"
          label="Display name"
          icon={IconUser}
          placeholder="Ari R."
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={name && name.trim().length < 2 ? 'Name needs at least 2 characters.' : null}
        />

        <TextField
          id="reg-email"
          label="Email"
          icon={IconMail}
          type="email"
          placeholder="you@studio.com"
          autoComplete="email"
          value={email.value}
          onChange={(e) => email.onChange(e.target.value)}
          error={emailError}
          hint={emailHint?.text}
          hintTone={emailHint?.tone}
        />

        <PasswordField
          id="reg-password"
          label="Password"
          placeholder="Create a strong password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
        <PasswordStrength password={password} />

        <PasswordField
          id="reg-confirm"
          label="Confirm password"
          placeholder="Repeat your password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={confirmError}
          autoComplete="new-password"
        />

        <div className="auth-terms">
          <CheckField
            label={
              <>
                I agree to the{' '}
                <a href="#terms" onClick={(e) => e.preventDefault()}>
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#privacy" onClick={(e) => e.preventDefault()}>
                  Privacy Policy
                </a>
                .
              </>
            }
            checked={agree}
            onChange={(e) => setAgree(e.target.checked)}
          />
        </div>

        <ErrorBanner message={error} />

        <LoadingButton loading={busy} loadingText="Creating your workspace…">
          Create Account
        </LoadingButton>
      </form>

      <div className="auth-divider">
        <span>OR</span>
      </div>

      <GoogleButton onClick={google} loading={googleBusy} label="Continue with Google" />

      <p className="auth-switch">
        Already have an account?{' '}
        <button type="button" className="auth-link" onClick={() => onNavigate('login')}>
          Sign In
        </button>
      </p>
    </div>
  )
}
