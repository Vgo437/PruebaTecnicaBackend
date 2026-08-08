import pytest
import asyncio


async def test_crear_solicitud_valida(client):
    """Debe crear una solicitud exitosamente con datos validos."""
    payload = {
        "identificador_externo": "TICKET-TEST-001",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Vanessa Giraldo",
        "correo_electronico": "vane@gmail.com",
        "descripcion": "Prueba de creacion con datos validos",
        "prioridad": "alta",
    }
    response = await client.post("/solicitudes", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["identificador_externo"] == "TICKET-TEST-001"
    assert data["estado"] == "recibida"
    assert "id" in data
    assert "fecha_creacion" in data


async def test_rechazar_datos_invalidos(client):
    """Debe rechazar una solicitud con correo invalido/incompleto"""

    payload = {
        "identificador_externo": "TIKECT-TEST-002",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Ana",
        "correo_electronico": "vanne@gmail",
        "descripcion": "Prueba de correo incompleto",
        "prioridad": "baja",
    }
    response = await client.post("/solicitudes", json=payload)

    assert response.status_code == 422


async def test_rechazar_campo_obligatorio_faltante(client):
    """Debe rechazar una solicitud sin el campo obligatorio correo_electronico."""

    payload = {
        "identificador_externo": "TICKER-TEST-003",
        "tipo_solicitud": "academica",
        "nombre_solicitante": "vanessa",
        "descripcion": "Prueba con campo faltante de correo",
        "prioridad": "baja",
    }
    response = await client.post("/solicitudes", json=payload)

    assert response.status_code == 422


async def test_rechazar_identificador_duplicado(client):
    """Debe rechazar una segunda solicitud con el mismo identificador_externo."""

    payload = {
        "identificador_externo": "TICKER-TEST-004",
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Paola",
        "correo_electronico": "paola@gmail.com",
        "descripcion": "Primera solicitud con doble ejecucion",
        "prioridad": "media",
    }

    primera_respuesta = await client.post("/solicitudes", json=payload)
    assert primera_respuesta.status_code == 201

    segunda_respuesta = await client.post("/solicitudes", json=payload)
    assert segunda_respuesta.status_code == 409


async def test_consultar_solicitud_existente(client):
    """Debe devolver el detalle de una solicitud que existe."""

    payload = {
        "identificador_externo": "TICKET-TEST-005",
        "tipo_solicitud": "administrativa",
        "nombre_solicitante": "Laura Gomez",
        "correo_electronico": "laura@example.com",
        "descripcion": "Prueba de consulta, primero hace el post y con el mismo id hace el get",
        "prioridad": "media",
    }
    creada = await client.post("/solicitudes", json=payload)
    id_creado = creada.json()["id"]

    response = await client.get(f"/solicitudes/{id_creado}")

    assert response.status_code == 200
    assert response.json()["id"] == id_creado
    assert response.json()["identificador_externo"] == "TICKET-TEST-005"


async def test_consultar_solicitud_inexistente(client):
    """Debe devolver 404 al consultar un ID que no existe."""

    response = await client.get("/solicitudes/999999")

    assert response.status_code == 404


async def test_actualizar_estado_transicion_valida(client):
    """Debe actualizar el estado cuando la transicion es valida."""

    payload = {
        "identificador_externo": "TICKET-TEST-006",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Ana",
        "correo_electronico": "ann@gmail.com",
        "descripcion": "Prueba de actualizacion de estado",
        "prioridad": "alta",
    }
    creada = await client.post("/solicitudes", json=payload)
    id_creado = creada.json()["id"]

    response = await client.patch(
        f"/solicitudes/{id_creado}/estado",
        json={"estado": "en_proceso"},
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "en_proceso"


async def test_actualizar_estado_transicion_invalida(client):
    """Debe rechazar una transicion de estado no permitida."""

    payload = {
        "identificador_externo": "TICKET-TEST-007",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "ana perez",
        "correo_electronico": "annpz@gmail.com",
        "descripcion": "Prueba de transicion invalida, no puede pasar de recibida a completa",
        "prioridad": "baja",
    }
    creada = await client.post("/solicitudes", json=payload)
    id_creado = creada.json()["id"]

    # Intenta pasar de "recibida" directo a "completada" (no permitido)
    response = await client.patch(
        f"/solicitudes/{id_creado}/estado",
        json={"estado": "completada"},
    )

    assert response.status_code == 422


async def test_actualizar_estado_solicitud_inexistente(client):
    """Debe devolver 404 al intentar actualizar el estado de un ID que no existe."""

    response = await client.patch(
        "/solicitudes/999999/estado",
        json={"estado": "en_proceso"},
    )

    assert response.status_code == 404


async def test_concurrencia_identificador_duplicado(client):
    """Debe garantizar que, ante dos creaciones simultaneas con el mismo
    identificador_externo, solo una tenga exito (201) y la otra falle (409),
    incluso cuando ambas requests se disparan al mismo tiempo."""

    payload = {
        "identificador_externo": "TICKET-TEST-010",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Usuario concurrente",
        "correo_electronico": "concurrente123@gmail.com",
        "descripcion": "Prueba de condicion de carrera real",
        "prioridad": "alta",
    }

    respuestas = await asyncio.gather(
        client.post("/solicitudes", json=payload),
        client.post("/solicitudes", json=payload),
        return_exceptions=True,
    )

    codigos = sorted(r.status_code for r in respuestas)

    assert codigos == [201, 409]