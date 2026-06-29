"""
app/startup.py
"""

import os
from dotenv import load_dotenv

load_dotenv()


def validate_environment():
    print("\n" + "="*60)
    print("🔧 ENVIRONMENT VALIDATION")
    print("="*60)

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        print("⚠️  GROQ_API_KEY not set")
    else:
        print("✅ GROQ_API_KEY is configured")

    hf_token = os.getenv("HF_TOKEN", "").strip()
    if not hf_token:
        print("⚠️  HF_TOKEN not set")
    else:
        print("✅ HF_TOKEN is configured")

    print("="*60 + "\n")


def startup():
    validate_environment()


async def startup_async():
    print("🔧 Models will load on first request (lazy loading)")