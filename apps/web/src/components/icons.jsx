/* Inline SVG icon set — no icon dependency, keeps the SPA lightweight. */

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export const IconSearch = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m20 20-3.6-3.6" />
  </svg>
)

export const IconChevron = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" className={className} {...base}>
    <path d="m6 9 6 6 6-6" />
  </svg>
)

export const IconSettings = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="12" cy="12" r="3.2" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 9 19.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.65 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1.03-1.56V3a2 2 0 1 1 4 0v.09c0 .68.4 1.29 1.03 1.56.61.28 1.33.2 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V9c.27.63.88 1.03 1.56 1.03H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51.97Z" />
  </svg>
)

export const IconLogout = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M14 4h-7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h7" />
    <path d="M10 12h10m0 0-3-3m3 3-3 3" />
  </svg>
)

export const IconPlus = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M12 5v14M5 12h14" />
  </svg>
)

export const IconChat = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.3 8.9 8.9 0 0 1-3.8-.9L3 20l1.2-5.2a8.2 8.2 0 0 1-1.2-4.3A8.38 8.38 0 0 1 11.5 2 8.38 8.38 0 0 1 21 11.5Z" />
  </svg>
)

export const IconProject = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M3.5 7.5 12 3l8.5 4.5L12 12Z" />
    <path d="M3.5 12 12 16.5 20.5 12" />
    <path d="M3.5 16.5 12 21l8.5-4.5" />
  </svg>
)

export const IconAttach = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m20.6 11.4-8.5 8.5a5 5 0 0 1-7.1-7.1l8.6-8.6a3.3 3.3 0 0 1 4.7 4.7l-8.6 8.5a1.7 1.7 0 0 1-2.4-2.4l8-8" />
  </svg>
)

export const IconSend = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M12 19V5m0 0-6 6m6-6 6 6" />
  </svg>
)

export const IconCopy = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
)

export const IconCheck = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m4 12.5 5 5L20 6.5" />
  </svg>
)

export const IconMenu = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M4 7h16M4 12h16M4 17h10" />
  </svg>
)

export const IconClose = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m6 6 12 12M18 6 6 18" />
  </svg>
)

/* Brand mark: a wobbly hand-sketched line resolving into crisp CAD linework. */
export const LogoMark = ({ size = 26 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="logo-mark">
    <rect x="1.5" y="1.5" width="29" height="29" rx="8" fill="var(--blueprint)" />
    <path
      className="lm-sketch"
      d="M7 21c2 1.6 3.6-2 6-1.4 2.4.6 3 2.6 5.5 1.6"
      fill="none"
      stroke="#FFFFFF"
      strokeOpacity=".62"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeDasharray="3 2.6"
    />
    <path
      className="lm-cad"
      d="M18.5 21.2 L22 21.2 L23.2 17.2 L26.6 17.2"
      fill="none"
      stroke="#FFFFFF"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="7" cy="21" r="1.3" fill="#FFFFFF" />
  </svg>
)
