from fastapi import FastAPI

from supervisor_router import router

app = FastAPI(title="Sketch2CAD Supervisor")
app.include_router(router)
