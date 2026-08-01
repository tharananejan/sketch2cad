import { LogoMark, IconChevronLeft, IconChevronRight, IconSun, IconMoon } from './icons'

export default function TopBar({ onToggleSidebar, theme, onToggleTheme, sidebarVisible }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="icon-btn sidebar-toggle"
          onClick={onToggleSidebar}
          aria-label={sidebarVisible ? 'Hide project sidebar' : 'Show project sidebar'}
          title={sidebarVisible ? 'Hide sidebar' : 'Show sidebar'}
        >
          {sidebarVisible ? <IconChevronLeft size={17} /> : <IconChevronRight size={17} />}
        </button>
        <a className="brand" href="#root" aria-label="sketch2cad home">
          <LogoMark size={26} />
          <span className="brand-word">sketch2cad</span>
        </a>
        <button
          type="button"
          className="theme-btn"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <IconSun size={17} /> : <IconMoon size={17} />}
        </button>
      </div>
    </header>
  )
}
