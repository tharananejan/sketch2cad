import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

app = FastAPI(
    title="Sketch2CAD Parameter Checking Agent",
    description="Interactive dialogue agent for determining CAD shape parameters.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount the static directory for the UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # When running directly, ensure you are in a directory where the module path makes sense,
    # or run using: uvicorn main:app --reload from inside the parameter directory.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
