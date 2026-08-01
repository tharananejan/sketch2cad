import { useEffect, useRef, useState } from 'react'
import BlueprintSheet from './BlueprintSheet'
import { DESIGNS } from '../designs'
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
            <i />
            <i />
            <i />
          </span>
          <span className="mono draft-label">Drafting</span>
        </div>
      </div>
    </article>
  )
}

function DesignShowcase({ design, index, onPick }) {
  return (
    <div className="showcase">
      <div className="showcase-stage" key={index}>
        <BlueprintSheet design={design} />
      </div>
      <div className="showcase-dots" aria-label="Designs">
        {DESIGNS.map((d, i) => (
          <button
            key={d.id}
            type="button"
            aria-pressed={i === index}
            aria-label={`${d.level} design ${i + 1}`}
            className={`showcase-dot tone-${d.tone} ${i === index ? 'active' : ''}`}
            onClick={() => onPick(i)}
          />
        ))}
      </div>
    </div>
  )
}

function WelcomeState({ design, index, onPick }) {
  return (
    <div className="welcome">
      <LogoMark size={44} />
      <p className="welcome-eyebrow mono">sketch2cad &middot; the drafting desk</p>
      <h1 className="welcome-title">What are we drafting?</h1>
      <p className="welcome-sub">
        Designs rotate below — follow the suggested prompt in the box, or describe your own part.
      </p>
      <DesignShowcase design={design} index={index} onPick={onPick} />
    </div>
  )
}

function Composer({ onSend, suggestedPrompt }) {
  const [value, setValue] = useState('')
  const [typed, setTyped] = useState('')
  const ref = useRef(null)
  const typing = !!suggestedPrompt && value === ''

  // Type the suggested prompt out, character by character.
  // Stops as soon as the user takes over (typing becomes false).
  useEffect(() => {
    setTyped('')
    if (!suggestedPrompt || !typing) return
    let i = 0
    const iv = window.setInterval(() => {
      i += 1
      setTyped(suggestedPrompt.slice(0, i))
      if (i >= suggestedPrompt.length) window.clearInterval(iv)
    }, 30)
    return () => window.clearInterval(iv)
  }, [suggestedPrompt, typing])

  function autoGrow() {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  useEffect(() => {
    autoGrow()
  }, [typed])

  function submit() {
    const text = typing ? suggestedPrompt : value
    if (!text.trim()) return
    const sent = onSend(text)
    if (sent === false) return // nothing accepted — keep the text
    setValue('')
    setTyped('')
    requestAnimationFrame(() => {
      if (ref.current) {
        ref.current.style.height = 'auto'
        ref.current.focus()
      }
    })
  }

  function handleFocus() {
    // Adopt the partially-typed suggestion so the user can edit it from there.
    if (typing) setValue(typed)
  }

  const canSend = (typing ? typed : value).trim() !== ''

  return (
    <div className="composer-wrap">
      <div className="composer">
        <button type="button" className="attach-btn" aria-label="Attach a sketch">
          <IconAttach />
          <span className="attach-label">Attach sketch</span>
        </button>
        <div className="composer-input-wrap">
          {typing && (
            <div className="suggestion-overlay" aria-hidden="true">
              {typed}
              <span className="type-caret" />
            </div>
          )}
          <textarea
            ref={ref}
            value={typing ? '' : value}
            rows={1}
            placeholder={typing ? '' : 'Describe the part, or attach a sketch…'}
            aria-label="Message"
            className={typing ? 'ghost' : ''}
            onChange={(e) => setValue(e.target.value)}
            onInput={autoGrow}
            onFocus={handleFocus}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
          />
        </div>
        <button
          type="button"
          className={`send-btn ${canSend ? 'ready' : ''}`}
          aria-label="Send message"
          disabled={!canSend}
          onClick={submit}
        >
          <IconSend size={17} />
        </button>
      </div>
      <p className="composer-hint mono">
        {typing ? 'Suggested — press Enter to use' : 'Enter to send · Shift+Enter for a new line'}
      </p>
    </div>
  )
}

export default function ChatPane({ chat, drafting, onSend }) {
  const [slide, setSlide] = useState(0)
  const scrollRef = useRef(null)

  // Auto-advance the design slideshow while no chat is open.
  useEffect(() => {
    if (chat) return
    const iv = window.setInterval(() => setSlide((s) => (s + 1) % DESIGNS.length), 6000)
    return () => window.clearInterval(iv)
  }, [chat])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [chat?.id, chat?.messages?.length, drafting])

  const messages = chat?.messages ?? []
  const design = DESIGNS[slide]

  return (
    <section className="chatpane" aria-label={chat ? `Chat: ${chat.name ?? ''}` : 'Drafting desk'}>
      <div className="thread-scroll" ref={scrollRef}>
        {!chat ? (
          <WelcomeState design={design} index={slide} onPick={setSlide} />
        ) : messages.length === 0 ? (
          <BlueprintSheet design={DESIGNS[0]} />
        ) : (
          <div className="thread">
            {messages.map((m) => (
              <Message key={m.id} msg={m} onCopy={(t) => navigator.clipboard?.writeText(t)} />
            ))}
            {drafting && <Drafting />}
          </div>
        )}
      </div>

      <Composer onSend={onSend} suggestedPrompt={chat ? null : design.prompt} />
    </section>
  )
}
