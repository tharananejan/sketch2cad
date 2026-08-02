import { useMemo } from 'react'

/* Live password strength: 0-5 score + checklist. */

export const STRENGTH_LABELS = {
  0: { label: 'Too short', color: 'var(--faint)' },
  1: { label: 'Weak', color: '#d64541' },
  2: { label: 'Fair', color: '#e88a2a' },
  3: { label: 'Good', color: '#d9a400' },
  4: { label: 'Strong', color: '#2e9e6b' },
  5: { label: 'Excellent', color: 'var(--blueprint)' },
}

export const STRENGTH_CHECKS = [
  { key: 'length', text: 'At least 8 characters', test: (p) => p.length >= 8 },
  { key: 'upper', text: 'Uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { key: 'lower', text: 'Lowercase letter', test: (p) => /[a-z]/.test(p) },
  { key: 'number', text: 'Number', test: (p) => /\d/.test(p) },
  { key: 'special', text: 'Special character', test: (p) => /[^A-Za-z0-9]/.test(p) },
]

export function scorePassword(password) {
  const checks = STRENGTH_CHECKS.map((c) => c.test(password))
  return { score: checks.filter(Boolean).length, checks }
}

export default function PasswordStrength({ password }) {
  const { score, checks } = useMemo(() => scorePassword(password), [password])
  const active = password.length > 0
  const meta = STRENGTH_LABELS[score]

  return (
    <div className="strength" aria-live="polite">
      <div className="strength-meter" role="progressbar" aria-valuemin={0} aria-valuemax={5} aria-valuenow={active ? score : 0} aria-label="Password strength">
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={`strength-seg ${active && i <= score ? 'lit' : ''}`}
            style={active && i <= score ? { background: meta.color } : undefined}
          />
        ))}
      </div>
      <div className="strength-meta">
        <span className="strength-label" style={{ color: active ? meta.color : 'var(--faint)' }}>
          {active ? meta.label : 'Password strength'}
        </span>
        {active && <span className="strength-score mono">{score}/5</span>}
      </div>
      {active && (
        <ul className="strength-checks">
          {STRENGTH_CHECKS.map((c, i) => (
            <li key={c.key} className={checks[i] ? 'met' : ''}>
              <span className="strength-check-dot" />
              {c.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
