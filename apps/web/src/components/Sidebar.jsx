import { useEffect, useRef, useState } from 'react'
import {
  IconProject,
  IconChat,
  IconPlus,
  IconSearch,
  IconChevron,
  IconSettings,
  IconLogout,
} from './icons'

export default function Sidebar({
  projects,
  filteredProjects,
  activeProject,
  activeProjectId,
  activeChatId,
  filteredChats,
  query,
  onQuery,
  totalChats,
  onSelectProject,
  onSelectChat,
  onNewChat,
  onNewProject,
  onOpenSettings,
  onLogout,
  open,
  collapsed,
  isMobile,
  onClose,
  onExpand,
  onSelectProjectRail,
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [hovering, setHovering] = useState(false)
  const rootRef = useRef(null)
  const searchRef = useRef(null)
  const pendingFocus = useRef(false)

  const menuVisible = menuOpen || hovering

  // Close the account menu on outside click or Escape.
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

  // "/" focuses search (expanding the sidebar first if it's collapsed).
  useEffect(() => {
    function onKey(e) {
      const tag = e.target.tagName
      if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA') {
        e.preventDefault()
        if (collapsed || (isMobile && !open)) {
          // drawer or rail is hidden — expand first, then focus search
          pendingFocus.current = true
          onExpand()
        } else {
          searchRef.current?.focus()
        }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [collapsed, open, isMobile, onExpand])

  // After expanding from the rail or opening the mobile drawer, hand focus to the search box.
  useEffect(() => {
    if (!collapsed && pendingFocus.current) {
      pendingFocus.current = false
      searchRef.current?.focus()
    }
  }, [collapsed, open])

  function railSearch() {
    pendingFocus.current = true
    onExpand()
  }

  if (collapsed) {
    return (
      <aside className="sidebar rail" aria-label="Project rail">
        <div className="rail-inner">
          <button type="button" className="rail-icon" onClick={railSearch} aria-label="Search" title="Search">
            <IconSearch size={17} />
          </button>
          <button type="button" className="rail-icon" onClick={onNewProject} aria-label="New project" title="New project">
            <IconPlus size={17} />
          </button>
          <div className="rail-divider" aria-hidden="true" />
          <div className="rail-project-icons">
            {filteredProjects.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`rail-icon ${p.id === activeProjectId ? 'active' : ''}`}
                onClick={() => onSelectProjectRail(p.id)}
                aria-label={p.name}
                title={p.name}
              >
                <IconProject size={17} />
              </button>
            ))}
          </div>
        </div>
        <div className="rail-bottom">
          <button type="button" className="rail-avatar" onClick={onExpand} aria-label="Open sidebar" title="Open sidebar">
            <span className="avatar">AR</span>
          </button>
        </div>
      </aside>
    )
  }

  return (
    <>
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-body">
          <div className="sidebar-search">
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

          <div className="projects-region">
            <div className="rail-head">
              <span className="eyebrow mono">Projects</span>
              <span className="rail-count mono">{projects.length}</span>
            </div>

            <button type="button" className="new-project" onClick={onNewProject}>
              <IconPlus size={14} />
              New project
            </button>

            <div className="project-list" role="listbox" aria-label="Projects">
              {filteredProjects.length === 0 ? (
                <p className="no-matches mono">No matching projects</p>
              ) : (
                filteredProjects.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    role="option"
                    aria-selected={p.id === activeProjectId}
                    className={`project-row ${p.id === activeProjectId ? 'active' : ''}`}
                    onClick={() => onSelectProject(p.id)}
                  >
                    <IconProject size={15} />
                    <span className="project-name">{p.name}</span>
                    <span className="mono project-count">{p.chats.length}</span>
                  </button>
                ))
              )}
            </div>
          </div>

          {activeProject && (
            <div className="chats-region">
              <div className="rail-head">
                <span className="eyebrow mono">Chats</span>
                <span className="rail-count mono">{totalChats}</span>
              </div>

              <button type="button" className="new-chat" onClick={onNewChat}>
                <IconPlus size={15} />
                New chat
                <kbd className="mono">↵</kbd>
              </button>

              <div className="chat-list" role="listbox" aria-label="Chat history">
                {filteredChats.length === 0 ? (
                  <p className="no-matches mono">
                    No matches for &ldquo;{query}&rdquo;
                  </p>
                ) : (
                  filteredChats.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      role="option"
                      aria-selected={c.id === activeChatId}
                      className={`chat-row ${c.id === activeChatId ? 'active' : ''}`}
                      onClick={() => onSelectChat(c.id)}
                    >
                      <IconChat size={14} />
                      <span className="chat-name">{c.name}</span>
                      <span className="mono chat-time">
                        {c.messages.length > 0 ? c.messages[c.messages.length - 1].time : ''}
                      </span>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="rail-foot">
          <div className="usage-card">
            <div className="usage-head">
              <span className="usage-label">Model usage</span>
              <span className="mono usage-pct">42%</span>
            </div>
            <div className="usage-track" role="progressbar" aria-valuenow={42} aria-valuemin={0} aria-valuemax={100} aria-label="Model usage this month">
              <div className="usage-fill" style={{ width: '42%' }} />
            </div>
            <p className="usage-sub mono">12 of 28 local drafts this month</p>
          </div>

          <div
            className="profile-wrap"
            ref={rootRef}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
          >
            <button
              type="button"
              className="profile-btn sidebar-profile"
              aria-haspopup="menu"
              aria-expanded={menuVisible}
              aria-label="Account menu"
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span className="avatar">AR</span>
              <span className="profile-id">
                <span className="profile-name-sm">Ari R.</span>
                <span className="profile-mail mono">ari@studio.local</span>
              </span>
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
      </aside>

      {open && (
        <button type="button" className="scrim" aria-label="Close sidebar" onClick={onClose}>
          &nbsp;
        </button>
      )}
    </>
  )
}
