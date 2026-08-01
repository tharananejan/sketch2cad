import { useEffect, useRef, useState } from 'react'
import { LogoMark, IconSearch, IconChevron, IconSettings, IconLogout, IconChevronLeft, IconChevronRight, IconSun, IconMoon } from './icons'

export default function TopBar({ query, onQuery, onOpenSettings, onLogout, onToggleSidebar, theme, onToggleTheme, sidebarVisible }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [hovering, setHovering] = useState(false)
  const rootRef = useRef(null)
  const searchRef = useRef(null)

  const menuVisible = menuOpen || hovering

  // Close on outside click or Escape.
  useEffect(() => {
    if (!menuVisible) return
    function onDown(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setMenuOpen(false)
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onDown)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onDown)
    }
  }, [menuVisible])

  // "/" focuses search when not already typing.
  useEffect(() => {
    function onKey(e) {
      const tag = e.target.tagName
      if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA') {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

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
      </div>

      <div className="topbar-search">
        <IconSearch size={15} />
        <input
          ref={searchRef}
          type="search"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Search projects & chats"
          aria-label="Search projects and chats"
        />
        <kbd className="mono">/</kbd>
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="theme-btn"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <IconSun size={17} /> : <IconMoon size={17} />}
        </button>

        <div
          className="profile-wrap"
          ref={rootRef}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => setHovering(false)}
        >
        <button
          type="button"
          className="profile-btn"
          aria-haspopup="menu"
          aria-expanded={menuVisible}
          aria-label="Account menu"
          onClick={() => setMenuOpen((v) => !v)}
        >
          <span className="avatar">AR</span>
          <IconChevron className={menuVisible ? 'chev open' : 'chev'} />
        </button>

        <div className={`profile-menu ${menuVisible ? 'show' : ''}`} role="menu" aria-label="Account">
          <div className="profile-head" role="presentation">
            <span className="avatar avatar-lg">AR</span>
            <div>
              <p className="profile-name">Ari R.</p>
              <p className="profile-mail mono">ari@studio.local</p>
            </div>
          </div>
          <div className="menu-rule" />
          <button
            type="button"
            className="menu-item"
            role="menuitem"
            onClick={() => {
              setMenuOpen(false)
              onOpenSettings()
            }}
          >
            <IconSettings />
            Settings
          </button>
          <button
            type="button"
            className="menu-item danger"
            role="menuitem"
            onClick={() => {
              setMenuOpen(false)
              onLogout()
            }}
          >
            <IconLogout />
            Log out
          </button>
        </div>
        </div>
      </div>
    </header>
  )
}
