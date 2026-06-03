# Taller de Lenguajes de Programación
## Sesión 02: Introducción a Django

---

## Introducción

Esta sesión cubre conceptos clave utilizados en Django, un framework web full-stack basado en Python. Si eres principiante en programación, puedes tener dificultades para entender algunos conceptos o términos. Sin embargo, es esencial que empieces a familiarizarte con esos nuevos conceptos o términos. Puedes hojear primero esta sección y volver a este capítulo más adelante, después de leer otros capítulos, que son más tangibles.

---

## Objetivos de la sesión

- Comprender la naturaleza de Django y su filosofía fundamental de desarrollo.
- Crear y organizar la estructura de un proyecto Django desde sus cimientos.
- Entender el funcionamiento del patrón MVT y la arquitectura basada en aplicaciones (apps).
- Configurar adecuadamente las variables de entorno utilizando archivos `.env`.
- Contenedorizar la aplicación empleando Docker y establecer la conexión con PostgreSQL.
- Realizar la entrega del proyecto base del Sistema de Gestión de Encomiendas ejecutándose en Docker.

---

## ¿Qué es Django? Filosofía y ventajas

Django es un framework web de alto nivel escrito en Python que fomenta el desarrollo rápido y el diseño limpio y pragmático. Su lema es:

> *"The web framework for perfectionists with deadlines."*

**Filosofía DRY (Don't Repeat Yourself):** Django promueve que cada pieza de conocimiento tenga una única representación en el sistema. Esto reduce la duplicación de código y facilita el mantenimiento.

### Ventajas principales

- **Batteries included:** ORM, administrador automático, sistema de autenticación, formularios, migraciones — todo incluido sin instalar nada extra.
- **Seguro por defecto:** protección contra CSRF, XSS, SQL injection y clickjacking incluida de fábrica.
- **Escalable:** usado por Instagram, Disqus, Pinterest y Mozilla a escala masiva.
- **Gran comunidad:** extensa documentación, paquetes de terceros (Django REST Framework, Celery, etc.).

---

## Instalación y primer proyecto

### Instalando Django

Ahora que hemos instalado y creado nuestro entorno virtual vamos a instalar Django como primer paso para empezar a trabajar con este framework.

1. Para instalarlo podemos ejecutar cualquiera de las siguientes instrucciones:

```bash
pip install django
# o
python -m pip install django
```

2. Para validar la correcta instalación de Django, ejecutamos la siguiente instrucción en la línea de comandos:

```bash
django-admin --version
```

Nos debe mostrar la versión instalada (e.g. `5.2`).

---

### Creando nuestro primer proyecto con Django

Crearemos nuestro proyecto llamado `my_project`:

```bash
django-admin startproject my_project
```

Luego abrimos el proyecto en VS Code y observamos la siguiente estructura de carpetas:

```
my_project/
├── my_project/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py
```

### Archivos de clave de Django creados con `django-admin startproject`

| Archivo | Descripción |
|---|---|
| `manage.py` | Panel de control. Desde aquí se ejecutan todos los comandos de Django. |
| `__init__.py` | Marca el directorio como paquete Python. Normalmente no se modifica. |
| `asgi.py` | Define la aplicación ASGI (servidor asíncrono). Se usa al desplegar. |
| `settings.py` | Archivo de configuración global de la aplicación Django. |
| `urls.py` | Sistema de enrutamiento de URL. Conecta URLs con sus vistas. |
| `wsgi.py` | Interfaz WSGI para servidores como Apache y Nginx. Se usa al desplegar. |

---

### Ejecutando nuestro servidor web

```bash
python manage.py runserver
```

Luego podemos acceder al sitio web en: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Aplicaciones en Django

Django utiliza el concepto de **proyectos y aplicaciones** para gestionar el código. Un proyecto Django contiene una o más aplicaciones que realizan el trabajo simultáneamente para garantizar un flujo fluido de la aplicación web.

Por ejemplo, un sitio web de comercio electrónico tendrá una aplicación para la autenticación de usuarios, otra para los pagos y una tercera para la información de los artículos; cada una se centrará en una sola funcionalidad.

Para crear o agregar aplicaciones dentro del proyecto:

```bash
django-admin startapp <nombre_app>
# o
python manage.py startapp [nombre_app]
```

Para el proyecto de ejemplo `my_project`, creamos una aplicación llamada `myapp`:

```bash
django-admin startapp myapp
```

### Estructura interna de una app

```
myapp/
├── migrations/
│   └── __init__.py
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
└── views.py
```

| Archivo | Descripción |
|---|---|
| `migrations/` | Almacena los archivos de migración generados con `makemigrations`. |
| `admin.py` | Personaliza el sitio de administración de Django. |
| `apps.py` | Personaliza la configuración de la aplicación. |
| `models.py` | ⭐ Define la estructura de la base de datos. |
| `tests.py` | Escribe y ejecuta pruebas para la aplicación. |
| `views.py` | ⭐ Funciones o clases que gestionan las solicitudes HTTP. |

### Registrando nuestra app

Al ejecutar únicamente `startapp`, el proyecto Django no reconoce la nueva aplicación. Debemos registrarla en `INSTALLED_APPS` dentro de `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'my_app',  # <-- nuestra app
]
```

---

## Creando el proyecto Django — Encomiendas

1. Crea una carpeta llamada `encomiendas`.

2. Crea el proyecto base del Sistema de Gestión de Encomiendas:

```bash
# El punto (.) crea el proyecto en la carpeta actual
# Evita crear una carpeta adicional anidada
django-admin startproject config .
```

3. Verifica que el proyecto funcione:

```bash
python manage.py runserver
# Abre en tu navegador: http://127.0.0.1:8000
# Deberías ver el cohete de Django.
```

### Estructura del proyecto

```
encomiendas/
├── config/
│   ├── __init__.py
│   ├── settings.py       <- TODA la configuración
│   ├── urls.py           <- enrutador raíz de URLs
│   ├── asgi.py           <- servidor asíncrono
│   └── wsgi.py           <- servidor síncrono
├── manage.py             <- CLI de Django
└── requirements.txt
```

---

## Patrón MVT (Model – View – Template)

Django sigue el patrón MVT, una variante del clásico MVC donde el framework actúa como el controlador:

| Componente | Responsabilidad | En Encomiendas |
|---|---|---|
| **Model** | Estructura de datos y lógica de BD | Encomienda, Cliente, Ruta, Empleado |
| **View** | Lógica de negocio y procesamiento | Consultar estado, registrar envío |
| **Template** | Presentación HTML al usuario | Lista de encomiendas, detalle de envío |

**Flujo de una petición:** Usuario → URL → View → consulta Model → renderiza Template → Respuesta HTTP

---

## Apps en Django

Un proyecto Django se organiza en apps: módulos independientes y reutilizables.

> **Regla práctica:** una app debe hacer una cosa y hacerla bien.

```bash
django-admin startapp envios
django-admin startapp clientes
django-admin startapp rutas
```

---

## Settings y Configuración

### Registrando nuestras apps

```python
# config/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Nuestras apps del proyecto encomiendas
    'envios',
    'clientes',
    'rutas',
]
```

### Idioma y Zona Horaria

```python
# config/settings.py
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True
```

---

## Introducción a Docker

Docker es una plataforma que permite empaquetar una aplicación y todas sus dependencias en una unidad llamada **contenedor**, garantizando que funcione igual en cualquier máquina.

> **¿Por qué usar Docker en el proyecto?**  
> El equipo desarrollará en Windows, Mac y Linux. Con Docker, todos corren exactamente el mismo ambiente: misma versión de Python, PostgreSQL y dependencias. "Funciona en mi máquina" deja de ser un problema.

### Docker vs Máquina Virtual

| Característica | Contenedor (Docker) | Máquina Virtual |
|---|---|---|
| Sistema Operativo | Comparte el kernel del host | SO completo virtualizado |
| Tiempo de arranque | Milisegundos | Minutos |
| Tamaño | Megabytes | Gigabytes |
| Rendimiento | Casi nativo | Menor rendimiento |
| Aislamiento | Proceso aislado | Completo |

### Imagen vs Contenedor

- **Imagen:** plantilla de solo lectura definida en un `Dockerfile`. Es el "molde" a partir del cual se crean contenedores.
- **Contenedor:** instancia en ejecución de una imagen. Tiene su propio filesystem y ciclo de vida (crear, iniciar, detener, eliminar).

---

## Docker en Proyectos Django

### Laboratorio 2.3 — Containerizar el proyecto

#### Paso 1: Crear el Dockerfile

Crea un archivo llamado `Dockerfile` (sin extensión) en la raíz del proyecto:

```dockerfile
# Imagen base oficial de Python
FROM python:3.11-slim

# Evitar archivos .pyc y buffering de stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha caché de capas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código fuente
COPY . .

# Puerto que expondrá el contenedor
EXPOSE 8000

# Comando por defecto al iniciar el contenedor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

#### Paso 2: Crear `docker-compose.yml`

```yaml
# docker-compose.yml
version: '3.9'

services:
  # Servicio de la app Django
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app          # monta el código en tiempo real
    ports:
      - "8000:8000"
    env_file:
      - .env            # variables de entorno
    depends_on:
      - db

  # Servicio de PostgreSQL
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}

volumes:
  postgres_data:
```

### Comandos esenciales de Docker Compose

```bash
# Construir las imágenes
docker compose build

# Levantar todos los servicios
docker compose up

# Levantar en segundo plano (detached)
docker compose up -d

# Ver logs del servicio web
docker compose logs -f web

# Ejecutar un comando dentro del contenedor
docker compose exec web python manage.py migrate

# Apagar todos los servicios
docker compose down
```

---

## Variables de Entorno (.env)

Las variables de entorno mantienen datos sensibles (contraseñas, claves secretas) fuera del código fuente y del repositorio Git. **Nunca deben subirse a GitHub.**

#### Paso 1: Crear el archivo `.env`

```env
# Django
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=encomiendas_db
DB_USER=encomiendas_user
DB_PASSWORD=encomiendas_pass_2026
```

#### Paso 2: Crear el `.gitignore`

```gitignore
.env
venv/
env/
__pycache__/
*.pyc
db.sqlite3
.DS_Store
```

> **Buena práctica — `.env.example`**  
> Crea un archivo `.env.example` con los nombres de las variables pero sin valores reales. Este archivo **SÍ** se sube a Git para que otros desarrolladores sepan qué variables necesitan configurar.
>
> ```
> SECRET_KEY=
> DEBUG=True
> DB_NAME=
> DB_USER=
> DB_PASSWORD=
> ```

#### Paso 3: Instalar `python-decouple` y leer el `.env`

```bash
pip install python-decouple
pip freeze > requirements.txt
```

Actualiza `config/settings.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool, default=False)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
```

---

## Django + PostgreSQL con Docker

### Laboratorio 2.4 — Sistema de Encomiendas corriendo en Docker

#### Paso 1: Configurar la base de datos en `settings.py`

```python
# config/settings.py
from decouple import config

DATABASES = {
    'default': {
        'ENGINE':   config('DB_ENGINE'),
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
    }
}
```

#### Paso 2: Instalar el adaptador de PostgreSQL

```bash
pip install psycopg2-binary
pip freeze > requirements.txt
```

#### Paso 3: Crear el primer modelo — `Encomienda`

```python
# envios/models.py
from django.db import models

class Encomienda(models.Model):
    class EstadoChoices(models.TextChoices):
        PENDIENTE   = 'PE', 'Pendiente'
        EN_TRANSITO = 'TR', 'En tránsito'
        ENTREGADO   = 'EN', 'Entregado'
        DEVUELTO    = 'DE', 'Devuelto'

    codigo       = models.CharField(max_length=20, unique=True)
    descripcion  = models.TextField()
    peso_kg      = models.DecimalField(max_digits=8, decimal_places=2)
    estado       = models.CharField(
                       max_length=2, choices=EstadoChoices.choices,
                       default=EstadoChoices.PENDIENTE)
    fecha_envio  = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} — {self.get_estado_display()}"

    class Meta:
        verbose_name        = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering            = ['-fecha_envio']
```

#### Paso 4: Registrar en el Admin

```python
# envios/admin.py
from django.contrib import admin
from .models import Encomienda

@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'descripcion', 'peso_kg', 'estado', 'fecha_envio')
    list_filter   = ('estado',)
    search_fields = ('codigo', 'descripcion')
```

#### Paso 5: Levantar todo y aplicar migraciones

```bash
# 1. Construir y levantar los contenedores
docker compose up --build -d

# 2. Crear migraciones del modelo Encomienda
docker compose exec web python manage.py makemigrations

# 3. Aplicar migraciones a PostgreSQL
docker compose exec web python manage.py migrate

# 4. Crear superusuario para el admin
docker compose exec web python manage.py createsuperuser

# 5. Verificar en el navegador
# App:   http://localhost:8000
# Admin: http://localhost:8000/admin
```

---

## Estructura final del proyecto

```
encomiendas/
├── config/
│   ├── settings.py       <- BD con variables .env
│   └── urls.py
├── envios/
│   ├── models.py         <- Modelo Encomienda
│   └── admin.py          <- Registro en Admin
├── clientes/
├── rutas/
├── Dockerfile
├── docker-compose.yml
├── .env                  <- NO subir a Git
├── .env.example          <- SÍ subir a Git
├── .gitignore
└── requirements.txt
```

---

## Entregable de la Sesión 2

Al finalizar la sesión debes poder demostrar:

1. Proyecto Django con las 3 apps creadas (`envios`, `clientes`, `rutas`).
2. Aplicación corriendo en Docker con PostgreSQL (`docker compose up`).
3. Modelo `Encomienda` creado y migrado correctamente.
4. Acceso al panel de administración en `http://localhost:8000/admin`.
5. Archivo `.env` configurado y en `.gitignore`.
6. Repositorio publicado en GitHub con `.env.example` incluido.

---

**Próxima sesión:** Modelos y ORM de Django — relaciones entre Encomienda, Cliente y Ruta. Migraciones avanzadas y Django Shell.
