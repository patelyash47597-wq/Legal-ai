"""
Legal Contract Risk Analyzer — FastAPI Backend
Entry point. Run: python main.py
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# ----------------------------------------
# CORS
# ----------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------
# ROUTES
# ----------------------------------------

app.include_router(router)

# ----------------------------------------
# RUN
# ----------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )