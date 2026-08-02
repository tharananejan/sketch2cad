import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { useEmailValidation } from './ValidationHook'
import { TextField, ErrorBanner } from './fields'
import LoadingButton from './LoadingButton'
import { IconMail, IconArrowLeft } from '../icons'

export default function ForgotPasswordForm({ onNavigate, onLinkSent }) {
  const { sendResetLink, checkEmail } = useAuth()
  const email = useEmailValidation(checkEmail)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!email.hasValidFormat || busy) return
    setBusy(true)
    setError(null)
    try {
      await sendResetLink(email.value)
      onLinkSent(email.value)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth-view">
      <h2 className="auth-title">Forgot password?</h2>
      <p className="auth-sub">
        No problem — enter your email and we&rsquo;ll send you a link to reset it.
      </p>

      <form onSubmit={submit} noValidate>
        <TextField
          id="forgot-email"
          label="Email"
          icon={IconMail}
          type="email"
          placeholder="you@studio.com"
          autoComplete="email"
          value={email.value}
          onChange={(e) => email.onChange(e.target.value)}
          error={email.status === 'invalid' ? 'Enter a valid email address.' : null}
        />

        <ErrorBanner message={error} />

        <LoadingButton loading={busy} loadingText="Sending reset link…">
          Send Reset Link
        </LoadingButton>
      </form>

      <button type="button" className="auth-back" onClick={() => onNavigate('login')}>
        <IconArrowLeft size={14} /> Back to Sign In
      </button>
    </div>
  )
}
