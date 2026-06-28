from fastapi import FastAPI
from app.api.routes import router
import asyncio

app = FastAPI()
app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    from app.database.database import engine
    from app.database.models import Base
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine)),
            timeout=10.0,
        )
        print("✅ DB ready")
    except Exception as e:
        print(f"⚠️ DB warning: {e}")