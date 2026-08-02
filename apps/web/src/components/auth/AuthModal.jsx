import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LogoMark, IconClose } from '../icons'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import ForgotPasswordForm from './ForgotPasswordForm'
import ResetPasswordForm from './ResetPasswordForm'
import EmailVerification from './EmailVerification'
import { useAuth } from '../../auth/AuthProvider'

const VIEWS = ['login', 'register', 'forgot', 'reset', 'verify']

export default function AuthModal({ onClose, initialView = 'login' }) {
  const { demoMode } = useAuth()
  const [view, setView] = useState(VIEWS.includes(initialView) ? initialView : 'login')
  const [verifyEmail, setVerifyEmail] = useState('')
  const [verifyMode, setVerifyMode] = useState('signup') // 'signup' | 'reset'
  const closeRef = useRef(null)

  // ESC closes; focus lands on the close button.
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    closeRef.current?.focus()
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [onClose])

  // Keep the backdrop click from closing when interacting with the card.
  return (
    <motion.div
      className="auth-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <motion.div
        className="auth-card"
        role="dialog"
        aria-modal="true"
        aria-label="Authentication"
        initial={{ opacity: 0, scale: 0.94, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ type: 'spring', stiffness: 340, damping: 28 }}
      >
        <header className="auth-head">
          <span className="auth-brand">
            <LogoMark size={24} />
            <span className="auth-brand-name">sketch2cad</span>
          </span>
          <div className="auth-head-right">
            {demoMode && <span className="auth-demo mono">demo mode</span>}
            <button
              ref={closeRef}
              type="button"
              className="auth-close"
              onClick={onClose}
              aria-label="Close"
              title="Close (Esc)"
            >
              <IconClose size={18} />
            </button>
          </div>
        </header>

        <div className="auth-body">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={view}
              className="auth-view-wrap"
              initial={{ opacity: 0, x: 26 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -26 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
            >
              {view === 'login' && (
                <LoginForm
                  onNavigate={(v) => setView(v)}
                  onSuccess={onClose}
                />
              )}
              {view === 'register' && (
                <RegisterForm
                  onNavigate={(v) => setView(v)}
                  onSuccess={onClose}
                  onRequireVerification={(email, mode) => {
                    setVerifyEmail(email)
                    setVerifyMode(mode)
                    setView('verify')
                  }}
                />
              )}
              {view === 'forgot' && (
                <ForgotPasswordForm
                  onNavigate={(v) => setView(v)}
                  onLinkSent={(email) => {
                    setVerifyEmail(email)
                    setVerifyMode('reset')
                    setView('verify')
                  }}
                />
              )}
              {view === 'reset' && (
                <ResetPasswordForm onNavigate={(v) => setView(v)} onSuccess={onClose} />
              )}
              {view === 'verify' && (
                <EmailVerification
                  mode={verifyMode}
                  email={verifyEmail}
                  onNavigate={(v) => setView(v)}
                  onSuccess={onClose}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        <footer className="auth-foot mono">
          <span>{demoMode ? 'Local demo · no cloud' : 'Secure session · Supabase Auth'}</span>
          <span className="auth-foot-dot">·</span>
          <span>Your models stay on this machine</span>
        </footer>
      </motion.div>
    </motion.div>
  )
}
