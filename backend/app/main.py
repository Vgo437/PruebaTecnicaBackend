from fastapi import FastAPI

app = FastAPI(title="API de Solicitudes Institucionales", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}