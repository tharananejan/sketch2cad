import { useEffect, useRef, useState } from 'react'
import BlueprintSheet from './BlueprintSheet'
import SketchPad from './SketchPad'
import { DESIGNS } from '../designs'
import {
  LogoMark,
  IconAttach,
  IconSend,
  IconCopy,
  IconCheck,
  IconImage,
  IconSketch,
  IconClose,
} from './icons'

const uid = () => Math.random().toString(36).slice(2, 9)

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
        {msg.attachments?.length > 0 && (
          <div className="msg-attachments">
            {msg.attachments.map((a) => (
              <img key={a.id} src={a.url} alt={a.name || 'Attached sketch'} className="msg-attach-img" />
            ))}
          </div>
        )}
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
  const [attachOpen, setAttachOpen] = useState(false)
  const [sketchOpen, setSketchOpen] = useState(false)
  const [attachments, setAttachments] = useState([])
  const ref = useRef(null)
  const fileRef = useRef(null)
  const typing = !!suggestedPrompt && value === ''

  // Close the attach popup on outside click or Escape.
  useEffect(() => {
    if (!attachOpen) return
    function onDown(e) {
      if (!e.target.closest('.attach-wrap')) setAttachOpen(false)
      if (e.key === 'Escape') setAttachOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onDown)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onDown)
    }
  }, [attachOpen])

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

  function pickImage(e) {
    const f = e.target.files?.[0]
    if (!f) return
    const url = URL.createObjectURL(f)
    setAttachments((a) => [...a, { id: uid(), kind: 'image', url, name: f.name }])
    setAttachOpen(false)
    e.target.value = ''
  }

  function attachSketch(url) {
    setAttachments((a) => [...a, { id: uid(), kind: 'sketch', url, name: 'Sketch' }])
    setSketchOpen(false)
  }

  function removeAttachment(id) {
    // Revoke the object URL before the chip is dropped — nothing else
    // references it once it's out of the preview list.
    const gone = attachments.find((x) => x.id === id)
    if (gone?.kind === 'image') URL.revokeObjectURL(gone.url)
    setAttachments((arr) => arr.filter((x) => x.id !== id))
  }

  function submit() {
    const text = typing ? suggestedPrompt : value
    if (!text.trim() && attachments.length === 0) return
    const sent = onSend(text, attachments)
    if (sent === false) return // nothing accepted — keep the text
    // Note: object URLs stay alive for the session — the sent message
    // renders the same image, so we must NOT revoke them here.
    setValue('')
    setTyped('')
    setAttachments([])
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

  const canSend = (typing ? typed : value).trim() !== '' || attachments.length > 0

  return (
    <div className="composer-wrap">
      {attachments.length > 0 && (
        <div className="attach-previews" aria-label="Attached sketches">
          {attachments.map((a) => (
            <span className="attach-chip" key={a.id}>
              <img src={a.url} alt={a.name} />
              <button
                type="button"
                className="chip-x"
                aria-label={`Remove ${a.name}`}
                onClick={() => removeAttachment(a.id)}
              >
                <IconClose size={11} />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="composer">
        <span className="attach-wrap">
          <button
            type="button"
            className={`attach-btn ${attachOpen ? 'open' : ''}`}
            aria-label="Attach a sketch"
            aria-expanded={attachOpen}
            onClick={() => setAttachOpen((v) => !v)}
          >
            <IconAttach />
          </button>
          {attachOpen && (
            <div className="attach-pop" role="menu" aria-label="Attach options">
              <button
                type="button"
                role="menuitem"
                onClick={() => fileRef.current?.click()}
              >
                <IconImage size={15} />
                Upload image
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setAttachOpen(false)
                  setSketchOpen(true)
                }}
              >
                <IconSketch size={15} />
                Sketch pad
              </button>
            </div>
          )}
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={pickImage} />
        </span>
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

      {sketchOpen && <SketchPad onClose={() => setSketchOpen(false)} onAttach={attachSketch} />}
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
