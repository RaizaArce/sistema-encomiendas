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

## Archivos Relevantes

| Archivo | Descripción |
|---------|-------------|
| `config/settings.py` | Configuración Django (DB, templates, static/media, auth, sesiones) |
| `config/urls.py` | Enrutador principal |
| `config/choices.py` | Enumerados del sistema |
| `clientes/models.py` | Modelo Cliente + properties + manager |
| `rutas/models.py` | Modelo Ruta + manager |
| `envios/models.py` | Modelos Empleado, Encomienda, HistorialEstado + lógica |
| `envios/validators.py` | 3 validadores personalizados |
| `envios/querysets.py` | QuerySets para los 3 modelos |
| `envios/views.py` | 6 vistas FBV (dashboard, CRUD, cambio estado) |
| `envios/views_auth.py` | 3 vistas de autenticación |
| `envios/urls.py` | 9 rutas del sistema |
| `envios/forms.py` | EncomiendaForm (ModelForm con Bootstrap) |
| `envios/context_processors.py` | Estadísticas globales para el navbar |
| `envios/admin.py` | Admin con fieldsets, badges, list_per_page |
| `clientes/admin.py` | Admin de Cliente |
| `rutas/admin.py` | Admin de Ruta |
| `templates/base.html` | Plantilla base (Bootstrap 5.3, Font Awesome, navbar, footer) |
| `templates/navbar.html` | Navbar con badges de estado |
| `templates/envios/*.html` | Dashboard, listado, detalle, formulario |
| `templates/accounts/*.html` | Login, perfil |
| `templates/partials/*.html` | stat_card, paginacion |
| `static/css/styles.css` | Estilos personalizados (badges, navbar, cards, tablas) |
| `static/js/main.js` | Tooltips, alertas, confirmación, filas clickeables |
| `Dockerfile` | python:3.12-slim |
| `docker-compose.yml` | web + PostgreSQL 15 |
| `.env` | Variables de entorno |

---

## Comandos Útiles

```bash
# Iniciar contenedores
docker compose up -d

# Ver estado
docker compose ps

# Acceder al shell de Django
docker compose exec web python manage.py shell

# Crear migraciones
docker compose exec web python manage.py makemigrations

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario (si no existe)
docker compose exec web python manage.py createsuperuser

# Admin Django
# http://localhost:8000/admin/  — usuario: admin / contraseña: admin123

# Sistema de Encomiendas
# http://localhost:8000/         — Dashboard (requiere login)
# http://localhost:8000/login/   — Página de inicio de sesión
```

> **Nota:** Cada usuario de Django debe tener un registro `Empleado` con el mismo email en `/admin/envios/empleado/` para poder crear encomiendas o cambiar estados. Si no, verá un mensaje de error claro en lugar de un crash.
