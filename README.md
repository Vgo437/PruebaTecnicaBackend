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

Cada capa solo se comunica con la inmediatamente inferior, permitiendo testear la lógica de negocio sin depender del framework HTTP, y aislar cambios de motor de BD en `repositories/`. La capa `services/` no depende de FastAPI: lanza excepciones de dominio propias en lugar de `HTTPException` (ver "Decisiones técnicas").

## Estructura del proyecto

```
PruebaTecnicaBackend/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point, middlewares, exception handlers
│   │   ├── api/solicitud.py     # Endpoints
│   │   ├── core/                # config, logging, middleware, exceptions, domain_exceptions
│   │   ├── models/solicitud.py  # Modelo SQLAlchemy
│   │   ├── schemas/solicitud.py # Schemas Pydantic + catalogos (Enum)
│   │   ├── repositories/        # Acceso a datos
│   │   ├── services/            # Logica de negocio (excepciones de dominio propias)
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

> **Nota:** el comando de arranque del servicio `api` no incluye `--reload`, pensado para una entrega evaluable estable. Para desarrollo activo con recarga automática, se puede agregar `--reload` al `command` del servicio `api` en `docker-compose.yml`.

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
Incluye 12 pruebas: los 11 casos funcionales básicos (creación, validaciones, duplicados, consultas, transiciones de estado, health checks) más una prueba de concurrencia real con `asyncio.gather`, que dispara dos creaciones simultáneas con el mismo `identificador_externo` para validar el `UNIQUE constraint` bajo una condición de carrera real.

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

**Duplicados a nivel de BD.** `identificador_externo` tiene `UNIQUE` en PostgreSQL, no solo validación en código — evita condiciones de carrera entre un `SELECT` de verificación y el `INSERT`. El `IntegrityError` resultante se traduce a `409`. Esto se valida con una prueba de concurrencia real (`asyncio.gather`), no solo con el caso secuencial.

**Excepciones de dominio en la capa de servicio.** `SolicitudService` no depende de FastAPI: en lugar de lanzar `HTTPException`, lanza excepciones propias del dominio (`SolicitudNoEncontrada`, `IdentificadorDuplicado`, `TransicionInvalida`, definidas en `core/domain_exceptions.py`). Un exception handler centralizado (`domain_exception_handler`) las traduce a los códigos HTTP correspondientes (404, 409, 422). Esto mantiene la lógica de negocio independiente del framework web y facilita testear el `service` de forma aislada.

**Manejo de excepciones en capas:**
1. Errores de negocio (excepciones de dominio → `HTTPException`: 404/409/422) → mensajes específicos.
2. Validación de entrada (`RequestValidationError`) → mensajes legibles en español, sin exponer la estructura interna de Pydantic.
3. Infraestructura (`DBAPIError` y `OSError`, cubriendo tanto errores traducidos por SQLAlchemy como fallos de red/DNS) → `503` genérico.
4. No previstos (`Exception`) → `500` genérico. El detalle técnico completo solo se registra en logs, nunca se envía al cliente.

**Logging JSON y trazabilidad end-to-end.** Cada request registra timestamp, nivel, servicio, `request_id`, método, endpoint, status y duración. El consumidor genera un `request_id` por operación y lo envía como header `X-Request-ID`; el middleware de la API reutiliza ese `request_id` si ya viene en la petición entrante, en lugar de generar uno nuevo siempre. Esto permite correlacionar, con un único identificador, los logs de una misma operación a través de ambos servicios. Las rutas `/health` y `/health/ready` se excluyen del logging del middleware para evitar ruido, ya que Docker las invoca automáticamente cada pocos segundos como parte del healthcheck.

**Healthcheck de disponibilidad real.** El healthcheck de Docker Compose para el servicio `api` apunta a `/health/ready` (no solo `/health`), verificando que la conexión a PostgreSQL esté realmente disponible antes de marcar el servicio como sano. Esto es importante porque el `consumer` depende de `api: condition: service_healthy` — con este cambio, el consumidor solo arranca cuando la API puede realmente atender solicitudes.

**Base de datos de test separada (`db_test`)**, aislada de la de desarrollo, para pruebas reproducibles sin riesgo de borrar datos reales.

**Consumidor con reintentos selectivos.** Solo reintenta (backoff exponencial) errores temporales: timeouts, fallos de conexión, `5xx`. Los `4xx` no se reintentan, ya que reintentar los mismos datos inválidos no cambia el resultado.

## Limitaciones y mejoras futuras

**Limitaciones actuales:**
- No se implementó paginación en `GET /solicitudes`. Con el volumen de datos de esta prueba no representa un problema, pero en producción con muchos registros podría afectar el rendimiento.
- El consumidor usa una lista de solicitudes de prueba y parámetros de reintento (timeout, número de intentos) definidos en código, en lugar de leer estos valores desde variables de entorno o un archivo externo.
- No se implementó autenticación ni autorización en la API (no formaba parte del alcance del enunciado).
- Los tests cubren los endpoints de extremo a extremo contra una base de datos real de test, incluyendo un caso de concurrencia real, pero no incluyen pruebas unitarias aisladas de `service`/`repository` con mocks.

**Mejoras futuras propuestas:**
- Paginación (`page`, `page_size`) y ordenamiento configurable en `GET /solicitudes`.
- Endpoint de resumen/conteo por estado, útil para un futuro dashboard.
- Historial de cambios de estado en una tabla separada, para auditoría más detallada.
- Externalizar la configuración del consumidor (casos de prueba, reintentos, timeouts) a variables de entorno.
- Autenticación (API Key o JWT) antes de un despliegue real, según lo propuesto en `docs/Propuesta_Arquitectura_AWS.pdf`.

## Documentación adicional

- Propuesta de arquitectura AWS: [`docs/Propuesta_Arquitectura_AWS.pdf`](docs/Propuesta_Arquitectura_AWS.pdf)
- Flujograma de arquitectura: [`docs/Flujograma_AWS.png`](docs/Flujograma_AWS.png)
- Colección de Postman (ejemplos de consumo): [`docs/PruebaTecnicaBanckend.postman_collection.json`](docs/PruebaTecnicaBanckend.postman_collection.json)
- Logs de una ejecución de ejemplo: [`docs/logs_ejemplo.log`](docs/logs_ejemplo.log)
- Swagger interactivo: `/docs` con el proyecto en ejecución