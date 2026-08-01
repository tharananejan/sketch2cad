/* Blueprint design presets for the welcome slideshow.
   Each design carries its own sketch->CAD artwork, a difficulty level,
   and a suggested prompt that types itself into the composer. */

const Art = ({ sketch, cad, dims }) => (
  <svg
    className="sheet-art"
    viewBox="0 0 640 260"
    preserveAspectRatio="xMidYMid meet"
    aria-hidden="true"
  >
    <g className="dim dims">{dims}</g>
    <g className="sketch">{sketch}</g>
    <g className="cad">{cad}</g>
  </svg>
)

export const DESIGNS = [
  {
    id: 'bracket',
    level: 'SIMPLE',
    tone: 'blue',
    sheetRef: 'SHEET 01 · A3 · 1:1',
    eyebrow: 'From hand sketch to parametric model',
    title: (
      <>
        Sketch it.
        <br />
        CAD it.
      </>
    ),
    sub: 'A 120×80 bracket with three 6mm holes. Every hole position is a named parameter — change one and the rest follow.',
    prompt: 'Design a simple mounting bracket with three 6mm holes on a 120×80 plate.',
    art: (
      <Art
        dims={
          <>
            <path d="M70 208 H230 M78 208 v9 M222 208 v9" />
            <text x="150" y="234">120</text>
            <path d="M252 208 H370 M260 208 v9 M362 208 v9" />
            <text x="311" y="234">80</text>
            <path d="M520 40 V168 M520 48 h-9 M520 160 h-9" />
            <text x="538" y="106">16</text>
          </>
        }
        sketch={
          <>
            <path d="M88 108 c18-14 34 20 56 6 s30-22 52-10 s36 8 56-4 s36-16 58-8 s40 10 60 2" />
            <circle cx="150" cy="76" r="17" />
            <circle cx="330" cy="74" r="17" />
            <circle cx="500" cy="66" r="17" />
            <path d="M88 108 v-12 M512 98 v18 M590 92 v14" />
          </>
        }
        cad={
          <>
            <path d="M88 108 H590" />
            <path d="M88 96 V108 M512 98 V108 M590 92 V108" />
            <circle cx="150" cy="76" r="17" />
            <circle cx="330" cy="74" r="17" />
            <circle cx="500" cy="66" r="17" />
          </>
        }
      />
    ),
  },
  {
    id: 'corner',
    level: 'SIMPLE',
    tone: 'blue',
    sheetRef: 'SHEET 02 · A3 · 1:1',
    eyebrow: 'Two legs, one fillet',
    title: (
      <>
        Corner
        <br />
        plate.
      </>
    ),
    sub: 'An L-bracket with two 5mm holes and a 3mm fillet on the inside corner.',
    prompt: 'Make an L-shaped corner bracket with two 5mm holes and a 3mm fillet.',
    art: (
      <Art
        dims={
          <>
            <path d="M74 92 V208 M74 100 h-9 M74 200 h-9" />
            <text x="52" y="154">110</text>
            <path d="M128 226 H332 M136 226 v9 M324 226 v9" />
            <text x="216" y="246">150</text>
          </>
        }
        sketch={
          <>
            <path d="M128 84 c4 34-2 72 0 122 M118 206 c40 2 92 4 138 0" />
            <circle cx="200" cy="160" r="16" />
            <circle cx="270" cy="160" r="16" />
          </>
        }
        cad={
          <>
            <path d="M128 84 V206 M336 84 V206 M128 84 H336" />
            <path d="M128 206 H336" />
            <path d="M128 84 Q218 84 218 84" />
            <circle cx="200" cy="160" r="16" />
            <circle cx="270" cy="160" r="16" />
          </>
        }
      />
    ),
  },
  {
    id: 'duct',
    level: 'MEDIUM',
    tone: 'orange',
    sheetRef: 'SHEET 03 · A3 · 1:2',
    eyebrow: 'Bent airflow, constrained',
    title: (
      <>
        Cooling
        <br />
        duct.
      </>
    ),
    sub: 'A 60mm tube bending 90° on an R35 centreline, flanged to a 90×90 plate with four corner holes.',
    prompt: 'Model a 60mm cooling duct that bends 90° to a square flange with four corner holes.',
    art: (
      <Art
        dims={
          <>
            <path d="M88 236 H230 M96 236 v9 M222 236 v9" />
            <text x="150" y="256">90</text>
            <path d="M410 60 V190 M410 68 h9 M410 182 h9" />
            <text x="428" y="128">R35</text>
          </>
        }
        sketch={
          <>
            <path d="M118 224 V150 Q118 112 156 112 H324" />
            <path d="M84 232 H232 M112 212 v30 M172 212 v30" />
          </>
        }
        cad={
          <>
            <path d="M118 224 V150 Q118 112 156 112 H324" strokeWidth="16" />
            <path d="M84 232 H232 M112 212 V242 M172 212 V242" />
            <circle cx="138" cy="227" r="4" />
            <circle cx="178" cy="227" r="4" />
          </>
        }
      />
    ),
  },
  {
    id: 'plate',
    level: 'MEDIUM',
    tone: 'orange',
    sheetRef: 'SHEET 04 · A3 · 1:1',
    eyebrow: 'Slots, not just holes',
    title: (
      <>
        Base
        <br />
        plate.
      </>
    ),
    sub: 'A 120×80 base with two 30mm slots and four M6 clearance holes — slot length driven by one variable.',
    prompt: 'Create a base plate with two 30mm slots and four M6 clearance holes.',
    art: (
      <Art
        dims={
          <>
            <path d="M96 96 H368 M104 96 v-9 M360 96 v-9" />
            <text x="220" y="86">120</text>
            <path d="M78 116 V208 M78 124 h-9 M78 200 h-9" />
            <text x="56" y="166">80</text>
          </>
        }
        sketch={
          <>
            <path d="M96 116 c70-8 150-6 220 0 s80 4 52 0" />
            <path d="M116 208 c60 6 130 4 176 0" />
            <path d="M140 158 h60 M240 158 h60" />
          </>
        }
        cad={
          <>
            <path d="M96 116 H368 V208 H96 Z" />
            <rect x="140" y="148" width="60" height="20" rx="10" />
            <rect x="244" y="148" width="60" height="20" rx="10" />
            <circle cx="122" cy="132" r="8" />
            <circle cx="342" cy="132" r="8" />
          </>
        }
      />
    ),
  },
  {
    id: 'gearbox',
    level: 'HARD',
    tone: 'red',
    sheetRef: 'SHEET 05 · A3 · 1:2',
    eyebrow: 'Two halves, one axis',
    title: (
      <>
        Gearbox
        <br />
        housing.
      </>
    ),
    sub: 'A two-part housing with 10mm walls, a Ø40 bearing seat, and a six-bolt flange split along the shaft axis.',
    prompt: 'Design a two-part gearbox housing with 10mm walls and a Ø40 bearing seat.',
    art: (
      <Art
        dims={
          <>
            <path d="M116 74 H388 M124 74 v-9 M380 74 v-9" />
            <text x="236" y="64">180</text>
            <path d="M424 108 V206 M424 116 h9 M424 198 h9" />
            <text x="442" y="162">10</text>
          </>
        }
        sketch={
          <>
            <path d="M116 108 c60-10 140-8 208 0 c40 4 56 16 56 40" />
            <path d="M116 108 v90 c0 12 12 16 24 16 h150" />
          </>
        }
        cad={
          <>
            <path d="M116 108 H316 M116 108 V208 M316 108 V208" />
            <path d="M116 208 H316" />
            <path d="M216 108 V208" strokeDasharray="6 5" />
            <circle cx="216" cy="158" r="24" />
            <circle cx="146" cy="126" r="5" />
            <circle cx="216" cy="126" r="5" />
            <circle cx="286" cy="126" r="5" />
          </>
        }
      />
    ),
  },
  {
    id: 'enclosure',
    level: 'HARD',
    tone: 'red',
    sheetRef: 'SHEET 06 · A3 · 1:1',
    eyebrow: 'Snap-fit, no fasteners',
    title: (
      <>
        Enclosure
        <br />
        with lid.
      </>
    ),
    sub: 'A box with a snap-fit lid, two M3 bosses for the PCB, and internal stiffening ribs.',
    prompt: 'Model an enclosure with a snap-fit lid, two M3 bosses, and internal ribs.',
    art: (
      <Art
        dims={
          <>
            <path d="M104 90 H392 M112 90 v-9 M384 90 v-9" />
            <text x="230" y="80">200</text>
            <path d="M78 120 V212 M78 128 h-9 M78 204 h-9" />
            <text x="56" y="170">60</text>
          </>
        }
        sketch={
          <>
            <path d="M104 120 c70-6 150-4 220 0 v60 c-60 6-140 4-220 0 Z" />
            <path d="M140 160 h40 M260 160 h40" />
          </>
        }
        cad={
          <>
            <path d="M104 120 H392 V212 H104 Z" />
            <path d="M104 120 H392" strokeWidth="6" />
            <circle cx="164" cy="166" r="11" />
            <circle cx="332" cy="166" r="11" />
            <path d="M120 212 V186 M228 212 V186 M280 212 V186" />
          </>
        }
      />
    ),
  },
]
