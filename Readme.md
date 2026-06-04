# Sistema de Gestión de Encomiendas

Plataforma web para gestión de envíos con **Django 6.0**, WebSockets en tiempo real, API REST y dashboard interactivo.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6.0.5 + Daphne (ASGI) |
| API | Django REST Framework 3.17 |
| WebSockets | Channels 4.0 + Redis |
| Base de datos | PostgreSQL 15 |
| Cache/WS Layer | Redis 7 |
| Frontend | Bootstrap 5.3 + Font Awesome |
| Auth | JWT (SimpleJWT) + sesión Django |

## Arquitectura

```
                     ┌──────────────────────────────────────┐
                     │            Daphne (ASGI)              │
                     │  ┌──────────┐ ┌────────┐ ┌─────────┐ │
                     │  │ FBV Views│ │DRF API │ │WebSocket│ │
                     │  │(envios/) │ │(api/v1)│ │Consumers│ │
                     └──────┬───────┴────┬────┴─────┬─────┘
                            │            │          │
                  ┌─────────▼────────────▼──────────▼──────┐
                  │          Django ORM + Models           │
                  │  Cliente ─ Ruta ─ Encomienda ─ Hist.   │
                  └───────────────────┬────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
     ┌────────▼────────┐   ┌──────────▼──────────┐   ┌──────▼──────┐
     │   PostgreSQL 15  │   │      Redis 7        │   │   APIs      │
     │   (datos)        │   │  - Cache (15min)    │   │  externas   │
     │                  │   │  - Channel Layer    │   │  (httpx)    │
     └─────────────────┘   └─────────────────────┘   └─────────────┘
```

## Requisitos

- Docker + Docker Compose
- Git

## Inicio rápido

```sh
# 1. Clonar
git clone <repo>
cd encomiendas

# 2. Configurar variables de entorno
cp .env.example .env
# editar .env con tus credenciales

# 3. Levantar servicios
docker compose up -d

# 4. Ejecutar migraciones
docker compose exec web python manage.py migrate

# 5. Crear superusuario
docker compose exec web python manage.py createsuperuser

# 6. Abrir
#    Web:      http://localhost:8000
#    Admin:    http://localhost:8000/admin/
#    API:      http://localhost:8000/api/v1/
#    Docs:     http://localhost:8000/docs/
```

## Comandos útiles

```sh
# Logs en vivo
docker compose logs -f web

# Shell de Django
docker compose exec web python manage.py shell

# Ejecutar tests
docker compose run --rm web pytest -v

# Reconstruir contenedor
docker compose build web
docker compose up -d
```

## Modelos principales

<modelo nombre="Cliente">
  tipo_doc (DNI/RUC/PAS), nro_doc, nombres, apellidos,
  telefono, email, estado, fecha_registro

<modelo nombre="Ruta">
  codigo (ej. LIM-CUS), origen, destino, precio_base,
  dias_entrega, estado

<modelo nombre="Empleado">
  codigo (ej. EMP001), nombres, apellidos, cargo, email,
  telefono, estado, rutas_asignadas

<modelo nombre="Encomienda">
  codigo (ENC-20260604-XXXXXX), descripcion, peso_kg,
  remitente, destinatario, ruta, empleado_registro,
  estado (PE/TR/DE/EN/DV), costo_envio, fechas

<modelo nombre="HistorialEstado">
  encomienda, estado_anterior, estado_nuevo,
  observacion, empleado, fecha_cambio

## API REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/auth/token/` | POST | Obtener JWT |
| `/api/v1/auth/token/refresh/` | POST | Refrescar token |
| `/api/v1/auth/token/blacklist/` | POST | Invalidar refresh |
| `/api/v1/encomiendas/` | GET | Listar (filtrable, paginado) |
| `/api/v1/encomiendas/` | POST | Crear |
| `/api/v1/encomiendas/{id}/` | GET | Detalle con historial |
| `/api/v1/encomiendas/{id}/` | PUT/PATCH | Actualizar |
| `/api/v1/encomiendas/{id}/` | DELETE | Eliminar |
| `/api/v1/encomiendas/{id}/cambiar_estado/` | POST | Cambiar estado |
| `/api/v1/encomiendas/con_retraso/` | GET | Listar con retraso |
| `/api/v1/encomiendas/pendientes/` | GET | Listar pendientes |
| `/api/v1/encomiendas/{id}/historial/` | GET | Historial de cambios |
| `/api/v1/encomiendas/estadisticas/` | GET | Contadores |
| `/api/v1/encomiendas/bulk_create/` | POST | Creación masiva |
| `/api/v1/encomiendas/bulk_estado/` | POST | Cambio estado masivo |
| `/api/v1/clientes/` | GET | Listar clientes |
| `/api/v1/rutas/` | GET | Listar rutas |

### Throttling por operación

| Throttle | Scope | Rate |
|----------|-------|------|
| Anónimo | `anon` | 20/hora |
| Usuario autenticado | `user` | 500/hora |
| Empleado (API general) | `empleado` | 100/minuto |
| Cambio de estado | `cambio_estado` | 30/hora |
| Intento de login | `login_attempt` | 5/minuto |

### Versionado

URL path versioning: `/api/v1/` vs `/api/v2/`. v2 agrega campo `meta` con metadata del serializer.

## WebSockets

| Endpoint | Propósito |
|----------|-----------|
| `ws://host/ws/dashboard/` | Estadísticas en tiempo real |
| `ws://host/ws/encomiendas/` | Notificaciones globales |
| `ws://host/ws/encomiendas/{pk}/` | Detalle de encomienda en vivo |

Autenticación vía JWT en query string: `?token=<access_token>`.

## Tests

```sh
docker compose run --rm web pytest -v
```

30 tests, 2 skipped. Incluye tests de API REST, WebSockets (Channels), autenticación y versionado.

## Variables de entorno (`.env`)

```
DB_NAME=encomiendas
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/1
SECRET_KEY=generar-una-segura
ALLOWED_HOSTS=*
DEBUG=True
```
