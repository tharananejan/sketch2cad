# Execution Agent

This agent executes generated code in a persistent FreeCAD GUI session.

## What it does
- The Execution Agent acts as a bridge between the FreeGen system and FreeCAD. 
- It receives Python code from other agents. 
- It runs this code inside a real FreeCAD application window. 
- It captures any printed output. 
- It catches any errors that occur during execution. 
- It reports the success or failure of the execution back to the caller.
- It ensures that all code runs on the same persistent 3D model document.

## How it does it
- The agent exposes a FastAPI server with an `/execute` endpoint.
- When it receives code, it locates the local FreeCAD executable on the system.
- **It automatically launches FreeCAD if it is not already running.**
- It starts FreeCAD using a custom generated macro.
- This macro runs a socket server inside FreeCAD.
- The agent connects to this internal socket bridge via TCP.
- It sends the Python code payload over the socket to FreeCAD.
- FreeCAD executes the code on the active document.
- FreeCAD sends back the status, standard output, or error stack trace.
- The agent parses this response and returns it as a standardized JSON response.
