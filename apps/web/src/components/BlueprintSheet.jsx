const SUGGESTIONS = [
  'A mounting bracket with four 6mm holes',
  '60mm cooling duct bent 90\u00b0',
  'Split housing with 10mm walls',
]

export default function BlueprintSheet({ onPick }) {
  return (
    <div className="sheet-stage">
      <div className="sheet">
        <div className="sheet-titlebar">
          <span className="mono">SHEET 01 &middot; A3 &middot; 1:1</span>
          <span className="mono">sketch2cad &middot; DRAFT</span>
        </div>

        <svg
          className="sheet-art"
          viewBox="0 0 640 260"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
        >
          {/* dimension leaders */}
          <g className="dim dims">
            <path d="M70 208 H230 M78 208 v9 M222 208 v9" />
            <text x="150" y="234">120</text>
            <path d="M252 208 H370 M260 208 v9 M362 208 v9" />
            <text x="311" y="234">80</text>
            <path d="M520 40 V168 M520 48 h-9 M520 160 h-9" />
            <text x="538" y="106">16</text>
          </g>

          {/* hand-sketch pass (wobbly, dashed) */}
          <g className="sketch">
            <path d="M88 108 c18-14 34 20 56 6 s30-22 52-10 s36 8 56-4 s36-16 58-8 s40 10 60 2" />
            <circle cx="150" cy="76" r="17" />
            <circle cx="330" cy="74" r="17" />
            <circle cx="500" cy="66" r="17" />
            <path d="M88 108 v-12 M512 98 v18 M590 92 v14" />
          </g>

          {/* CAD pass (crisp, solid, drawn in) */}
          <g className="cad">
            <path d="M88 108 H590" />
            <path d="M88 96 V108 M512 98 V108 M590 92 V108" />
            <circle cx="150" cy="76" r="17" />
            <circle cx="330" cy="74" r="17" />
            <circle cx="500" cy="66" r="17" />
          </g>

          <g className="dim marks">
            <circle cx="150" cy="76" r="10" />
            <circle cx="330" cy="74" r="10" />
            <circle cx="500" cy="66" r="10" />
          </g>
        </svg>

        <div className="sheet-copy">
          <p className="sheet-eyebrow mono">From hand sketch to parametric model</p>
          <h1 className="sheet-title">Sketch it.<br />CAD it.</h1>
          <p className="sheet-sub">
            Describe a part in plain words or drop a hand sketch — I\u2019ll turn it into a
            dimensioned, editable FreeCAD model that lives on your machine.
          </p>

          <div className="sheet-suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button key={s} type="button" className="suggestion" onClick={() => onPick(s)}>
                <span className="mono suggestion-mark">{String(i + 1).padStart(2, '0')}</span>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <p className="sheet-footnote mono">
        Every dimension is a parameter you can change later &middot; nothing is hard-coded
      </p>
    </div>
  )
}
