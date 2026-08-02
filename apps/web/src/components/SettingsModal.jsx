import { useEffect, useRef, useState } from 'react'
import {
  IconClose,
  LogoMark,
  IconUser,
  IconSun,
  IconMoon,
  IconRuler,
  IconDownload,
  IconCheck,
  IconChevron,
} from './icons'

const SECTIONS = [
  { id: 'profile', label: 'Profile', icon: IconUser },
  { id: 'appearance', label: 'Appearance', icon: IconSun },
  { id: 'drafting', label: 'Drafting', icon: IconRuler },
  { id: 'export', label: 'Export', icon: IconDownload },
  { id: 'about', label: 'About', icon: LogoMark },
]

const SOLVERS = [
  { value: 'Local Qwen \u00b7 4-bit', note: 'Fastest \u2014 runs on this machine' },
  { value: 'Local Qwen \u00b7 8-bit', note: 'Balanced speed and quality' },
  { value: 'API Qwen \u00b7 cloud', note: 'Sends sketches to a remote model' },
]

const EXPORTS = ['FreeCAD (.FCStd)', 'STEP (.step)', 'STL (.stl)', 'All three']

const UNITS = [
  { value: 'Millimetres', note: 'mm \u2014 everything stays parametric' },
  { value: 'Inches', note: 'in \u2014 for imperial-first shops' },
]

function initials(name) {
  return name
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || '?'
}

export default function SettingsModal({
  theme,
  onToggleTheme,
  profile,
  onProfileChange,
  prefs,
  onPrefsChange,
  onClose,
}) {
  const [section, setSection] = useState('profile')
  const [draft, setDraft] = useState({ name: profile.name, email: profile.email })
  const [saved, setSaved] = useState(false)
  const [clearing, setClearing] = useState(false)
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

  function saveProfile() {
    const name = draft.name.trim()
    const email = draft.email.trim()
    if (!name || !email) return
    onProfileChange({ name, email })
    setSaved(true)
    window.setTimeout(() => setSaved(false), 2200)
  }

  function eraseAll() {
    try {
      ;['s2c-theme', 's2c-profile', 's2c-prefs'].forEach((k) => window.localStorage.removeItem(k))
    } catch {
      /* storage unavailable */
    }
    window.location.reload()
  }

  const AppIcon = SECTIONS.find((s) => s.id === section).icon

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
          <div className="settings-head-title">
            <span className="eyebrow mono">Workspace</span>
            <h1 className="settings-title">Settings</h1>
          </div>
          <button ref={closeRef} type="button" className="close-btn" onClick={onClose} aria-label="Close settings">
            <IconClose size={18} />
          </button>
        </header>

        <div className="settings-shell">
          <nav className="settings-nav" aria-label="Settings sections">
            {SECTIONS.map((s) => {
              const Icon = s.icon
              return (
                <button
                  type="button"
                  key={s.id}
                  className={`settings-nav-item ${section === s.id ? 'active' : ''}`}
                  aria-current={section === s.id ? 'page' : undefined}
                  onClick={() => setSection(s.id)}
                >
                  <Icon size={16} />
                  {s.label}
                </button>
              )
            })}
          </nav>

          <div className="settings-panel">
            <div className="settings-panel-head">
              <span className="settings-panel-icon"><AppIcon size={20} /></span>
              <div>
                <h2 className="settings-panel-title">{SECTIONS.find((s) => s.id === section).label}</h2>
                <p className="settings-panel-sub">
                  {section === 'profile' && 'Your name on the desk \u2014 shown in the sidebar and chat.'}
                  {section === 'appearance' && 'How the desk looks, in light or dark.'}
                  {section === 'drafting' && 'Units and the model that turns words into parts.'}
                  {section === 'export' && 'What you get when a part is finished.'}
                  {section === 'about' && 'sketch2cad \u2014 local-first, no cloud.'}
                </p>
              </div>
            </div>

            {section === 'profile' && (
              <div className="settings-section">
                <div className="profile-edit-head">
                  <span className="avatar avatar-edit">{initials(draft.name)}</span>
                  <div>
                    <p className="settings-label">{draft.name.trim() || 'Unnamed drafter'}</p>
                    <p className="settings-note mono">{draft.email.trim() || 'no email yet'}</p>
                  </div>
                </div>
                <div className="settings-table">
                  <div className="settings-row">
                    <div className="settings-cell">
                      <label className="settings-label" htmlFor="s2c-name">Display name</label>
                      <p className="settings-note">How you appear to yourself \u2014 used on the desk badge.</p>
                    </div>
                    <div className="settings-cell right">
                      <input
                        id="s2c-name"
                        className="settings-input"
                        value={draft.name}
                        onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                        placeholder="Ari R."
                      />
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell">
                      <label className="settings-label" htmlFor="s2c-email">Email</label>
                      <p className="settings-note">Where export notifications land. Never leaves your machine.</p>
                    </div>
                    <div className="settings-cell right">
                      <input
                        id="s2c-email"
                        className="settings-input"
                        type="email"
                        value={draft.email}
                        onChange={(e) => setDraft((d) => ({ ...d, email: e.target.value }))}
                        placeholder="ari@studio.local"
                      />
                    </div>
                  </div>
                </div>
                <div className="settings-actions">
                  <button
                    type="button"
                    className={`save-btn ${saved ? 'saved' : ''}`}
                    onClick={saveProfile}
                    disabled={!draft.name.trim() || !draft.email.trim()}
                  >
                    {saved ? <IconCheck size={15} /> : null}
                    {saved ? 'Saved' : 'Save changes'}
                  </button>
                  {saved && <span className="saved-note">Profile updated everywhere.</span>}
                </div>
              </div>
            )}

            {section === 'appearance' && (
              <div className="settings-section">
                <div className="settings-table">
                  <div className="settings-row">
                    <div className="settings-cell">
                      <p className="settings-label">Theme</p>
                      <p className="settings-note">Flip it any time from the top bar too.</p>
                    </div>
                    <div className="settings-cell right">
                      <div className="segmented" role="radiogroup" aria-label="Theme">
                        <button
                          type="button"
                          role="radio"
                          aria-checked={theme === 'dark'}
                          className={`segment ${theme === 'dark' ? 'active' : ''}`}
                          onClick={() => theme !== 'dark' && onToggleTheme()}
                        >
                          <IconMoon size={14} /> Dark
                        </button>
                        <button
                          type="button"
                          role="radio"
                          aria-checked={theme === 'light'}
                          className={`segment ${theme === 'light' ? 'active' : ''}`}
                          onClick={() => theme !== 'light' && onToggleTheme()}
                        >
                          <IconSun size={14} /> Light
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {section === 'drafting' && (
              <div className="settings-section">
                <div className="settings-table">
                  <div className="settings-row">
                    <div className="settings-cell">
                      <label className="settings-label" htmlFor="s2c-units">Units</label>
                      <p className="settings-note">New sketches start in these units.</p>
                    </div>
                    <div className="settings-cell right">
                      <span className="select-wrap">
                        <select
                          id="s2c-units"
                          className="settings-select"
                          value={prefs.units}
                          onChange={(e) => onPrefsChange({ ...prefs, units: e.target.value })}
                        >
                          {UNITS.map((u) => (
                            <option key={u.value} value={u.value}>{u.value}</option>
                          ))}
                        </select>
                        <IconChevron size={13} />
                      </span>
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell">
                      <label className="settings-label" htmlFor="s2c-solver">Model</label>
                      <p className="settings-note">The engine that turns your words into parts.</p>
                    </div>
                    <div className="settings-cell right">
                      <span className="select-wrap">
                        <select
                          id="s2c-solver"
                          className="settings-select"
                          value={prefs.solver}
                          onChange={(e) => onPrefsChange({ ...prefs, solver: e.target.value })}
                        >
                          {SOLVERS.map((s) => (
                            <option key={s.value} value={s.value}>{s.value}</option>
                          ))}
                        </select>
                        <IconChevron size={13} />
                      </span>
                    </div>
                  </div>
                </div>
                <p className="settings-solver-note">
                  {SOLVERS.find((s) => s.value === prefs.solver)?.note}
                </p>
              </div>
            )}

            {section === 'export' && (
              <div className="settings-section">
                <div className="settings-table">
                  <div className="settings-row">
                    <div className="settings-cell">
                      <label className="settings-label" htmlFor="s2c-export">Default export</label>
                      <p className="settings-note">What you get when a model is finished.</p>
                    </div>
                    <div className="settings-cell right">
                      <span className="select-wrap">
                        <select
                          id="s2c-export"
                          className="settings-select"
                          value={prefs.export}
                          onChange={(e) => onPrefsChange({ ...prefs, export: e.target.value })}
                        >
                          {EXPORTS.map((x) => (
                            <option key={x} value={x}>{x}</option>
                          ))}
                        </select>
                        <IconChevron size={13} />
                      </span>
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell">
                      <p className="settings-label">Also export STEP</p>
                      <p className="settings-note">Interchange format, kept up to date.</p>
                    </div>
                    <div className="settings-cell right">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={prefs.alsoStep}
                        className={`switch ${prefs.alsoStep ? 'on' : ''}`}
                        onClick={() => onPrefsChange({ ...prefs, alsoStep: !prefs.alsoStep })}
                        aria-label="Also export STEP"
                      >
                        <span className="switch-knob" />
                      </button>
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell">
                      <p className="settings-label">Also export STL</p>
                      <p className="settings-note">Mesh for printing and slicing.</p>
                    </div>
                    <div className="settings-cell right">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={prefs.alsoStl}
                        className={`switch ${prefs.alsoStl ? 'on' : ''}`}
                        onClick={() => onPrefsChange({ ...prefs, alsoStl: !prefs.alsoStl })}
                        aria-label="Also export STL"
                      >
                        <span className="switch-knob" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {section === 'about' && (
              <div className="settings-section">
                <div className="about-card">
                  <div className="about-logo">
                    <LogoMark size={40} />
                  </div>
                  <div className="about-copy">
                    <p className="settings-label">sketch2cad \u2014 The Drafting Desk</p>
                    <p className="settings-note">
                      Turn hand sketches and plain words into dimensioned, editable FreeCAD models.
                      Everything runs locally \u2014 your parts never leave this machine.
                    </p>
                  </div>
                </div>
                <div className="settings-table">
                  <div className="settings-row">
                    <div className="settings-cell"><p className="settings-label">Version</p></div>
                    <div className="settings-cell right"><span className="settings-value mono">v0.1.0</span></div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell"><p className="settings-label">Storage</p></div>
                    <div className="settings-cell right"><span className="settings-value mono">Local \u00b7 this machine</span></div>
                  </div>
                  <div className="settings-row">
                    <div className="settings-cell"><p className="settings-label">Privacy</p></div>
                    <div className="settings-cell right"><span className="settings-value mono">No cloud \u00b7 no telemetry</span></div>
                  </div>
                </div>
                <div className="settings-actions">
                  <button
                    type="button"
                    className={`danger-btn ${clearing ? 'armed' : ''}`}
                    onClick={() => {
                      if (clearing) eraseAll()
                      else setClearing(true)
                    }}
                  >
                    {clearing ? 'Really erase everything?' : 'Erase all local data'}
                  </button>
                  <p className="settings-solver-note">
                    {clearing
                      ? 'Projects, chats and preferences will be wiped from this browser. Click again to confirm.'
                      : 'Deletes every project, chat and preference stored in this browser.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <footer className="settings-about mono">
          <LogoMark size={16} /> sketch2cad v0.1.0 &middot; local-first &middot; no cloud
        </footer>
      </div>
    </div>
  )
}
