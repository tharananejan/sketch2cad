import {
  IconProject,
  IconChat,
  IconPlus,
  IconClose,
  LogoMark,
} from './icons'

export default function Sidebar({
  projects,
  activeProjectId,
  activeChatId,
  filteredChats,
  query,
  totalChats,
  onSelectProject,
  onSelectChat,
  onNewChat,
  open,
  onClose,
}) {
  return (
    <>
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-scroll">
          <div className="rail-head">
            <span className="eyebrow mono">Projects</span>
            <span className="rail-count mono">{projects.length}</span>
          </div>

          <div className="project-list" role="listbox" aria-label="Projects">
            {projects.map((p) => (
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
            ))}
          </div>

          <div className="rail-head chat-head">
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

        <div className="rail-foot">
          <div className="local-card">
            <span className="live-dot" aria-hidden="true" />
            <div>
              <p className="local-title">Local engine</p>
              <p className="local-sub mono">models run on this machine</p>
            </div>
            <LogoMark size={18} />
          </div>
        </div>
      </aside>

      {open && (
        <button type="button" className="scrim" aria-label="Close sidebar" onClick={onClose}>
          <IconClose />
        </button>
      )}
    </>
  )
}
