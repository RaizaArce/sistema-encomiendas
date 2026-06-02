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

---

## Decisiones Técnicas

| Decisión | Razón |
|----------|-------|
| `python:3.12-slim` | Django 6.0.5 requiere Python ≥ 3.12 |
| Sin `version: '3.9'` en compose | Obsoleto en Docker Compose v2+ |
| `PROTECT` en FKs de negocio | Evita borrado accidental de clientes/empleados/rutas |
| `CASCADE` en HistorialEstado | El historial se borra con la encomienda |
| `validar_nro_doc_dni` definido sin usar | Disponible para futuro, la guía lo pide |



## Archivos Relevantes

| Archivo | Descripción |
|---------|-------------|
| `config/choices.py` | Enumerados del sistema |
| `config/settings.py` | Configuración Django (DB, idioma, zona horaria) |
| `clientes/models.py` | Modelo Cliente + properties + manager |
| `rutas/models.py` | Modelo Ruta + manager |
| `envios/models.py` | Modelos Empleado, Encomienda, HistorialEstado + lógica |
| `envios/validators.py` | 3 validadores personalizados |
| `envios/querysets.py` | QuerySets para los 3 modelos |
| `envios/admin.py` | Admin de Encomienda, Empleado, HistorialEstado |
| `clientes/admin.py` | Admin de Cliente |
| `rutas/admin.py` | Admin de Ruta |
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

# Admin Django
# http://localhost:8000/admin/  — usuario: admin / contraseña: admin123
```
