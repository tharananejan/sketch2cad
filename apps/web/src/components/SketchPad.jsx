import { useEffect, useRef, useState } from 'react'
import { IconClose, IconCheck } from './icons'

const COLORS = [
  { id: 'blue', value: '#0e5fd8', name: 'Blueprint blue' },
  { id: 'ink', value: '#1e232b', name: 'Ink' },
  { id: 'orange', value: '#e85d1f', name: 'Safety orange' },
]

const SIZES = [2, 4, 7]

export default function SketchPad({ onAttach, onClose }) {
  const canvasRef = useRef(null)
  const [tool, setTool] = useState('pen') // 'pen' | 'eraser'
  const [color, setColor] = useState(COLORS[0].value)
  const [size, setSize] = useState(SIZES[1])
  const [hasInk, setHasInk] = useState(false)
  const drawing = useRef(false)
  const lastPoint = useRef(null)
  const undoStack = useRef([])
  const dirtyRef = useRef(false)

  // Fit the canvas to its container at devicePixelRatio for crisp lines.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    const dpr = window.devicePixelRatio || 1
    const rect = parent.getBoundingClientRect()
    canvas.width = Math.max(1, Math.round(rect.width * dpr))
    canvas.height = Math.max(1, Math.round(rect.height * dpr))
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
  }, [])

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  function getPos(e) {
    const rect = canvasRef.current.getBoundingClientRect()
    return { x: e.clientX - rect.left, y: e.clientY - rect.top }
  }

  function strokeStart(e) {
    e.preventDefault()
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    // Only snapshot when the canvas already has ink, so the first Undo
    // restores a real previous state instead of a blank no-op.
    if (dirtyRef.current) {
      undoStack.current.push(ctx.getImageData(0, 0, canvas.width, canvas.height))
      if (undoStack.current.length > 30) undoStack.current.shift()
    }
    canvas.setPointerCapture?.(e.pointerId)
    drawing.current = true
    lastPoint.current = getPos(e)
    ctx.beginPath()
    ctx.moveTo(lastPoint.current.x, lastPoint.current.y)
  }

  function strokeMove(e) {
    if (!drawing.current) return
    // A real mark is being drawn — arm the snapshot gate and show ink.
    dirtyRef.current = true
    setHasInk(true)
    const ctx = canvasRef.current.getContext('2d')
    const p = getPos(e)
    const prev = lastPoint.current
    ctx.globalCompositeOperation = tool === 'eraser' ? 'destination-out' : 'source-over'
    ctx.strokeStyle = tool === 'eraser' ? 'rgba(0,0,0,1)' : color
    ctx.lineWidth = tool === 'eraser' ? size * 3 : size
    ctx.beginPath()
    ctx.moveTo(prev.x, prev.y)
    ctx.lineTo(p.x, p.y)
    ctx.stroke()
    lastPoint.current = p
  }

  function strokeEnd() {
    drawing.current = false
    lastPoint.current = null
  }

  function undo() {
    const snap = undoStack.current.pop()
    if (!snap) return
    const ctx = canvasRef.current.getContext('2d')
    ctx.putImageData(snap, 0, 0)
    // The restored state still has ink (the first stroke never gets a
    // snapshot), so hasInk stays true — only Clear resets it.
  }

  function clear() {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    ctx.save()
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.restore()
    undoStack.current = []
    lastPoint.current = null
    dirtyRef.current = false
    setHasInk(false)
  }

  function attach() {
    const url = canvasRef.current.toDataURL('image/png')
    onAttach(url)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="sketch-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Sketch pad"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="sketch-head">
          <div>
            <span className="eyebrow mono">Freehand</span>
            <h2 className="sketch-title">Sketch pad</h2>
          </div>
          <button type="button" className="close-btn" onClick={onClose} aria-label="Close sketch pad">
            <IconClose size={18} />
          </button>
        </header>

        <div className="sketch-tools" role="toolbar" aria-label="Sketch tools">
          <div className="sketch-tool-group" role="group" aria-label="Tool">
            <button
              type="button"
              className={`sketch-tool ${tool === 'pen' ? 'active' : ''}`}
              onClick={() => setTool('pen')}
            >
              Pen
            </button>
            <button
              type="button"
              className={`sketch-tool ${tool === 'eraser' ? 'active' : ''}`}
              onClick={() => setTool('eraser')}
            >
              Eraser
            </button>
          </div>

          {tool === 'pen' && (
            <div className="sketch-tool-group swatches" role="group" aria-label="Ink color">
              {COLORS.map((c) => (
                <button
                  type="button"
                  key={c.id}
                  className={`swatch ${color === c.value ? 'active' : ''}`}
                  style={{ background: c.value }}
                  aria-label={c.name}
                  aria-pressed={color === c.value}
                  onClick={() => setColor(c.value)}
                />
              ))}
            </div>
          )}

          <div className="sketch-tool-group" role="group" aria-label="Brush size">
            {SIZES.map((s) => (
              <button
                type="button"
                key={s}
                className={`sketch-tool ${size === s ? 'active' : ''}`}
                onClick={() => setSize(s)}
              >
                <span className="size-dot" style={{ width: s * 2 + 2, height: s * 2 + 2 }} />
              </button>
            ))}
          </div>

          <div className="sketch-tool-group sketch-tools-right" role="group" aria-label="Edit">
            <button type="button" className="sketch-tool" onClick={undo} disabled={!hasInk}>
              Undo
            </button>
            <button type="button" className="sketch-tool danger" onClick={clear} disabled={!hasInk}>
              Clear
            </button>
          </div>
        </div>

        <div className="sketch-canvas-wrap">
          <canvas
            ref={canvasRef}
            className="sketch-canvas"
            aria-label="Drawing area"
            onPointerDown={strokeStart}
            onPointerMove={strokeMove}
            onPointerUp={strokeEnd}
            onPointerLeave={strokeEnd}
          />
        </div>

        <footer className="sketch-foot">
          <p className="sketch-hint mono">
            {tool === 'pen' ? 'Draw the part \u2014 press Undo to step back.' : 'Rub out marks you don\u2019t want.'}
          </p>
          <button type="button" className="save-btn" onClick={attach} disabled={!hasInk}>
            <IconCheck size={15} />
            Attach sketch
          </button>
        </footer>
      </div>
    </div>
  )
}
