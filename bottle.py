import FreeCAD
import Part
from FreeCAD import Vector
import os

def create_and_export_bottle():
    doc_name = "WaterBottle_500ml"
    
    # CORRECTED: Safely check if document exists in the current open documents list
    if doc_name in FreeCAD.listDocuments():
        FreeCAD.closeDocument(doc_name)
        
    doc = FreeCAD.newDocument(doc_name)

    # Define the 2D profile points (Half cross-section in XZ plane)
    points = [
        # --- OUTER SHELL ---
        Vector(0, 0, 0),             # Bottom center
        Vector(15, 0, 0),            # Bottom flat edge
        Vector(20, 0, 0.5),          # Bottom curve start
        Vector(25, 0, 2),
        Vector(29, 0, 5),
        Vector(31.5, 0, 10),
        Vector(32.5, 0, 15),         # Main body start (65mm Diameter)
        Vector(32.5, 0, 160),        # Main body end (elongated for 500ml volume)
        Vector(32.5, 0, 165),        # Shoulder curve start
        Vector(31.5, 0, 170),
        Vector(28, 0, 178),
        Vector(22, 0, 186),
        Vector(16, 0, 192),
        Vector(14, 0, 195),          # Neck base
        Vector(14, 0, 205),          # Neck body
        Vector(15.5, 0, 205),        # Thread ring/bulge start
        Vector(15.5, 0, 208),        # Thread ring/bulge end
        Vector(14, 0, 208),          # Neck upper body
        Vector(14, 0, 220),          # Top lip (Outer)
        
        # --- INNER SHELL (1.5mm Wall Thickness) ---
        Vector(12.5, 0, 220),        # Top lip (Inner)
        Vector(12.5, 0, 208),
        Vector(12.5, 0, 205),
        Vector(12.5, 0, 195),
        Vector(14.5, 0, 191),
        Vector(20.5, 0, 185),
        Vector(26.5, 0, 177),
        Vector(30, 0, 169),
        Vector(31, 0, 165),
        Vector(31, 0, 160),          # Inner body start
        Vector(31, 0, 15),           # Inner body end
        Vector(30, 0, 10.5),
        Vector(27.5, 0, 5.5),
        Vector(23.5, 0, 2.5),
        Vector(19.5, 0, 1.5),        # Inner bottom curve end
        Vector(15, 0, 1.5),          # Inner bottom flat start
        Vector(0, 0, 1.5),           # Inner bottom center
        
        # --- CLOSE LOOP ---
        Vector(0, 0, 0)              # Back to start
    ]

    # Create a polygon wire from the points
    wire = Part.makePolygon(points)
    
    # Convert the closed wire into a face
    face = Part.Face(wire)
    
    # Revolve the face 360 degrees around the Z-axis (0,0,1)
    bottle_solid = face.revolve(Vector(0,0,0), Vector(0,0,1), 360)

    # Add the generated solid to the FreeCAD document
    part_obj = doc.addObject("Part::Feature", "Bottle_500ml")
    part_obj.Shape = bottle_solid

    # Recompute document to apply changes
    doc.recompute()

    # Adjust the view to frame the new bottle perfectly
    if FreeCAD.GuiUp:
        import FreeCADGui
        FreeCADGui.activeDocument().activeView().viewAxometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")
        FreeCADGui.activeDocument().activeView().setDrawStyle("Shaded")

    # Determine export path (Defaults to your Desktop)
    home_dir = os.path.expanduser("~")
    desktop_dir = os.path.join(home_dir, "Desktop")
    
    if os.path.exists(desktop_dir):
        export_path = os.path.join(desktop_dir, "WaterBottle_500ml.step")
    else:
        export_path = os.path.join(home_dir, "WaterBottle_500ml.step")

    # Export the object as a STEP file
    Part.export([part_obj], export_path)
    
    # Print success message in the console
    print(f"\n=========================================")
    print(f" SUCCESS: 500ml Water Bottle Generated!")
    print(f" STEP file saved to: {export_path}")
    print(f"=========================================\n")

# Run the function
create_and_export_bottle()