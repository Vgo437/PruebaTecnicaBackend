async def test_health(client):
    """El endpoint /health debe responder con estado ok."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_ready(client):
    """El endpoint /health/ready debe confirmar que la conexion a la BD funciona."""
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}