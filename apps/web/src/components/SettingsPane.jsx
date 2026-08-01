import { IconChevron, LogoMark } from './icons'

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
    value: 'Local Qwen · 4-bit',
    note: 'Runs on this machine, nothing leaves it',
  },
]

export default function SettingsPane({ onBack }) {
  return (
    <section className="settingspane" aria-label="Settings">
      <button type="button" className="back-btn" onClick={onBack}>
        <IconChevron size={16} />
        <span>Back to chat</span>
      </button>

      <header className="settings-head">
        <span className="eyebrow mono">Workspace</span>
        <h1 className="settings-title">Settings</h1>
        <p className="settings-sub">Preferences for how sketch2cad drafts and exports your models.</p>
      </header>

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
      </div>

      <footer className="settings-about mono">
        <LogoMark size={16} /> sketch2cad v0.1.0 &middot; local-first &middot; no cloud
      </footer>
    </section>
  )
}
