"""
Legal Contract Risk Analyzer — FastAPI Backend
Entry point. Run: python main.py
"""

import asyncio
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.database import models
from app.database.database import Base, engine

# ----------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified!")
except Exception as e:
    print(f"⚠️ Database startup warning: {e}")

# ----------------------------------------
# APP INIT
# ----------------------------------------

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

# ----------------------------------------
# CORS
# ----------------------------------------

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
            content={
                "detail": f"Internal server error: {exc}",
                "path": request.url.path,
            },
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
        content={
            "detail": f"Internal server error: {exc}",
            "path": request.url.path,
        },
    )
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response

# ----------------------------------------
# ROUTES
# ----------------------------------------

app.include_router(router)

# ----------------------------------------
# STARTUP
# ----------------------------------------

@app.on_event("startup")
async def startup_event():
    """Run initialization on app startup."""
    from app.startup import startup, startup_async
    startup()
    # Schedule async startup tasks in the background so FastAPI can bind immediately.
    asyncio.create_task(startup_async())

# ----------------------------------------
# RUN
# ----------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting app on 0.0.0.0:{port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )