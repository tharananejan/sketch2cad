import { DESIGNS } from '../designs'

export default function BlueprintSheet({ design }) {
  const d = design ?? DESIGNS[0]
  return (
    <div className="sheet-stage">
      <div className="sheet">
        <div className="sheet-titlebar">
          <span className="mono">{d.sheetRef}</span>
          <span className={`mono level-badge tone-${d.tone}`}>{d.level}</span>
        </div>

        {d.art}

        <div className="sheet-copy">
          <p className="sheet-eyebrow mono">{d.eyebrow}</p>
          <h1 className="sheet-title">{d.title}</h1>
          <p className="sheet-sub">{d.sub}</p>
        </div>
      </div>

      <p className="sheet-footnote mono">
        Every dimension is a parameter you can change later &middot; nothing is hard-coded
      </p>
    </div>
  )
}
