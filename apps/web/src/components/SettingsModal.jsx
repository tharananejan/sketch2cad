import { useEffect, useRef } from 'react'
import { IconClose, LogoMark } from './icons'

const ROWS = [
  {
    label: 'Default export',
    value: 'FreeCAD (.FCStd)',
    note: 'What you get when a model is finished',
  },
  {
    label: 'Also export',
    value: 'STEP, STL',
    note: 'Toggled per chat, off by default',
  },
  {
    label: 'Units',
    value: 'Millimetres',
    note: 'Everything stays parametric in mm',
  },
  {
    label: 'Solver',
    value: 'Local Qwen \u00b7 4-bit',
    note: 'Runs on this machine, nothing leaves it',
  },
]

export default function SettingsModal({ theme, onClose }) {
  const closeRef = useRef(null)

  useEffect(() => {
    const opener = document.activeElement
    closeRef.current?.focus()
    return () => {
      if (opener && typeof opener.focus === 'function' && opener.closest('.profile-menu.show')) {
        opener.focus()
      } else {
        document.querySelector('.profile-btn')?.focus()
      }
    }
  }, [])

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="settings-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="settings-modal-head">
          <div>
            <span className="eyebrow mono">Workspace</span>
            <h1 className="settings-title">Settings</h1>
          </div>
          <button ref={closeRef} type="button" className="close-btn" onClick={onClose} aria-label="Close settings">
            <IconClose size={18} />
          </button>
        </header>

        <div className="settings-modal-body">
          <p className="settings-sub">Preferences for how sketch2cad drafts and exports your models.</p>

          <div className="settings-table">
            {ROWS.map((r) => (
              <div className="settings-row" key={r.label}>
                <div className="settings-cell">
                  <p className="settings-label">{r.label}</p>
                  <p className="settings-note">{r.note}</p>
                </div>
                <div className="settings-cell right">
                  <span className="settings-value mono">{r.value}</span>
                </div>
              </div>
            ))}
            <div className="settings-row">
              <div className="settings-cell">
                <p className="settings-label">Appearance</p>
                <p className="settings-note">Flip it any time from the top bar</p>
              </div>
              <div className="settings-cell right">
                <span className="settings-value mono">{theme === 'dark' ? 'Dark' : 'Light'}</span>
              </div>
            </div>
          </div>
        </div>

        <footer className="settings-about mono">
          <LogoMark size={16} /> sketch2cad v0.1.0 &middot; local-first &middot; no cloud
        </footer>
      </div>
    </div>
  )
}
