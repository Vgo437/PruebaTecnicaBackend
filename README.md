# API de Solicitudes Institucionales

Prueba técnica Backend Developer — solución backend contenerizada para la gestión de solicitudes institucionales, con servicio consumidor simulado y arquitectura preparada para despliegue en AWS.

## Arquitectura

Tres servicios orquestados con Docker Compose:

- **`backend/`**: API REST (FastAPI) en arquitectura de capas (rutas → servicios → repositorios → BD), con PostgreSQL.
- **`consumer/`**: simula un sistema externo, enviando solicitudes y consultando su estado, con reintentos ante fallos temporales.
- **`db`** / **`db_test`**: PostgreSQL para desarrollo y para pruebas automatizadas, respectivamente.

```
┌─────────────┐   HTTP    ┌─────────────┐   SQLAlchemy   ┌─────────────┐
│  consumer   │ ─────────>│     api     │───────────────>│   db (pg)   │
└─────────────┘           └─────────────┘                └─────────────┘
```

**Flujo interno de la API:**
```
api/ (rutas) → services/ (negocio) → repositories/ (datos) → models/ (SQLAlchemy)
```

Cada capa solo se comunica con la inmediatamente inferior, permitiendo testear la lógica de negocio sin depender del framework HTTP, y aislar cambios de motor de BD en `repositories/`.

## Estructura del proyecto

```
PruebaTecnicaBackend/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point, middlewares, exception handlers
│   │   ├── api/solicitud.py     # Endpoints
│   │   ├── core/                # config, logging, middleware, exceptions
│   │   ├── models/solicitud.py  # Modelo SQLAlchemy
│   │   ├── schemas/solicitud.py # Schemas Pydantic + catalogos (Enum)
│   │   ├── repositories/        # Acceso a datos
│   │   ├── services/            # Logica de negocio
│   │   └── db/                  # base.py, session.py
│   ├── alembic/                 # Migraciones
│   ├── tests/                   # conftest.py, test_solicitud.py, test_health.py
│   ├── Dockerfile
│   └── requirements.txt
├── consumer/
│   ├── app/                     # main.py, client.py (httpx + tenacity)
│   └── Dockerfile
├── docs/
│   ├── Propuesta_Arquitectura_AWS.pdf
│   ├── Flujograma_AWS.png
│   ├── PruebaTecnicaBanckend.postman_collection.json
│   └── logs_ejemplo.log
├── docker-compose.yml
├── .env.example
└── README.md
```

**Convención de nombres:** términos técnicos en inglés (`api`, `core`, `models`, `schemas`, `services`, `repositories`) por ser universales de la arquitectura; términos de dominio en español (`solicitud`, `estado`, `prioridad`) por reflejar el vocabulario del enunciado.

## Tecnologías

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy (async) · Alembic · PostgreSQL 16 · httpx · tenacity · python-json-logger · pytest / pytest-asyncio · Docker / Docker Compose

## Variables de entorno

`.env.example` documenta lo que debe configurarse manualmente:

| Variable | Descripción |
|---|---|
| `DB_USER` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Contraseña de PostgreSQL |
| `DB_NAME` | Nombre de la base de datos de desarrollo |

```bash
cp .env.example .env
```

**Generadas automáticamente por Docker Compose** (no requieren configuración manual):

| Variable | Se construye como | Servicio |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}` | `api` |
| `DATABASE_URL_TEST` | igual, apuntando a `db_test` | `api` (tests) |
| `API_URL` | `http://api:8000` (fijo) | `consumer` |

## Cómo ejecutar

```bash
git clone https://github.com/Vgo437/PruebaTecnicaBackend.git
cd PruebaTecnicaBackend
cp .env.example .env
docker compose up --build
```

Esto levanta `db`, `db_test`, `api` (aplicando las migraciones automáticamente antes de iniciar) y `consumer` (envía un lote de solicitudes de prueba y finaliza).

Verificar:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

Swagger: `http://localhost:8000/docs`

**Pruebas automatizadas:**
```bash
docker compose exec api pytest -v
```

**Consumidor manual** (para volver a ejecutarlo bajo demanda):
```bash
docker compose run --rm consumer
```

**Detener:**
```bash
docker compose down        # conserva datos
docker compose down -v     # elimina también los volúmenes
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/solicitudes` | Crea una nueva solicitud |
| `GET` | `/solicitudes` | Lista con filtros por `estado`, `tipo_solicitud`, `prioridad` |
| `GET` | `/solicitudes/{id}` | Consulta una solicitud específica |
| `PATCH` | `/solicitudes/{id}/estado` | Actualiza el estado |
| `GET` | `/health` | Disponibilidad de la API |
| `GET` | `/health/ready` | Conexión con PostgreSQL |

> No se implementó `DELETE` — ver "Decisiones técnicas".

**Catálogos:**

| Campo | Valores |
|---|---|
| `tipo_solicitud` | `acceso_plataforma`, `soporte_tecnico`, `academica`, `administrativa` |
| `estado` | `recibida`, `en_proceso`, `completada`, `rechazada` |
| `prioridad` | `baja`, `media`, `alta` |

## Decisiones técnicas

**Sin DELETE.** El dominio exige trazabilidad completa; eliminar una solicitud perdería el historial. El ciclo de vida se gestiona vía `estado`, donde `rechazada` cumple el rol de "descarte" sin perder el registro.

**`estado` fuera de `SolicitudCreate`.** Toda solicitud nace en `recibida`. Si el cliente pudiera enviar `estado`, podría crear solicitudes "ya resueltas" sin pasar por el proceso real.

**Transiciones de estado restringidas:**
```
recibida → en_proceso | rechazada
en_proceso → completada | rechazada
completada / rechazada → (finales)
```
Una transición no permitida devuelve `422`.

**Duplicados a nivel de BD.** `identificador_externo` tiene `UNIQUE` en PostgreSQL, no solo validación en código — evita condiciones de carrera entre un `SELECT` de verificación y el `INSERT`. El `IntegrityError` resultante se traduce a `409`.

**Manejo de excepciones en capas:**
1. Errores de negocio (`HTTPException`: 404/409/422) → mensajes específicos.
2. Validación de entrada (`RequestValidationError`) → mensajes legibles en español, sin exponer la estructura interna de Pydantic.
3. Infraestructura (`DBAPIError` y `OSError`, cubriendo tanto errores traducidos por SQLAlchemy como fallos de red/DNS) → `503` genérico.
4. No previstos (`Exception`) → `500` genérico. El detalle técnico completo solo se registra en logs, nunca se envía al cliente.

**Logging JSON.** Cada request registra timestamp, nivel, servicio, `request_id` (también como header `X-Request-ID`), método, endpoint, status y duración. Las rutas `/health` y `/health/ready` se excluyen del logging del middleware para evitar ruido, ya que Docker las invoca automáticamente cada pocos segundos como parte del healthcheck.

**Base de datos de test separada (`db_test`)**, aislada de la de desarrollo, para pruebas reproducibles sin riesgo de borrar datos reales.

**Consumidor con reintentos selectivos.** Solo reintenta (backoff exponencial) errores temporales: timeouts, fallos de conexión, `5xx`. Los `4xx` no se reintentan, ya que reintentar los mismos datos inválidos no cambia el resultado.

## Limitaciones y mejoras futuras

**Limitaciones actuales:**
- No se implementó paginación en `GET /solicitudes`. Con el volumen de datos de esta prueba no representa un problema, pero en producción con muchos registros podría afectar el rendimiento.
- El consumidor usa una lista de solicitudes de prueba definida en código, en lugar de leer los casos desde un archivo externo.
- No se implementó autenticación ni autorización en la API (no formaba parte del alcance del enunciado).
- Los tests cubren los endpoints de extremo a extremo contra una base de datos real de test, pero no incluyen pruebas unitarias aisladas de `service`/`repository` con mocks.

**Mejoras futuras propuestas:**
- Paginación (`page`, `page_size`) y ordenamiento configurable en `GET /solicitudes`.
- Endpoint de resumen/conteo por estado, útil para un futuro dashboard.
- Historial de cambios de estado en una tabla separada, para auditoría más detallada.
- Externalizar la configuración del consumidor (casos de prueba, reintentos, timeouts).
- Autenticación (API Key o JWT) antes de un despliegue real, según lo propuesto en `docs/Propuesta_Arquitectura_AWS.pdf`.

## Documentación adicional

- Propuesta de arquitectura AWS: [`docs/Propuesta_Arquitectura_AWS.pdf`](docs/Propuesta_Arquitectura_AWS.pdf)
- Flujograma de arquitectura: [`docs/Flujograma_AWS.png`](docs/Flujograma_AWS.png)
- Colección de Postman (ejemplos de consumo): [`docs/PruebaTecnicaBanckend.postman_collection.json`](docs/PruebaTecnicaBanckend.postman_collection.json)
- Logs de una ejecución de ejemplo: [`docs/logs_ejemplo.log`](docs/logs_ejemplo.log)
- Swagger interactivo: `/docs` con el proyecto en ejecución