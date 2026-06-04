# Sistema de Gestión de Encomiendas

Sistema web para gestionar envíos de paquetes, desarrollado con **Django 6.0.5**, **PostgreSQL 15** y **Docker**.

Repositorio: [github.com/RaizaArce/sistema-encomiendas](https://github.com/RaizaArce/sistema-encomiendas)

---

## Goal

Implementar paso a paso el sistema siguiendo las guías del curso, sin desviarse del código de las guías.

## Constraints

- Los códigos deben coincidir exactamente con la guía (solo corregir errores).
- Comentarios explicativos agregados para entender el proyecto.
- Seguir orden punto por punto.

---

## Progreso

### Sesión 02 — Proyecto Base
- Proyecto Django con `startproject encomiendas`, apps `envios`, `clientes`, `rutas`.
- Docker configurado (`Dockerfile` + `docker-compose.yml` con PostgreSQL 15-alpine).
- `.env` con variables de entorno (SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, etc.).
- Superusuario `admin` / `admin123`.
- Subido a GitHub.

### Sesión 03 — Modelos ORM

#### Archivos creados
- **`config/choices.py`** — Enumerados: `EstadoGeneral` (ACTIVO/DE_BAJA), `EstadoEnvio` (PE/TR/DE/EN/DV), `TipoDocumento` (DNI/RUC/PAS).
- **`envios/validators.py`** — 3 validadores: `validar_peso_positivo`, `validar_codigo_encomienda`, `validar_nro_doc_dni`.
- **`envios/querysets.py`** — QuerySets para los 3 modelos.

#### Modelos
| Modelo | Archivo | Detalle |
|--------|---------|---------|
| `Cliente` | `clientes/models.py` | tipo_doc, nro_doc, nombres, apellidos, teléfono, email, dirección, estado, fecha_registro + properties (`nombre_completo`, `esta_activo`, `total_encomiendas_enviadas`) |
| `Ruta` | `rutas/models.py` | codigo, origen, destino, descripción, precio_base, dias_entrega, estado |
| `Empleado` | `envios/models.py` | codigo, nombres, apellidos, cargo, email, teléfono, estado, fecha_ingreso, `rutas_asignadas` (M2M a Ruta) |
| `Encomienda` | `envios/models.py` | codigo, descripcion, peso_kg, volumen_cm3, FKs a Cliente×2/Ruta/Empleado, estado, costo_envio, fechas, observaciones |
| `HistorialEstado` | `envios/models.py` | FK a Encomienda (CASCADE), estado_anterior, estado_nuevo, observacion, FK a Empleado, fecha_cambio |

#### Lógica de negocio en Encomienda
- `clean()` — 3 reglas de validación cruzada (remitente≠destinatario, fecha estimada no pasada, coherencia de fechas).
- `save()` — llama `full_clean()` automáticamente.
- Propiedades: `esta_entregada`, `esta_en_transito`, `dias_en_transito`, `tiene_retraso`, `descripcion_corta`.
- `cambiar_estado()` — actualiza estado + crea HistorialEstado.
- `calcular_costo()` — `precio_base + (peso - 5) × 2.50` si peso > 5 kg.
- `crear_con_costo_calculado()` — classmethod que genera código y fecha auto.

#### Admin
- `envios/admin.py` — `EncomiendaAdmin`, `EmpleadoAdmin`, `HistorialEstadoAdmin`
- `clientes/admin.py` — `ClienteAdmin`
- `rutas/admin.py` — `RutaAdmin`

#### Migraciones
- `clientes.0001_initial`, `rutas.0001_initial`, `envios.0001_initial`
- `envios.0002` (validators en campos), `envios.0003` (M2M rutas_asignadas)
- BD reseteada una vez (DROP SCHEMA public CASCADE) para limpiar conflictos.

#### Commit
`dde5eda` — "Sesión 03: Modelos ORM, validadores, querysets y admin" → push a `main`.

### Sesión 04 — Componentes en Django (URLs, Vistas, Templates, Admin, Auth)

#### Archivos creados
- **`envios/views.py`** — 6 vistas FBV: `dashboard`, `encomienda_lista` (filtros + paginación 15/page), `encomienda_detalle` (historial + modal), `encomienda_crear` (form + empleado logueado), `encomienda_cambiar_estado` (POST + método del modelo), `encomienda_estado_json` (JsonResponse).
- **`envios/views_auth.py`** — 3 vistas de autenticación: `login_view`, `logout_view`, `perfil_view`.
- **`envios/urls.py`** — 9 rutas: dashboard, lista, crear, detalle, cambiar_estado, estado_json, login, logout, perfil.
- **`envios/forms.py`** — `EncomiendaForm` (ModelForm con widgets Bootstrap, filtro clientes/rutas activos, validación remitente≠destinatario).
- **`envios/context_processors.py`** — `estadisticas_globales()` inyecta `nav_activas`, `nav_retraso`, `nav_pendientes` en todos los templates.
- **`templates/base.html`** — Plantilla base con herencia (title, extra_css, content, extra_js), Bootstrap 5.3 + Font Awesome, navbar, messages flash, footer.
- **`templates/navbar.html`** — Navbar responsivo con badges: Dashboard (activas), Encomiendas (retraso en rojo si >0), Nueva Encomienda, usuario + Salir.
- **`templates/envios/dashboard.html`** — 4 tarjetas de estadísticas + tabla últimas 5 encomiendas.
- **`templates/envios/lista.html`** — Búsqueda + filtro por estado + tabla paginada + paginación reutilizable.
- **`templates/envios/detalle.html`** — Info completa + alerta de retraso + historial de estados + modal para cambiar estado.
- **`templates/envios/form.html`** — Layout campo por campo con Bootstrap (código+descripción, remitente+destinatario, ruta+peso+costo).
- **`templates/accounts/login.html`** — Pantalla de login centrada con iconos.
- **`templates/accounts/perfil.html`** — Tabla con datos del usuario autenticado.
- **`templates/partials/stat_card.html`** — Tarjeta de estadística reutilizable con border-color dinámico.
- **`templates/partials/paginacion.html`** — Paginación que conserva filtros q y estado_activo.
- **`static/css/styles.css`** — Variables CSS, badges de color (PE/TR/DE/EN/DV), navbar, cards hover, tablas, formularios, sidebar, animación fadeAlert.
- **`static/js/main.js`** — Tooltips, auto-cerrar alertas, confirmación en botones, filas clickeables.

#### Archivos modificados
- **`config/settings.py`** — `TEMPLATES[0].DIRS`, `STATICFILES_DIRS`, `STATIC_ROOT`, `MEDIA_URL`, `MEDIA_ROOT`, `LOGIN_URL='/login/'`, `LOGIN_REDIRECT_URL='/'`, `LOGOUT_REDIRECT_URL='/login/'`, `SESSION_ENGINE`, `SESSION_COOKIE_AGE=28800`, `SESSION_COOKIE_NAME='encomiendas_session'`, context processor `envios.context_processors.estadisticas_globales`.
- **`config/urls.py`** — `include('envios.urls')`, static/media en DEBUG, títulos admin personalizados.
- **`envios/admin.py`** — `EncomiendaAdmin` con fieldsets + badges color con `format_html`, `list_per_page=20`; `EmpleadoAdmin`; `HistorialEstadoAdmin` con readonly_fields.

#### Correcciones aplicadas
- `LOGIN_URL` cambiado de `/accounts/login/` a `/login/` para usar login_view propio.
- Eliminado `include('django.contrib.auth.urls')` de `config/urls.py` (usa vistas propias).
- Eliminado `templates/registration/` (innecesario).
- Creado helper `_get_empleado()` en `views.py` para evitar error 500 cuando un usuario Django no tiene registro `Empleado` asociado.

### Sesión 05 — Django REST Framework (API)

#### API REST
- **Endpoints**: `/api/v1/auth/token/` (JWT login), `/api/v1/encomiendas/` (CRUD), `/api/v1/clientes/`, `/api/v1/rutas/`.
- **Authentication**: JWT via `rest_framework_simplejwt` con tokens rotados y blacklist.
- **Permissions**: `EsEmpleadoActivo` (solo empleados con `estado=1`), `EsPropietarioOAdmin` (solo dueño o staff en write).
- **Versioning**: URL path (`/api/v1/`, `/api/v2/`). V2 agrega `meta` con `version` y `puede_editar`.
- **Pagination**: `EncomiendaPagination` (15/page, configurable vía `page_size`).
- **Filters**: `EncomiendaFilter` (estado, fechas, ruta, remitente, retraso) + `SearchFilter` + `OrderingFilter`.
- **Throttling**: `LoginRateThrottle` (5/min) en login, `CambioEstadoThrottle` (30/h) en cambios de estado.
- **Exception handler**: `api/exceptions.py` — respuestas uniformes `{error, status_code, message, errors}`.

#### Serializers
| Serializer | Uso |
|-----------|-----|
| `EncomiendaSerializer` | Create/update, con validación cruzada y autogeneración de `codigo` |
| `EncomiendaDetailSerializer` | Retrieve (incluye objetos anidados Cliente, Ruta, historial) |
| `EncomiendaListSerializer` | List (13 campos planos, evita N+1) |
| `EncomiendaBulkSerializer` | Bulk create con errores por índice |
| `EncomiendaV2Serializer` | Version v2 con campos extra |
| `HistorialEstadoSerializer` | Historial de cambios de estado |

#### Vistas extra (ViewSet actions)
- `POST /api/v1/encomiendas/{id}/cambiar_estado/` — Cambia estado y registra historial
- `GET /api/v1/encomiendas/con_retraso/` — Encomiendas con fecha estimada vencida
- `GET /api/v1/encomiendas/pendientes/` — Encomiendas en estado Pendiente
- `GET /api/v1/encomiendas/{id}/historial/` — Historial paginado de cambios
- `GET /api/v1/encomiendas/estadisticas/` — Conteos: activas, tránsito, retraso, entregadas hoy
- `POST /api/v1/encomiendas/bulk_create/` — Creación masiva (vía `EncomiendaBulkSerializer`)
- `POST /api/v1/encomiendas/bulk_estado/` — Cambio de estado masivo por lista de IDs
- `POST /api/v1/auth/token/blacklist/` — Invalidar refresh token

#### Documentación
- Swagger UI: `/api/v1/docs/`
- Redoc: `/api/v1/redoc/`
- Schema OpenAPI 3.0: `/api/v1/schema/`
- Generado con `drf-spectacular`.

#### Optimización N+1
- `get_queryset()` usa `.only()` en `list` + `select_related('empleado_registro')` en `con_relaciones()`.
- `EncomiendaListSerializer` usa `source` plana en vez de serializers anidados.

#### Redis + Caching
- Redis 7-alpine como servicio Docker.
- `django-redis` como backend de caché (15 min TTL).
- `cache_page` removido del ViewSet para evitar datos inconsistentes entre requests.

#### django-silk (profiling)
- Middleware `SilkyMiddleware` (antes de CommonMiddleware).
- Captura el 25% del tráfico, máx 100 requests.
- Requiere autenticación (staff). UI en `/silk/` (solo en DEBUG).

#### Testing (pytest)
- **26 tests, 2 skip, 0 failures** — suite completa en ~21s.
- Framework: `pytest` + `pytest-django` + `factory-boy`.
- Fixtures: `user_admin`, `empleado`, `cliente`, `ruta`, `encomienda`, `token`, `auth_client`.
- Fixture autouse `_test_settings`: sobreescribe throttle rates y remueve SilkMiddleware.
- `conftest.py` con 12 fixtures.
- `api/tests.py` con 7 clases: `TestAuth` (5 tests), `TestEncomiendas` (12 tests), `TestClientes`, `TestRutas`, `TestVersioning`, `TestBulk`, `TestDocs`.

#### Archivos creados/modificados
| Archivo | Cambio |
|---------|--------|
| `api/` | App nueva con urls, permissions, throttles, exceptions, filters, pagination |
| `api/tests.py` | 28 tests de API |
| `conftest.py` | Fixtures de pytest |
| `pytest.ini` | Configuración de pytest |
| `envios/serializers.py` | 6 serializers (Encomienda, Detail, List, Bulk, V2, Historial) |
| `envios/viewsets.py` | EncomiendaViewSet con 8 actions, permisos dinámicos, N+1 optimization |
| `envios/api_auth.py` | Login con HttpOnly cookies + JWT personalizado |
| `config/settings.py` | DRF config, JWT blacklist, Redis cache, silk, exception handler |
| `config/urls.py` | URLs de silk (DEBUG), router API v1/v2 |
| `docker-compose.yml` | Servicio redis:7-alpine |
| `requirements.txt` | django-redis, django-silk, pytest, pytest-django, factory-boy |

#### Estado actual del proyecto
```
26 passed, 2 skipped, 10 warnings in 21s
Schema: 0 errors, 11 warnings (10 type hints, 1 enum collision)
Check: 0 errors, 16 deploy warnings (esperados en desarrollo)
```

### Sesión 06 — WebSockets en Tiempo Real, Daphne ASGI y Throttles por Rol

#### Arquitectura ASGI
- Migración de `runserver` (WSGI) a **Daphne** (ASGI) para servir HTTP + WebSocket en el mismo proceso.
- **`config/asgi.py`** — `ProtocolTypeRouter` con `get_asgi_application()` para HTTP y `URLRouter` para WebSockets.
- **`config/settings.py`** — `daphne` y `channels` agregados a `INSTALLED_APPS`. `ASGI_APPLICATION` apunta a `config.asgi.application`.

#### Channel Layer
- **Producción**: `channels_redis.RedisChannelLayer` con Redis 7 (capacidad 100, expiración 60s).
- **Tests**: `InMemoryChannelLayer` (detectado automáticamente por `pytest` en `sys.modules`).
- **`redis.conf`** — Configuración personalizada: `maxmemory 256mb`, política `allkeys-lru`, RDB persistence.

#### WebSocket Consumers (`envios/consumers.py`)
| Consumer | Ruta | Propósito |
|----------|------|-----------|
| `DashboardConsumer` | `ws/dashboard/` | Envía estadísticas iniciales y actualizaciones en tiempo real |
| `EncomiendaConsumer` | `ws/encomiendas/` | Notificaciones globales de cambios de estado |
| `EncomiendaDetalleConsumer` | `ws/encomiendas/{pk}/` | Detalle de encomienda en vivo |

- Todos verifican autenticación (`close(code=4001)` si no).
- `EncomiendaConsumer` acepta mensajes `ping`, `solicitar_stats` y `suscribir_encomienda`.

#### Autenticación WebSocket (`channels_middleware.py`)
- **`JWTAuthMiddleware`** — Extrae JWT del query string `?token=<access_token>` y autentica al usuario.
- **`JWTAuthMiddlewareStack`** — Compone `JWTAuthMiddleware(AuthMiddlewareStack(inner))` para soportar sesión Django + JWT.
- Maneja `InvalidToken`, `TokenError` y `User.DoesNotExist` devolviendo `AnonymousUser`.

#### Notificaciones desde el Modelo (`envios/models.py`)
- `Encomienda.cambiar_estado()` ahora llama a `_notificar_websocket()` después de cada cambio.
- Envía 3 mensajes por canal:
  1. `encomiendas_global` — feed de actividad general
  2. `encomienda_{pk}` — detalle específico
  3. `dashboard` — estadísticas actualizadas (`dashboard_actualizar`)
- Usa `async_to_sync(channel_layer.group_send)` para compatibilidad síncrona.

#### Throttles por Rol (`api/throttles.py`)
| Throttle | Scope | Rate |
|----------|-------|------|
| `EmpleadoRateThrottle` | `empleado` | 100/minuto (API general) |
| `CambioEstadoThrottle` | `cambio_estado` | 30/hora (cambios de estado) |

- `EmpleadoRateThrottle` asignado al `EncomiendaViewSet` completo.
- `CambioEstadoThrottle` asignado solo a la acción `cambiar_estado`.
- Rates configurados en `DEFAULT_THROTTLE_RATES` de DRF.

#### Vistas Asíncronas (`envios/views_async.py`, `envios/async_services.py`)
- **`dashboard_stats_async()`** — Usa `asyncio.gather` con consultas ORM asíncronas (`.acount()`, `.alist()`).
- **`async_services.py`** — Integración con API externa de transportista (`httpx.AsyncClient`), verificación batch con timeouts, marcado automático de entregas.

#### Web Frontend
- **Dashboard** (`templates/envios/dashboard.html`):
  - WebSocket `DashboardWebSocket` con auto-reconexión (backoff exponencial, máx 30s, 10 intentos).
  - Feed de actividad en tiempo real con últimos 50 eventos.
  - Toast notifications con Bootstrap para cada cambio de estado.
  - Contadores de estadísticas con animación `scale(1.4)`.
  - Protocolo dinámico `ws://` / `wss://` según la página.
- **Navbar** (`templates/navbar.html`):
  - Nombre de usuario convertido a dropdown con enlaces a Administración (staff), Mi Perfil y Salir.
- **Detalle** — WebSocket por encomienda para updates en vivo.

#### Orquestación (docker-compose.yml)
- Comando de `web` cambiado a: `collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application`.
- Redis: `healthcheck` con `redis-cli ping`, `redis.conf` montado como volumen.

#### Testing
- **`envios/tests/test_consumers.py`** — 4 tests asíncronos con `WebsocketCommunicator`:
  - `test_conexion_sin_autenticacion` — código 4001
  - `test_conexion_autenticada` — conexión exitosa + mensaje de stats
  - `test_ping_pong` — respuesta a ping
  - `test_notificacion_via_channel_layer` — grupo `dashboard` recibe `dashboard_actualizar`
- **`conftest.py`** — Agregado `'empleado'` al override de `DEFAULT_THROTTLE_RATES`.
- Total: **30 passed, 2 skipped** (se agregaron 4 tests de WebSocket).

#### Otros cambios
- **`envios/urls.py`** — Ruta `health/` para health check.
- **`envios/views.py`** — Vista `health_check` que verifica Redis + DB.
- **`staticfiles/`** — Agregado a `.gitignore` (generado por `collectstatic`).
- Corrección: import faltante `AnonymousUser` en `channels_middleware.py`.

---

## Decisiones Técnicas

| Decisión | Razón |
|----------|-------|
| `python:3.12-slim` | Django 6.0.5 requiere Python ≥ 3.12 |
| Sin `version: '3.9'` en compose | Obsoleto en Docker Compose v2+ |
| `PROTECT` en FKs de negocio | Evita borrado accidental de clientes/empleados/rutas |
| `CASCADE` en HistorialEstado | El historial se borra con la encomienda |
| `validar_nro_doc_dni` definido sin usar | Disponible para futuro, la guía lo pide |
| Vistas basadas en funciones (FBV) | Claridad y facilidad de aprendizaje, como indica la guía |
| Login propio vs `django.contrib.auth.urls` | Evita depender de templates built-in que no personalizamos |
| `_get_empleado()` helper | Evita error 500 si el usuario no tiene Empleado asociado; muestra mensaje claro |
| `form.html` campo por campo | Control total con Bootstrap en vez de `{{ form.as_p }}` |
| Paginación pasa `q` y `estado_activo` en contexto | Los filtros se conservan al navegar entre páginas |
| Daphne en vez de runserver | Soporta WebSockets + HTTP simultáneamente |
| Channel Layer con Redis | Escalable para múltiples workers WebSocket |
| `InMemoryChannelLayer` en tests | Evita dependencia de Redis en CI |
| `_notificar_websocket()` en el modelo | Single source of truth: todo cambio de estado notifica automáticamente |
| JWT en query string de WebSocket | Compatible con `WebSocket()` del navegador (no soporta headers) |
| Throttle `empleado` a 100/min | Balance entre capacidad y abuso; navbar dropdown en vez de texto estático |

## Archivos Relevantes

| Archivo | Descripción |
|---------|-------------|
| `config/settings.py` | Configuración Django (DB, templates, static/media, auth, sesiones) |
| `config/urls.py` | Enrutador principal |
| `config/asgi.py` | ProtocolTypeRouter para HTTP + WebSocket |
| `config/choices.py` | Enumerados del sistema |
| `clientes/models.py` | Modelo Cliente + properties + manager |
| `rutas/models.py` | Modelo Ruta + manager |
| `envios/models.py` | Modelos Empleado, Encomienda, HistorialEstado + lógica + notificaciones WS |
| `envios/validators.py` | 3 validadores personalizados |
| `envios/querysets.py` | QuerySets para los 3 modelos |
| `envios/views.py` | 6 vistas FBV (dashboard, CRUD, cambio estado) + health_check |
| `envios/views_auth.py` | 3 vistas de autenticación |
| `envios/views_async.py` | Vistas asíncronas con asyncio.gather |
| `envios/async_services.py` | Integración asíncrona con API de transportista |
| `envios/consumers.py` | 3 WebSocket consumers (Dashboard, Encomienda, Detalle) |
| `envios/routing.py` | Rutas WebSocket |
| `envios/urls.py` | Rutas del sistema |
| `envios/forms.py` | EncomiendaForm (ModelForm con Bootstrap) |
| `envios/context_processors.py` | Estadísticas globales para el navbar |
| `envios/admin.py` | Admin con fieldsets, badges, list_per_page |
| `clientes/admin.py` | Admin de Cliente |
| `rutas/admin.py` | Admin de Ruta |
| `channels_middleware.py` | JWTAuthMiddleware para WebSockets |
| `api/throttles.py` | EmpleadoRateThrottle, CambioEstadoThrottle, LoginRateThrottle |
| `templates/base.html` | Plantilla base (Bootstrap 5.3, Font Awesome, navbar, footer) |
| `templates/navbar.html` | Navbar con dropdown de usuario |
| `templates/envios/*.html` | Dashboard (con WS feed), listado, detalle, formulario |
| `templates/accounts/*.html` | Login, perfil |
| `templates/partials/*.html` | stat_card, paginacion |
| `static/css/styles.css` | Estilos personalizados (badges, navbar, cards, tablas) |
| `static/js/main.js` | Tooltips, alertas, confirmación, filas clickeables |
| `Dockerfile` | python:3.12-slim |
| `docker-compose.yml` | web (Daphne) + PostgreSQL 15 + Redis 7 |
| `redis.conf` | Configuración de Redis (256MB, LRU, RDB) |
| `.env` | Variables de entorno |

---

## Comandos Útiles

```bash
# Iniciar contenedores
docker compose up -d

# Ver estado
docker compose ps

# Logs en vivo
docker compose logs -f web

# Acceder al shell de Django
docker compose exec web python manage.py shell

# Crear migraciones
docker compose exec web python manage.py makemigrations

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario (si no existe)
docker compose exec web python manage.py createsuperuser

# Ejecutar tests
docker compose run --rm web pytest -v

# Reconstruir imagen
docker compose build web
docker compose up -d

# Admin Django
# http://localhost:8000/admin/  — usuario: admin / contraseña: admin123

# Sistema de Encomiendas
# http://localhost:8000/         — Dashboard (requiere login)
# http://localhost:8000/login/   — Página de inicio de sesión

# Documentación API
# http://localhost:8000/docs/    — Swagger UI
# http://localhost:8000/redoc/   — Redoc
```

> **Nota:** Cada usuario de Django debe tener un registro `Empleado` con el mismo email en `/admin/envios/empleado/` para poder crear encomiendas o cambiar estados. Si no, verá un mensaje de error claro en lugar de un crash.
