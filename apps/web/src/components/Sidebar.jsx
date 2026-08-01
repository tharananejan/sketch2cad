import { IconProject, IconChat, IconPlus } from './icons'

export default function Sidebar({
  projects,
  filteredProjects,
  activeProject,
  activeProjectId,
  activeChatId,
  filteredChats,
  query,
  totalChats,
  onSelectProject,
  onSelectChat,
  onNewChat,
  open,
  collapsed,
  onClose,
}) {
  return (
    <>
      <aside className={`sidebar ${open ? 'open' : ''} ${collapsed ? 'collapsed' : ''}`}>
        <div className={`sidebar-body ${activeProject ? '' : 'only'}`}>
          <div className="projects-region">
            <div className="rail-head">
              <span className="eyebrow mono">Projects</span>
              <span className="rail-count mono">{projects.length}</span>
            </div>

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
