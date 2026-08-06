from sqlalchemy import text
from app.db.session import get_db
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession


app = FastAPI(title="API de Solicitudes Institucionales para prueba tecnica", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}