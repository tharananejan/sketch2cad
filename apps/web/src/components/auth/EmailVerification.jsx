import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { IconMail, IconRefresh, IconArrowLeft, IconCheckCircle } from '../icons'

/* "Check your email" screen — shown after sign-up (verify mode) or after
   requesting a reset link (reset mode). In demo mode an inline "verify"
   link stands in for the real email. */

export default function EmailVerification({ mode, email, onNavigate, onSuccess }) {
  const { demoMode, verifyEmail, resendEmail, showToast } = useAuth()
  const [sending, setSending] = useState(false)
  const [verified, setVerified] = useState(false)

  const title = mode === 'reset' ? 'Check your email' : 'Verify your email'
  const sub =
    mode === 'reset'
      ? `We sent a reset link to ${email}. Open it to choose a new password.`
      : `We sent a confirmation link to ${email}. Click it to activate your account.`

  async function resend() {
    setSending(true)
    try {
      await resendEmail(mode === 'reset' ? 'recovery' : 'signup', email)
      showToast(demoMode ? 'Email sent (simulated).' : mode === 'reset' ? 'Reset link sent.' : 'Verification email sent.')
    } catch (err) {
      showToast(err.message, { tone: 'err' })
    } finally {
      setSending(false)
    }
  }

  async function demoVerify() {
    // Reset mode: the "email" contains a reset link — go set a new password.
    if (mode === 'reset') {
      onNavigate('reset')
      return
    }
    setVerified(true)
    try {
      await verifyEmail(email)
      showToast('Email verified — account active. Welcome!')
      // The demo adapter signs the user in on verification, so close the modal.
      window.setTimeout(() => onSuccess?.(), 900)
    } catch (err) {
      setVerified(false)
      showToast(err.message, { tone: 'err' })
    }
  }

  return (
    <div className="auth-view">
      <div className="verify-icon" aria-hidden="true">
        <IconMail size={30} />
        <span className="verify-ping" />
      </div>
      <h2 className="auth-title">{title}</h2>
      <p className="auth-sub">{sub}</p>

      <div className="verify-actions">
        <a className="verify-gmail" href="https://mail.google.com" target="_blank" rel="noreferrer">
          Open Gmail
        </a>
        <button type="button" className="verify-resend" onClick={resend} disabled={sending}>
          {sending ? (
            <span className="btn-loading">
              <span className="dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
              Resending…
            </span>
          ) : (
            <>
              <IconRefresh size={14} /> Resend Email
            </>
          )}
        </button>
      </div>

      {demoMode && (
        <button type="button" className="verify-demo" onClick={demoVerify} disabled={verified}>
          {verified ? (
            <>
              <IconCheckCircle size={14} /> Verified!
            </>
          ) : mode === 'reset' ? (
            'Use demo reset link'
          ) : (
            'Use demo verification link'
          )}
        </button>
      )}

      <button type="button" className="auth-back" onClick={() => onNavigate('login')}>
        <IconArrowLeft size={14} /> Back to Login
      </button>
    </div>
  )
}
