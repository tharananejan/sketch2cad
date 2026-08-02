import { useState } from 'react'
import { IconEye, IconEyeOff, IconLock, IconAlert } from '../icons'

/* Reusable auth fields with focus glow and inline validation. */

export function TextField({ label, icon: Icon, error, hint, hintTone = 'ok', ...rest }) {
  return (
    <div className="auth-field">
      <label className="auth-label" htmlFor={rest.id}>
        {label}
      </label>
      <div className={`auth-input-wrap ${error ? 'error' : ''} ${Icon ? 'has-icon' : ''}`}>
        {Icon && (
          <span className="auth-field-icon" aria-hidden="true">
            <Icon size={16} />
          </span>
        )}
        <input className="auth-input" aria-invalid={error ? 'true' : undefined} {...rest} />
      </div>
      {error ? (
        <p className="auth-hint err" role="alert">
          <IconAlert size={12} /> {error}
        </p>
      ) : hint ? (
        <p className={`auth-hint ${hintTone}`}>{hint}</p>
      ) : null}
    </div>
  )
}

export function PasswordField({ label, error, hint, hintTone, showToggle = true, ...rest }) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="auth-field">
      <label className="auth-label" htmlFor={rest.id}>
        {label}
      </label>
      <div className={`auth-input-wrap ${error ? 'error' : ''} has-icon`}>
        <span className="auth-field-icon" aria-hidden="true">
          <IconLock size={16} />
        </span>
        <input
          className="auth-input"
          type={visible ? 'text' : 'password'}
          aria-invalid={error ? 'true' : undefined}
          autoComplete={rest.autoComplete || 'current-password'}
          {...rest}
        />
        {showToggle && (
          <button
            type="button"
            className="auth-eye"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Hide password' : 'Show password'}
            tabIndex={-1}
          >
            {visible ? <IconEyeOff size={16} /> : <IconEye size={16} />}
          </button>
        )}
      </div>
      {error ? (
        <p className="auth-hint err" role="alert">
          <IconAlert size={12} /> {error}
        </p>
      ) : hint ? (
        <p className={`auth-hint ${hintTone}`}>{hint}</p>
      ) : null}
    </div>
  )
}

export function CheckField({ label, ...rest }) {
  return (
    <label className="auth-check">
      <input type="checkbox" {...rest} />
      <span>{label}</span>
    </label>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="auth-error" role="alert">
      <IconAlert size={15} />
      <span>{message}</span>
    </div>
  )
}

export function SuccessFlash({ title, sub }) {
  return (
    <div className="auth-success-flash" role="status">
      <span className="success-ring">
        <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m4.5 12.5 5 5L19.5 7" />
        </svg>
      </span>
      <p className="success-title">{title}</p>
      {sub && <p className="success-sub">{sub}</p>}
    </div>
  )
}
