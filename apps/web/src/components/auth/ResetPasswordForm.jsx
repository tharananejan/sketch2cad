import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { PasswordField, ErrorBanner, SuccessFlash } from './fields'
import LoadingButton from './LoadingButton'
import PasswordStrength from './PasswordStrength'
import { IconArrowLeft } from '../icons'

export default function ResetPasswordForm({ onNavigate, onSuccess }) {
  const { updatePassword, showToast } = useAuth()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const confirmError = confirm && confirm !== password ? 'Passwords do not match.' : null
  const canSubmit = password.length >= 8 && confirm === password && !busy

  async function submit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      await updatePassword(password)
      setDone(true)
      showToast('Password updated — you\u2019re signed in with the new one.')
      // Recovery sessions are live in both modes, so close the modal.
      window.setTimeout(() => onSuccess?.(), 1900)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="auth-view">
        <SuccessFlash title="Password updated" sub="You can now sign in with your new password." />
      </div>
    )
  }

  return (
    <div className="auth-view">
      <h2 className="auth-title">Set a new password</h2>
      <p className="auth-sub">Choose a strong password you haven&rsquo;t used before.</p>

      <form onSubmit={submit} noValidate>
        <PasswordField
          id="reset-password"
          label="New password"
          placeholder="Create a strong password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
        <PasswordStrength password={password} />

        <PasswordField
          id="reset-confirm"
          label="Confirm password"
          placeholder="Repeat your new password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={confirmError}
          autoComplete="new-password"
        />

        <ErrorBanner message={error} />

        <LoadingButton loading={busy} loadingText="Securing your account…">
          Update Password
        </LoadingButton>
      </form>

      <button type="button" className="auth-back" onClick={() => onNavigate('login')}>
        <IconArrowLeft size={14} /> Back to Sign In
      </button>
    </div>
  )
}
