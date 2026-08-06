from sqlalchemy import text
from app.db.session import get_db
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.solicitudes import router


app = FastAPI(title="API de Solicitudes Institucionales para prueba tecnica", version="1.0.0")
app.include_router(router)

@app.get("/health")
async def health():
    """Consulta el estado de la API"""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Consulta que la conexion a la bd esta funcionando"""
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}