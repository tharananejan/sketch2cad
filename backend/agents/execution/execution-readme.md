# Execution Agent

**Purpose:** Non-LLM executor for one persistent FreeCAD project session.

`POST /execute` receives Python from the Code Generator and sends it to one managed
FreeCAD GUI process through a localhost-only bridge. The first request launches the
GUI session; every following request runs in that same process and changes the same
active document. On every successful request the agent recomputes, saves
`models/freegen.FCStd`, and fits the 3D view. A failure returns the traceback in
the normal response contract for the Error Handling Agent.

The generated code must modify `FreeCAD.ActiveDocument` for follow-up changes. For
example, the first request can create `Bottle_500ml`; a later cap request should get
that object from the active document and add the cap. It must not create a new
document when it is intended to extend the existing bottle.

Run locally after installing dependencies:

```powershell
& <python> -m pip install -r requirements.txt
& <python> -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Example follow-up script contract:

```json
{
  "step_id": 2,
  "code": "import FreeCAD as App\nimport Part\ndoc = App.ActiveDocument\nif doc is None:\n    raise RuntimeError('No active FreeGen document')\ncap = doc.addObject('Part::Feature', 'BottleCap')\ncap.Shape = Part.makeCylinder(16, 12, App.Vector(0, 0, 220))\ndoc.recompute()\nprint('Bottle cap added')\n"
}
```
