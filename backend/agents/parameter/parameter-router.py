from fastapi import FastAPI, HTTPException
from schemas.request import AnalyzeRequest
from schemas.response import AnalyzeResponse
from services.analyzer import analyze_prompt
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Sketch2CAD Parameter Agent API",
    description="LLM-driven parameter extraction and complexity analysis.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        response = analyze_prompt(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("parameter-router:app", host="127.0.0.1", port=8002, reload=True)
