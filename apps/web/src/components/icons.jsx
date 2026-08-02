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

export const IconChevronLeft = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m15 6-6 6 6 6" />
  </svg>
)

export const IconChevronRight = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m9 6 6 6-6 6" />
  </svg>
)

export const IconDots = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" fill="currentColor" stroke="none">
    <circle cx="12" cy="5.5" r="1.6" />
    <circle cx="12" cy="12" r="1.6" />
    <circle cx="12" cy="18.5" r="1.6" />
  </svg>
)

export const IconClose = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m6 6 12 12M18 6 6 18" />
  </svg>
)

export const IconImage = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
    <circle cx="9" cy="9.5" r="1.6" />
    <path d="m5 17.5 4.2-4.2 2.4 2.4 3-3 4.4 4.8" />
  </svg>
)

export const IconSketch = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="m4 20 4.5-1.2L19.8 7.5a2.1 2.1 0 0 0-3-3L5.5 15.8 4 20Z" />
    <path d="m14.5 6.8 2.7 2.7" />
  </svg>
)

export const IconShare = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="18" cy="5.5" r="2.6" />
    <circle cx="6" cy="12" r="2.6" />
    <circle cx="18" cy="18.5" r="2.6" />
    <path d="m8.2 10.9 7.6-4.4M8.2 13.1l7.6 4.4" />
  </svg>
)

export const IconUser = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="12" cy="8" r="3.6" />
    <path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" />
  </svg>
)

export const IconRuler = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M3 8.5 8.5 3 21 15.5 15.5 21 3 8.5Z" />
    <path d="m6.6 7.1 2.1 2.1M9.9 9.8l2.1 2.1M13.2 12.5l2.1 2.1" />
  </svg>
)

export const IconDownload = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M12 3.5V15m0 0 4.2-4.2M12 15l-4.2-4.2" />
    <path d="M4.5 17v2.5a1 1 0 0 0 1 1h13a1 1 0 0 0 1-1V17" />
  </svg>
)

export const IconSun = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2.6v2.3M12 19.1v2.3M2.6 12h2.3M19.1 12h2.3M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4 17 7M7 17l-1.6 1.6" />
  </svg>
)

export const IconMoon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M20.6 14.6A8.6 8.6 0 0 1 9.4 3.4a8.6 8.6 0 1 0 11.2 11.2Z" />
  </svg>
)

/* Official Google G — multicolor, for the branded OAuth button. */
export const IconGoogle = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
    <path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47a5.57 5.57 0 0 1-2.4 3.58v3h3.86c2.26-2.09 3.56-5.17 3.56-8.82Z" />
    <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09A11.99 11.99 0 0 0 12 24Z" />
    <path fill="#FBBC05" d="M5.27 14.29A7.17 7.17 0 0 1 4.89 12c0-.8.14-1.57.38-2.29V6.62H1.29a11.99 11.99 0 0 0 0 10.76l3.98-3.09Z" />
    <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.69 1.29 6.62l3.98 3.09C6.22 6.86 8.87 4.75 12 4.75Z" />
  </svg>
)

export const IconEye = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
    <circle cx="12" cy="12" r="2.8" />
  </svg>
)

export const IconEyeOff = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M2.5 12S6 5.5 12 5.5c1.2 0 2.3.25 3.3.66M20.9 9.4C21.8 10.6 21.5 12 21.5 12s-3.5 6.5-9.5 6.5c-1.4 0-2.7-.33-3.8-.9" />
    <path d="m4 4 16 16" />
  </svg>
)

export const IconMail = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <rect x="3" y="5" width="18" height="14" rx="2.5" />
    <path d="m4 7.5 8 5.5 8-5.5" />
  </svg>
)

export const IconLock = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <rect x="5" y="10.5" width="14" height="9.5" rx="2.5" />
    <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
    <circle cx="12" cy="15.5" r="1.4" />
  </svg>
)

export const IconShield = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M12 3 5 6v5.5c0 4.4 3 8 7 9.5 4-1.5 7-5.1 7-9.5V6Z" />
    <path d="m9 11.8 2.2 2.2 4-4.2" />
  </svg>
)

export const IconKey = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="8" cy="15.5" r="4.5" />
    <path d="m11.2 12.3 8.3-8.3M16 7l3 3M13 10l2 2" />
  </svg>
)

export const IconArrowLeft = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M19 12H5m0 0 6-6m-6 6 6 6" />
  </svg>
)

export const IconRefresh = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M20 11a8 8 0 1 0-2.3 6.3" />
    <path d="M20 5v6h-6" />
  </svg>
)

export const IconTrash = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M4 7h16M9 7V4.5h6V7M6.5 7l1 13h9l1-13" />
    <path d="M10 11v5.5M14 11v5.5" />
  </svg>
)

export const IconAlert = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <path d="M12 3.5 2.5 20h19Z" />
    <path d="M12 10v4.5M12 17.5v.5" />
  </svg>
)

export const IconCheckCircle = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8 12.2 2.6 2.6L16.2 9" />
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
