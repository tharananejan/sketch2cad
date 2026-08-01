import { useEffect, useRef, useState } from 'react'
import BlueprintSheet from './BlueprintSheet'
import { LogoMark, IconAttach, IconSend, IconCopy, IconCheck } from './icons'

function Message({ msg, onCopy }) {
  const [copied, setCopied] = useState(false)
  const isUser = msg.role === 'user'

  return (
    <article className={`msg ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <span className="msg-avatar" aria-hidden="true">
          <LogoMark size={20} />
        </span>
      )}
      <div className="msg-body">
        <div className="msg-bubble">{msg.text}</div>
        <div className="msg-meta mono">
          <span>{msg.time}</span>
          {!isUser && (
            <button
              type="button"
              className="copy-btn"
              aria-label="Copy response"
              onClick={() => {
                onCopy(msg.text)
                setCopied(true)
                window.setTimeout(() => setCopied(false), 1400)
              }}
            >
              {copied ? <IconCheck /> : <IconCopy />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          )}
        </div>
      </div>
    </article>
  )
}

function Drafting() {
  return (
    <article className="msg assistant drafting">
      <span className="msg-avatar" aria-hidden="true">
        <LogoMark size={20} />
      </span>
      <div className="msg-body">
        <div className="msg-bubble drafting-bubble">
          <span className="draft-dots" aria-hidden="true">
            <i /><i /><i />
          </span>
          <span className="mono draft-label">Drafting</span>
        </div>
      </div>
    </article>
  )
}

function Composer({ onSend }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  function autoGrow() {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  function submit() {
    if (!value.trim()) return
    onSend(value)
    setValue('')
    requestAnimationFrame(() => {
      if (ref.current) {
        ref.current.style.height = 'auto'
        ref.current.focus()
      }
    })
  }

  return (
    <div className="composer-wrap">
      <div className="composer">
        <button type="button" className="attach-btn" aria-label="Attach a sketch">
          <IconAttach />
          <span className="attach-label">Attach sketch</span>
        </button>
        <textarea
          ref={ref}
          value={value}
          rows={1}
          placeholder="Describe the part, or attach a sketch\u2026"
          aria-label="Message"
          onInput={autoGrow}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
        />
        <button
          type="button"
          className={`send-btn ${value.trim() ? 'ready' : ''}`}
          aria-label="Send message"
          disabled={!value.trim()}
          onClick={submit}
        >
          <IconSend size={17} />
        </button>
      </div>
      <p className="composer-hint mono">
        Enter to send &middot; Shift+Enter for a new line
      </p>
    </div>
  )
}

export default function ChatPane({ chat, drafting, onSend }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [chat?.id, chat?.messages?.length, drafting])

  const messages = chat?.messages ?? []
  const threadTitle = chat?.name ?? ''

  return (
    <section className="chatpane" aria-label={`Chat: ${threadTitle}`}>
      <div className="thread-head">
        <h2 className="thread-title">{threadTitle}</h2>
        <span className="thread-meta mono">parametric &middot; FreeCAD</span>
      </div>

      <div className="thread-scroll" ref={scrollRef}>
        {messages.length === 0 ? (
          <BlueprintSheet onPick={onSend} />
        ) : (
          <div className="thread">
            {messages.map((m) => (
              <Message key={m.id} msg={m} onCopy={(t) => navigator.clipboard?.writeText(t)} />
            ))}
            {drafting && <Drafting />}
          </div>
        )}
      </div>

      <Composer onSend={onSend} />
    </section>
  )
}
