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
  IconKey,
  IconShield,
  IconLogout,
} from './icons'
import { PasswordField, ErrorBanner, SuccessFlash } from './auth/fields'
import PasswordStrength from './auth/PasswordStrength'
import LoadingButton from './auth/LoadingButton'
import initials from '../lib/initials'

const SECTIONS = [
  { id: 'profile', label: 'Profile', icon: IconUser },
  { id: 'account', label: 'Account', icon: IconKey },
  { id: 'security', label: 'Security', icon: IconShield },
  { id: 'appearance', label: 'Appearance', icon: IconSun },
  { id: 'drafting', label: 'Drafting', icon: IconRuler },
  { id: 'export', label: 'Export', icon: IconDownload },
  { id: 'about', label: 'About', icon: LogoMark },
  { id: 'danger', label: 'Danger Zone', icon: IconLogout },
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


export default function SettingsModal({
  theme,
  onToggleTheme,
  profile,
  signedIn = false,
  onProfileChange,
  onChangePassword,
  onLogout,
  prefs,
  onPrefsChange,
  onClose,
}) {
  const [section, setSection] = useState('profile')
  const [draft, setDraft] = useState({ name: profile.name, email: profile.email })
  const [saved, setSaved] = useState(false)
  const [clearing, setClearing] = useState(false)
  // Security section
  const [secCurrent, setSecCurrent] = useState('')
  const [secNew, setSecNew] = useState('')
  const [secConfirm, setSecConfirm] = useState('')
  const [secBusy, setSecBusy] = useState(false)
  const [secError, setSecError] = useState(null)
  const [secDone, setSecDone] = useState(false)
  const [logoutArmed, setLogoutArmed] = useState(false)
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

  async function saveSecurity(e) {
    e.preventDefault()
    if (!secCurrent || secNew.length < 8 || secNew !== secConfirm || secBusy) return
    setSecBusy(true)
    setSecError(null)
    setSecDone(false)
    try {
      await onChangePassword(secCurrent, secNew)
      setSecDone(true)
      setSecCurrent('')
      setSecNew('')
      setSecConfirm('')
      window.setTimeout(() => setSecDone(false), 2600)
    } catch (err) {
      setSecError(err.message || 'Could not change password.')
    } finally {
      setSecBusy(false)
    }
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
          <div className="settings-head-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button ref={closeRef} type="button" className="close-btn" onClick={onClose} aria-label="Close settings">
              <IconClose size={18} />
            </button>
          </div>
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
                  {section === 'account' && 'Your sign-in identity and how you connect.'}
                  {section === 'security' && 'Keep your account safe with a strong password.'}
                  {section === 'appearance' && 'How the desk looks, in light or dark.'}
                  {section === 'drafting' && 'Units and the model that turns words into parts.'}
                  {section === 'export' && 'What you get when a part is finished.'}
                  {section === 'about' && 'sketch2cad \u2014 local-first, no cloud.'}
                  {section === 'danger' && 'Sign out of sketch2cad on this device.'}
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
                      <p className="settings-note">
                        {signedIn
                          ? 'Managed by your account \u2014 cannot be changed here.'
                          : 'Where export notifications land. Never leaves your machine.'}
                      </p>
                    </div>
                    <div className="settings-cell right">
                      <input
                        id="s2c-email"
                        className="settings-input"
                        type="email"
                        value={draft.email}
                        readOnly={signedIn}
                        disabled={signedIn}
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

            {section === 'account' && (
              <div className="settings-section">
                {signedIn ? (
                  <>
                    <div className="settings-table">
                      <div className="settings-row">
                        <div className="settings-cell">
                          <p className="settings-label">Account email</p>
                          <p className="settings-note">Used for sign-in and verification.</p>
                        </div>
                        <div className="settings-cell right">
                          <span className="settings-value mono">{profile.email}</span>
                        </div>
                      </div>
                      <div className="settings-row">
                        <div className="settings-cell">
                          <p className="settings-label">Sign-in method</p>
                          <p className="settings-note">How you authenticate to sketch2cad.</p>
                        </div>
                        <div className="settings-cell right">
                          <span className="settings-value mono">Email / Google</span>
                        </div>
                      </div>
                    </div>
                    <p className="settings-solver-note">
                      Change your display name from the Profile tab. Manage your password under Security.
                    </p>
                  </>
                ) : (
                  <div className="settings-table">
                    <div className="settings-row">
                      <div className="settings-cell">
                        <p className="settings-label">Not signed in</p>
                        <p className="settings-note">
                          Account features \u2014 synced display name, password recovery and verification \u2014 need a sign-in.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {section === 'security' && (
              <div className="settings-section">
                {signedIn ? (
                  <form onSubmit={saveSecurity}>
                    <div className="security-fields">
                      <PasswordField
                        id="s2c-sec-current"
                        label="Current password"
                        placeholder="Your current password"
                        value={secCurrent}
                        onChange={(e) => setSecCurrent(e.target.value)}
                        autoComplete="current-password"
                      />
                      <PasswordField
                        id="s2c-sec-new"
                        label="New password"
                        placeholder="Create a strong password"
                        value={secNew}
                        onChange={(e) => setSecNew(e.target.value)}
                        autoComplete="new-password"
                      />
                      <PasswordStrength password={secNew} />
                      <PasswordField
                        id="s2c-sec-confirm"
                        label="Confirm new password"
                        placeholder="Repeat your new password"
                        value={secConfirm}
                        onChange={(e) => setSecConfirm(e.target.value)}
                        error={secConfirm && secConfirm !== secNew ? 'Passwords do not match.' : null}
                        autoComplete="new-password"
                      />
                    </div>
                    <ErrorBanner message={secError} />
                    {secDone && (
                      <div className="security-done">
                        <SuccessFlash title="Password updated" sub="Use the new password next time you sign in." />
                      </div>
                    )}
                    <div className="settings-actions">
                      <LoadingButton
                        loading={secBusy}
                        loadingText="Updating password\u2026"
                        className="save-btn"
                        disabled={!secCurrent || secNew.length < 8 || secNew !== secConfirm}
                      >
                        Save Changes
                      </LoadingButton>
                    </div>
                  </form>
                ) : (
                  <div className="settings-table">
                    <div className="settings-row">
                      <div className="settings-cell">
                        <p className="settings-label">Password security</p>
                        <p className="settings-note">Sign in to change your password.</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {section === 'danger' && (
              <div className="settings-section">
                <div className="settings-table danger-table">
                  <div className="settings-row">
                    <div className="settings-cell">
                      <p className="settings-label">Sign out of sketch2cad</p>
                      <p className="settings-note">Ends this session. Projects and chats stay on this machine.</p>
                    </div>
                    <div className="settings-cell right">
                      <button
                        type="button"
                        className={`danger-btn ${logoutArmed ? 'armed' : ''}`}
                        onClick={() => {
                          if (logoutArmed) onLogout()
                          else setLogoutArmed(true)
                        }}
                      >
                        {logoutArmed ? 'Really sign out?' : 'Logout'}
                      </button>
                    </div>
                  </div>
                </div>
                <p className="settings-solver-note">
                  {logoutArmed
                    ? 'Click again to confirm \u2014 the modal will close and the top bar will show Login.'
                    : 'You can always sign back in \u2014 your local data is untouched.'}
                </p>
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
