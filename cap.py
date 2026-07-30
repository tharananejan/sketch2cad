import FreeCAD as App
import Part

# Select the bottle's existing document by name.
doc = App.getDocument("WaterBottle_500ml")
if doc is None:
    raise RuntimeError("WaterBottle_500ml document does not exist. Run bottle.py first.")

App.setActiveDocument(doc.Name)

# Confirm the bottle exists in this same document.
bottle = doc.getObject("Bottle_500ml")
if bottle is None:
    raise RuntimeError("Bottle_500ml was not found in WaterBottle_500ml.")

# Create the cap in the SAME document.
cap = doc.getObject("BottleCap")
if cap is None:
    cap = doc.addObject("Part::Feature", "BottleCap")

cap.Shape = Part.makeCylinder(
    16.0,
    14.0,
    App.Vector(0, 0, 220)
)

doc.recompute()
print("Bottle cap added to WaterBottle_500ml.")