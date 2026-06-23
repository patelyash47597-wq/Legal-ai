"""
app/startup.py
Initialize backend services on app startup.
Validates environment, preloads models to avoid request timeouts.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def validate_environment():
    """Validate required environment variables."""
    print("\n" + "="*60)
    print("🔧 ENVIRONMENT VALIDATION")
    print("="*60)
    
    issues = []
    
    # Check GROQ_API_KEY
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        issues.append("❌ GROQ_API_KEY not set → AI explanations will fail")
    else:
        print("✅ GROQ_API_KEY is configured")
    
    # Check HF_TOKEN
    hf_token = os.getenv("HF_TOKEN", "").strip()
    if not hf_token:
        issues.append("❌ HF_TOKEN not set → InLegalBERT model download may fail")
    else:
        print("✅ HF_TOKEN is configured")
    
    # Check standard_clauses.json
    if not os.path.exists("data/processed/standard_clauses.json"):
        issues.append("❌ standard_clauses.json not found")
    else:
        print("✅ standard_clauses.json exists")
    
    if issues:
        print("\n⚠️  WARNINGS:")
        for issue in issues:
            print(f"   {issue}")
        print("\n📖 See DEPLOYMENT.md for environment setup instructions")
    
    print("="*60 + "\n")


async def preload_models():
    """Preload models asynchronously to avoid request timeouts."""
    print("🔄 PRELOADING MODELS (this may take 1-2 minutes on first run)...")
    
    try:
        # Preload InLegalBERT
        from app.services.risk_engine import _get_model, _load_standard_data
        
        print("   → Loading InLegalBERT...")
        model = _get_model()
        if model:
            print("   ✅ InLegalBERT loaded successfully")
            
            print("   → Building FAISS indexes...")
            try:
                _load_standard_data("data/processed/standard_clauses.json")
                print("   ✅ FAISS indexes built")
            except Exception as e:
                print(f"   ⚠️  Could not build FAISS indexes: {e}")
        else:
            print("   ⚠️  InLegalBERT unavailable (HF_TOKEN may not be set)")
        
        # Preload spaCy model
        print("   → Loading spaCy model...")
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("   ✅ spaCy model loaded")
        except Exception as e:
            print(f"   ⚠️  Could not load spaCy: {e}")
        
    except Exception as e:
        print(f"   ⚠️  Model preloading incomplete: {e}")
    
    print("✅ Startup complete\n")


def startup():
    """Run all startup tasks."""
    validate_environment()


async def startup_async():
    """Run async startup tasks."""
    await preload_models()
