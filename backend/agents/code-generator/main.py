from fastapi import FastAPI
from code_generator_router import router, app as code_gen_app

app = code_gen_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
