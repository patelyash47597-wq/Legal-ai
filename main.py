"""
Legal Contract Risk Analyzer — FastAPI Backend
"""

import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router

app = FastAPI(
    title="Legal Contract Risk Analyzer",
    description="AI-powered legal contract risk analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

ALLOWED_ORIGINS = [
    "https://legal-ai-fronted-sbug.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    origin = request.headers.get("origin")
    try:
        response = await call_next(request)
    except Exception as exc:
        response = JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {exc}", "path": request.url.path},
        )
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    elif origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}", "path": request.url.path},
    )
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    from app.database.database import engine
    from app.database.models import Base
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine)),
            timeout=30.0,
        )
        print("✅ DB ready")
    except asyncio.TimeoutError:
        print("⚠️ DB init timed out — continuing anyway")
    except Exception as e:
        print(f"⚠️ DB warning: {e}")

    from app.startup import startup, startup_async
    startup()
    asyncio.create_task(startup_async())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)