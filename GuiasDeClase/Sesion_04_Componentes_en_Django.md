# Taller de Lenguajes de Programación
## Sesión 04: Componentes en Django

---

## Introducción

En esta sesión construiremos las páginas web del Sistema de Gestión de Encomiendas utilizando los componentes frontales de Django: URLs, vistas, templates, formularios, el Admin site y autenticación de usuarios. Al terminar tendremos un sistema web funcional que corre completamente dentro de Docker.

**Temas de esta sesión:**
- 4.1. URLs, Views y Templates
- 4.2. Formularios
- 4.3. Django Admin Site
- 4.4. Django Authentication
- 4.5. Sesiones en Django

> **CONTEXTO DEL PROYECTO**
> Construiremos las siguientes pantallas del sistema de encomiendas:
> - Dashboard principal con estadísticas (encomiendas activas, en tránsito, con retraso).
> - Listado y detalle de encomiendas con paginación y búsqueda.
> - Formulario de registro de nueva encomienda.
> - Páginas de login y perfil del empleado.
> - Todo protegido con autenticación: solo usuarios con sesión pueden acceder.

---

## 4.1 URLs, Views y Templates

### El modelo MVT (Model-View-Template) en Django

Django se basa en la arquitectura **MVT (Model-View-Template)**, un patrón de diseño de software para desarrollar aplicaciones web con tres partes:

- **Modelo**: Actúa como la interfaz de datos. Es responsable de mantenerlos y está representado por una base de datos relacional (MySQL, Postgres, etc.).
- **View**: La interfaz de usuario — lo que ves en el navegador. Representada por archivos HTML/CSS/Javascript y Jinja.
- **Template**: Consiste en partes estáticas del HTML de salida más sintaxis especial que describe cómo se insertará el contenido dinámico.

---

### URLs de la app Envios

Django utiliza un sistema basado en patrones para definir las rutas de las aplicaciones web, configurados en archivos `urls.py`.

```python
# envios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.dashboard,                name='dashboard'),
    path('encomiendas/',                  views.encomienda_lista,         name='encomienda_lista'),
    path('encomiendas/nueva/',            views.encomienda_crear,         name='encomienda_crear'),
    path('encomiendas/<int:pk>/',         views.encomienda_detalle,       name='encomienda_detalle'),
    path('encomiendas/<int:pk>/estado/',  views.encomienda_cambiar_estado, name='encomienda_cambiar_estado'),
]
```

Registrar las URLs en el enrutador principal:

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('',          include('envios.urls')),
    path('accounts/', include('django.contrib.auth.urls')),   # login/logout incluidos
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
```

---

### Django Templates

Las plantillas están escritas en HTML, CSS y Javascript en archivos `.html`. Django las usa para proporcionar un frontend dinámico al sitio web.

#### Configurar la estructura de templates

```python
# config/settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # <- carpeta global de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Archivos estáticos (CSS, JS, imágenes)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

### Herencia de Templates

La herencia es el concepto más importante del sistema de templates de Django. Permite que todas las páginas compartan una estructura común (navbar, footer, CSS) definida una sola vez en una plantilla base.

> **VENTAJA CLAVE**
> Sin herencia: cada página repite el DOCTYPE, head, navbar y footer — cientos de líneas duplicadas.
> Con herencia: el navbar y el footer se escriben **UNA sola vez** en `base.html`. Cualquier cambio se refleja automáticamente en todas las páginas.

#### Configurar Plantilla base (`base.html`)

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Encomiendas{% endblock %}</title>

  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <!-- Font Awesome -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

  {% load static %}
  <link rel="stylesheet" href="{% static 'css/styles.css' %}">
  {% block extra_css %}{% endblock %}
</head>

<body>
  {% include 'navbar.html' %}

  <main class="container py-4">
    {% if messages %}
    <div class="messages">
      {% for message in messages %}
      <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% block content %}{% endblock %}
  </main>

  <footer class="bg-dark text-white py-3 mt-5">
    <div class="container text-center">
      <p class="mb-0">Sistema de Gestión de Encomiendas &copy; {% now "Y" %}</p>
    </div>
  </footer>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{% static 'js/main.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Resumen de bloques definidos en `base.html`

| Bloque      | Para qué sirve                                  | Obligatorio |
|-------------|--------------------------------------------------|-------------|
| `title`     | Título de la pestaña del navegador               | Sí          |
| `extra_css` | CSS adicional que solo carga esta página          | No          |
| `content`   | TODO el contenido HTML de la página              | Sí          |
| `extra_js`  | JavaScript adicional que solo carga esta página   | No          |

---

### Django Template Language (DTL) — Etiquetas más usadas

El DTL es un lenguaje basado en texto que permite generar contenido web dinámico. Usa cuatro construcciones principales:

- **Variables**: `{{ nombre_de_la_variable }}` — muestran datos dinámicos.
- **Etiquetas**: `{% nombre_de_la_etiqueta %}` — controlan la lógica (bucles, condiciones).
- **Filtros**: `{{ variable|nombre_del_filtro }}` — modifican el resultado de las variables.
- **Comentarios**: `{# comentario #}` — se ignoran en la renderización.

| Etiqueta                     | Descripción                                        | Ejemplo                           |
|------------------------------|----------------------------------------------------|-----------------------------------|
| `{% load static %}`          | Carga la librería de archivos estáticos            | `{% load static %}`               |
| `{% static 'ruta' %}`        | Genera la URL de un archivo estático               | `{% static 'css/styles.css' %}`   |
| `{% url 'nombre' %}`         | Genera la URL de una vista por su nombre           | `{% url 'encomienda_lista' %}`    |
| `{% include 'file' %}`       | Incluye otra plantilla dentro                      | `{% include 'navbar.html' %}`     |
| `{% extends 'base.html' %}`  | Hereda de la plantilla base                        | Primera línea de cada template    |
| `{% block nombre %}`         | Define una zona sobreescribible                    | `{% block content %}...{% endblock %}` |
| `{{ variable }}`             | Muestra el valor de una variable                   | `{{ encomienda.codigo }}`         |
| `{% for x in lista %}`       | Bucle sobre una lista                              | `{% for enc in encomiendas %}`    |
| `{% if condicion %}`         | Condicional                                        | `{% if enc.tiene_retraso %}`      |
| `{% csrf_token %}`           | Token de seguridad para formularios POST           | Dentro de todo `<form>`           |

**Características principales del DTL:**
- **Herencia de plantillas**: permite crear un `base.html` con elementos comunes que otras páginas amplían.
- **Escapado automático**: previene ataques XSS escapando caracteres HTML como `<`, `>` y `&`.
- **Sin código arbitrario**: no puede ejecutar expresiones Python arbitrarias.
- **Extensibilidad**: permite crear etiquetas y filtros personalizados.

---

### Dashboard del Sistema

```html
{# templates/envios/dashboard.html #}
{% extends 'base.html' %}

{% block title %}Dashboard — Encomiendas{% endblock %}

{% block content %}
<div class="row mb-4">
  <div class="col-12">
    <h2 class="h3"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</h2>
  </div>
</div>

<!-- Tarjetas de estadísticas -->
<div class="row mb-4">
  {% for label, valor, color, icono in stats %}
  <div class="col-md-3">
    <div class="card bg-{{ color }} text-white shadow-sm mb-3">
      <div class="card-body d-flex justify-content-between align-items-center">
        <div>
          <h6 class="card-title">{{ label }}</h6>
          <h2 class="mb-0">{{ valor }}</h2>
        </div>
        <i class="fas fa-{{ icono }} fa-2x"></i>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

<!-- Últimas encomiendas -->
<div class="card shadow">
  <div class="card-header bg-white">
    <h5 class="mb-0">Últimas encomiendas registradas</h5>
  </div>
  <div class="card-body p-0">
    <table class="table table-hover mb-0">
      <thead>
        <tr>
          <th>Código</th><th>Remitente</th>
          <th>Destino</th><th>Estado</th><th></th>
        </tr>
      </thead>
      <tbody>
        {% for enc in ultimas %}
        <tr>
          <td><code>{{ enc.codigo }}</code></td>
          <td>{{ enc.remitente.nombre_completo }}</td>
          <td>{{ enc.ruta.destino }}</td>
          <td>
            <span class="badge bg-{% if enc.esta_en_transito %}primary
                         {% elif enc.esta_entregada %}success
                         {% elif enc.tiene_retraso %}danger
                         {% else %}secondary{% endif %}">
              {{ enc.get_estado_display }}
            </span>
          </td>
          <td><a href="{% url 'encomienda_detalle' enc.pk %}" class="btn btn-sm btn-outline-primary">Ver</a></td>
        </tr>
        {% empty %}
        <tr><td colspan="5" class="text-center py-3">No hay encomiendas</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

---

### Listado con paginación y filtros

```html
{# templates/envios/lista.html #}
{% extends 'base.html' %}

{% block title %}Encomiendas{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2 class="h3"><i class="fas fa-boxes me-2"></i>Encomiendas</h2>
  <a href="{% url 'encomienda_crear' %}" class="btn btn-primary">
    <i class="fas fa-plus me-1"></i>Nueva
  </a>
</div>

{# Formulario de busqueda y filtros (metodo GET) #}
<form method="get" class="row g-2 mb-3">
  <div class="col-md-6">
    <input type="text" name="q" value="{{ request.GET.q }}"
           class="form-control" placeholder="Buscar por código o cliente...">
  </div>
  <div class="col-md-4">
    <select name="estado" class="form-select">
      <option value="">Todos los estados</option>
      {% for valor, etiqueta in estados %}
      <option value="{{ valor }}" {% if estado_activo == valor %}selected{% endif %}>
        {{ etiqueta }}
      </option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-2">
    <button type="submit" class="btn btn-outline-primary w-100">Filtrar</button>
  </div>
</form>

{# Tabla de encomiendas #}
<div class="card shadow">
  <div class="card-body p-0">
    <table class="table table-hover mb-0">
      <thead>
        <tr>
          <th>Código</th><th>Remitente</th>
          <th>Ruta</th><th>Estado</th><th>Fecha</th><th></th>
        </tr>
      </thead>
      <tbody>
        {% for enc in encomiendas %}
        <tr>
          <td><code>{{ enc.codigo }}</code></td>
          <td>{{ enc.remitente.nombre_completo }}</td>
          <td>{{ enc.ruta.origen }} → {{ enc.ruta.destino }}</td>
          <td>
            <span class="badge-estado badge-{{ enc.estado }}">
              {{ enc.get_estado_display }}
            </span>
          </td>
          <td>{{ enc.fecha_registro|date:'d/m/Y' }}</td>
          <td>
            <a href="{% url 'encomienda_detalle' enc.pk %}"
               class="btn btn-sm btn-outline-primary">Ver</a>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6" class="text-center py-4">No se encontraron encomiendas</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  {# Paginacion #}
  {% if encomiendas.has_other_pages %}
  <div class="card-footer bg-white">
    <nav><ul class="pagination justify-content-center mb-0">
      {% if encomiendas.has_previous %}
      <li class="page-item">
        <a class="page-link" href="?page={{ encomiendas.previous_page_number }}&q={{ request.GET.q }}&estado={{ request.GET.estado }}">
          &laquo; Anterior
        </a>
      </li>
      {% endif %}
      {% for num in encomiendas.paginator.page_range %}
      <li class="page-item {% if encomiendas.number == num %}active{% endif %}">
        <a class="page-link" href="?page={{ num }}&q={{ request.GET.q }}&estado={{ request.GET.estado }}">{{ num }}</a>
      </li>
      {% endfor %}
      {% if encomiendas.has_next %}
      <li class="page-item">
        <a class="page-link" href="?page={{ encomiendas.next_page_number }}&q={{ request.GET.q }}&estado={{ request.GET.estado }}">
          Siguiente &raquo;
        </a>
      </li>
      {% endif %}
    </ul></nav>
  </div>
  {% endif %}
</div>
{% endblock %}
```

---

### Filtros de Template más usados

| Filtro            | Ejemplo                                             | Resultado                          |
|-------------------|-----------------------------------------------------|------------------------------------|
| `date`            | `{{ enc.fecha_registro\|date:'d/m/Y' }}`            | `18/04/2026`                       |
| `date con hora`   | `{{ enc.fecha_registro\|date:'d/m/Y H:i' }}`        | `18/04/2026 10:30`                 |
| `truncatechars`   | `{{ enc.descripcion\|truncatechars:50 }}`           | `Caja con ropa y docume…`          |
| `default`         | `{{ enc.observaciones\|default:'—' }}`              | `—` (si el campo es vacío o None)  |
| `floatformat`     | `{{ enc.costo_envio\|floatformat:2 }}`              | `25.00`                            |
| `length`          | `{{ enc.historial.all\|length }}`                   | Número de registros en el historial |
| `lower` / `upper` | `{{ enc.codigo\|lower }}`                           | `enc-2026-001`                     |
| `join`            | `{{ lista_estados\|join:', ' }}`                    | `Pendiente, En tránsito, Entregado`|
| `yesno`           | `{{ enc.esta_entregada\|yesno:'Si,No,—' }}`         | `Si` / `No` / `—`                 |
| `safe`            | `{{ html_content\|safe }}`                          | Renderiza HTML sin escapar         |

---

## Archivos Estáticos

### Configuración en `settings.py`

```python
# config/settings.py

# URL base para los archivos estáticos
STATIC_URL = 'static/'

# Carpetas donde Django busca los archivos en DESARROLLO
STATICFILES_DIRS = [
    BASE_DIR / 'static',   # <- aqui pones tus CSS, JS, imagenes
]

# Carpeta donde se juntan todos al hacer collectstatic (PRODUCCION)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Archivos subidos por el usuario
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Uso correcto en los templates

```html
{# SIEMPRE cargar static antes del primer uso #}
{% load static %}

{# Bootstrap desde CDN: no necesita {% static %} #}
<link href="https://cdn.../bootstrap.min.css" rel="stylesheet">

{# Tu CSS propio: SI necesita {% static %} #}
<link rel="stylesheet" href="{% static 'css/styles.css' %}">

{# Imagen #}
<img src="{% static 'img/logo.png' %}" alt="Logo" height="40">

{# JS propio al final del body #}
<script src="{% static 'js/main.js' %}"></script>
```

> **COLLECTSTATIC EN DOCKER**
> En producción debes juntar todos los archivos estáticos en `STATIC_ROOT`:
> ```bash
> docker compose exec web python manage.py collectstatic
> ```
> En desarrollo con `DEBUG=True` esto **NO** es necesario.

---

### CSS Personalizado — `styles.css`

#### Variables de color y estructura base

```css
/* static/css/styles.css */

/* ── Variables globales del sistema ────────────────────────────── */
:root {
    /* Colores de estados de encomienda */
    --estado-pendiente: #6c757d;   /* gris */
    --estado-transito:  #0d6efd;   /* azul */
    --estado-destino:   #fd7e14;   /* naranja */
    --estado-entregado: #198754;   /* verde */
    --estado-devuelto:  #dc3545;   /* rojo */

    --color-primary: #0d6efd;
    --color-bg:      #f8f9fa;
    --shadow-sm:     0 2px 8px rgba(0,0,0,.07);
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--color-bg);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

main { flex: 1; }   /* el footer siempre queda abajo */
```

#### Badges de estado de encomienda

El sistema usa clases dinámicas basadas en el código de estado (PE, TR, DE, EN, DV). El template genera `class="badge-estado badge-{{ enc.estado }}"` y el CSS aplica el color correcto automáticamente.

```css
.badge-estado {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: .78rem;
    font-weight: 600;
    letter-spacing: .3px;
    white-space: nowrap;
}

.badge-PE { background-color: #e9ecef; color: #495057; }   /* Pendiente */
.badge-TR { background-color: #cfe2ff; color: #084298; }   /* En tránsito */
.badge-DE { background-color: #fff3cd; color: #664d03; }   /* En destino */
.badge-EN { background-color: #d1e7dd; color: #0a3622; }   /* Entregado */
.badge-DV { background-color: #f8d7da; color: #58151c; }   /* Devuelto */
```

#### Animaciones y paginación

```css
/* ── Alertas flash: desaparecen automáticamente ─────────────────── */
.alert { animation: fadeAlert 5s ease forwards; }

@keyframes fadeAlert {
    0%   { opacity: 1; max-height: 200px; }
    70%  { opacity: 1; }
    100% { opacity: 0; max-height: 0; padding: 0; margin: 0; overflow: hidden; }
}

/* ── Paginación ─────────────────────────────────────────────────── */
.pagination .page-link { color: var(--color-primary); }
.pagination .page-item.active .page-link {
    background-color: var(--color-primary);
    border-color: var(--color-primary);
}
```

---

### JavaScript básico — `main.js`

```javascript
// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {

    // ── Inicializar tooltips de Bootstrap ──────────────────────────
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(el => new bootstrap.Tooltip(el));

    // ── Auto-cerrar alertas flash después de 5 segundos ────────────
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);

    // ── Confirmación antes de eliminar ────────────────────────────
    // Uso: <button onclick="return confirmar('Eliminar?')" form="formEliminar">
    window.confirmar = function (mensaje) {
        return confirm(mensaje || '¿Estás seguro?');
    };

    // ── Resaltar fila al hacer clic ───────────────────────────────
    // Uso: <tr class="fila-link" data-href="{% url 'encomienda_detalle' enc.pk %}">
    document.querySelectorAll('.fila-link').forEach(function (fila) {
        fila.addEventListener('click', function () {
            window.location = this.dataset.href;
        });
    });

});
```

---

## Vistas en Django

Una vista en Django es una función o clase Python que recibe un objeto `HttpRequest` y devuelve un objeto `HttpResponse`. Es el puente entre el modelo (datos) y el template (presentación).

| Tipo            | Cuándo usar                            | Ejemplo en el proyecto                      |
|-----------------|----------------------------------------|---------------------------------------------|
| FBV (función)   | Lógica personalizada, control explícito | `dashboard()`, `encomienda_crear()`         |
| CBV (clase)     | Operaciones CRUD estándar              | `EncomiendaListView`, `EncomiendaDetailView`|
| Vista genérica  | CRUD completo con mínimo código        | `ListView`, `DetailView`, `CreateView`      |

---

### Vistas Basadas en Funciones (FBV)

```python
# envios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Encomienda, Empleado, HistorialEstado
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoEnvio


# ── Vista mínima ──────────────────────────────────────────────────
def mi_vista(request):
    from django.http import HttpResponse
    return HttpResponse('Hola desde Django')


# ── Vista real: dashboard del sistema ─────────────────────────────
@login_required
def dashboard(request):
    """Vista principal del sistema con estadísticas"""
    hoy = timezone.now().date()
    context = {
        'total_activas':  Encomienda.objects.activas().count(),
        'en_transito':    Encomienda.objects.en_transito().count(),
        'con_retraso':    Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
                              estado=EstadoEnvio.ENTREGADO,
                              fecha_entrega_real=hoy).count(),
        'ultimas':        Encomienda.objects.con_relaciones()[:5],
    }
    return render(request, 'envios/dashboard.html', context)
```

#### Las cuatro funciones de atajo más usadas

```python
# render() — renderizar un template con contexto
def encomienda_lista(request):
    encomiendas = Encomienda.objects.all()
    return render(request, 'envios/lista.html', {'encomiendas': encomiendas})


# redirect() — redirigir a otra URL
def mi_vista(request):
    return redirect('encomienda_lista')             # por nombre
    return redirect('encomienda_detalle', pk=1)     # con argumento
    return redirect('/encomiendas/')                # por URL directa


# get_object_or_404() — buscar o devolver 404
def encomienda_detalle(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)
    # También acepta QuerySets optimizados:
    enc = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    return render(request, 'envios/detalle.html', {'encomienda': enc})


# get_list_or_404() — lista o devolver 404
def encomiendas_por_ruta(request, ruta_pk):
    encomiendas = get_list_or_404(Encomienda, ruta__pk=ruta_pk)
    return render(request, 'envios/lista.html', {'encomiendas': encomiendas})
```

#### Patrón GET/POST — vista de creación completa

```python
@login_required
def encomienda_crear(request):
    """
    GET  → muestra el formulario vacío
    POST → valida, guarda y redirige al detalle
    """
    from .forms import EncomiendaForm

    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            enc = form.save(commit=False)       # no guarda aún en BD
            enc.empleado_registro = Empleado.objects.get(email=request.user.email)
            enc.save()                          # ahora sí guarda
            messages.success(request, f'Encomienda {enc.codigo} registrada correctamente.')
            # Redirige para evitar reenvío del formulario al recargar
            return redirect('encomienda_detalle', pk=enc.pk)
        # Si el form tiene errores, vuelve a mostrar con los errores
    else:
        form = EncomiendaForm()   # GET: form vacío

    return render(request, 'envios/form.html', {
        'form': form,
        'titulo': 'Nueva Encomienda',
    })
```

> **PATRÓN POST/REDIRECT/GET (PRG)**
> Después de un POST exitoso SIEMPRE redirige con `redirect()`.
> Si el usuario recarga la página después del redirect, no reenvía el formulario.

---

### El Objeto Request

```python
def mi_vista(request):
    # Método HTTP
    request.method          # 'GET', 'POST', 'PUT', 'DELETE'

    # Datos enviados
    request.GET             # parámetros de URL (?q=Lima&estado=TR)
    request.POST            # datos del formulario (método POST)
    request.FILES           # archivos subidos

    # Usuario autenticado
    request.user            # objeto User (o AnonymousUser)
    request.user.username   # 'juan.mendoza'
    request.user.is_authenticated   # True / False
    request.user.email      # 'juan@encomiendas.pe'

    # Sesión del usuario
    request.session                         # diccionario de sesión
    request.session['ultima_ruta'] = 1      # guardar en sesión
    ruta = request.session.get('ultima_ruta')   # leer

    # Meta del request
    request.path                 # '/encomiendas/1/'
    request.get_full_path()      # '/encomiendas/1/?page=2'
    request.META['REMOTE_ADDR']  # IP del cliente
```

---

### Tipos de Respuesta HTTP

| Clase / Función           | Status code    | Cuándo usar                                       |
|---------------------------|----------------|----------------------------------------------------|
| `render()`                | 200 OK         | Renderizar un template con contexto — la más común |
| `redirect()`              | 302 Found      | Redirigir a otra URL después de un POST            |
| `HttpResponse()`          | Configurable   | Respuesta básica con texto, HTML o cualquier contenido |
| `JsonResponse()`          | 200 OK         | Devolver JSON para peticiones AJAX o APIs          |
| `raise Http404`           | 404 Not Found  | Recurso no encontrado                              |
| `PermissionDenied`        | 403 Forbidden  | El usuario no tiene permiso                        |
| `HttpResponseBadRequest`  | 400 Bad Request| Datos inválidos en la petición                     |

```python
# JsonResponse — endpoint AJAX para el badge del navbar
def encomienda_estado_json(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo':  enc.codigo,
        'estado':  enc.estado,
        'display': enc.get_estado_display(),
        'retraso': enc.tiene_retraso,
        'dias':    enc.dias_en_transito,
    })
```

---

### Decoradores de Vistas

```python
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

# @login_required — proteger vistas
@login_required
def dashboard(request): ...

# @require_GET — solo lectura
@require_GET
@login_required
def encomienda_lista(request): ...

# @require_POST — operaciones que modifican datos
@require_POST
@login_required
def encomienda_cambiar_estado(request, pk): ...

# @require_http_methods — GET y POST
@require_http_methods(['GET', 'POST'])
@login_required
def encomienda_crear(request): ...

# Configuración en settings.py (aplica a todos los @login_required)
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
```

> **NOTA:** Los decoradores se aplican de abajo hacia arriba. `@login_required` actúa segundo, `@require_POST` actúa primero.

---

### Paginación

```python
# envios/views.py
from django.core.paginator import Paginator

@login_required
def encomienda_lista(request):
    qs = Encomienda.objects.con_relaciones()

    # ── Filtros opcionales ──────────────────────────────────────────
    estado = request.GET.get('estado', '')
    q      = request.GET.get('q', '')

    if estado:
        qs = qs.filter(estado=estado)
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(codigo__icontains=q)              |
            Q(remitente__apellidos__icontains=q) |
            Q(destinatario__apellidos__icontains=q)
        )

    # ── Paginación ──────────────────────────────────────────────────
    paginator   = Paginator(qs, 15)               # 15 por página
    page_number = request.GET.get('page', 1)      # página actual
    encomiendas = paginator.get_page(page_number) # objeto Page

    # El objeto Page tiene estos atributos útiles:
    # encomiendas.number              → número de página actual
    # encomiendas.paginator.count     → total de registros
    # encomiendas.paginator.num_pages → total de páginas
    # encomiendas.has_previous()      → True/False
    # encomiendas.has_next()          → True/False

    return render(request, 'envios/lista.html', {
        'encomiendas':  encomiendas,       # objeto Page (iterable)
        'estados':      EstadoEnvio.choices,
        'estado_activo': estado,
        'q':            q,
    })
```

---

### Vistas Basadas en Clases (CBV)

```python
# envios/views_cbv.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from .models import Encomienda
from .forms import EncomiendaForm


# ── ListView: lista paginada ──────────────────────────────────────
class EncomiendaListView(LoginRequiredMixin, ListView):
    model               = Encomienda
    template_name       = 'envios/lista.html'
    context_object_name = 'encomiendas'
    paginate_by         = 15
    ordering            = ['-fecha_registro']

    def get_queryset(self):
        qs     = Encomienda.objects.con_relaciones()
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = EstadoEnvio.choices
        return ctx


# ── DetailView: detalle de un registro ───────────────────────────
class EncomiendaDetailView(LoginRequiredMixin, DetailView):
    model               = Encomienda
    template_name       = 'envios/detalle.html'
    context_object_name = 'encomienda'

    def get_queryset(self):
        return Encomienda.objects.con_relaciones()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['historial'] = self.object.historial.select_related('empleado')
        return ctx


# ── CreateView: formulario de creación ───────────────────────────
class EncomiendaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model           = Encomienda
    form_class      = EncomiendaForm
    template_name   = 'envios/form.html'
    success_message = 'Encomienda %(codigo)s creada correctamente.'

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.empleado_registro = self.request.user.empleado
        return super().form_valid(form)


# ── UpdateView: formulario de edición ────────────────────────────
class EncomiendaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model           = Encomienda
    form_class      = EncomiendaForm
    template_name   = 'envios/form.html'
    success_message = 'Encomienda actualizada correctamente.'

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})
```

#### Registrar CBV en `urls.py`

```python
# envios/urls.py — CBV con .as_view()
from django.urls import path
from . import views_cbv

urlpatterns = [
    path('',               views_cbv.EncomiendaListView.as_view(),   name='encomienda_lista'),
    path('<int:pk>/',      views_cbv.EncomiendaDetailView.as_view(), name='encomienda_detalle'),
    path('nueva/',         views_cbv.EncomiendaCreateView.as_view(), name='encomienda_crear'),
    path('<int:pk>/editar/', views_cbv.EncomiendaUpdateView.as_view(), name='encomienda_editar'),
]
```

---

### Context Processors

Los Context Processors son funciones que inyectan datos automáticamente en **todas** las plantillas, eliminando la necesidad de pasar las mismas variables en cada vista.

```python
# envios/context_processors.py
from .models import Encomienda

def estadisticas_globales(request):
    """
    Inyecta en TODOS los templates estas variables.
    Visible en el navbar sin tener que pasarlas vista por vista.
    Solo corre si el usuario está autenticado.
    """
    if not request.user.is_authenticated:
        return {}

    return {
        'nav_activas':    Encomienda.objects.activas().count(),
        'nav_retraso':    Encomienda.objects.con_retraso().count(),
        'nav_pendientes': Encomienda.objects.pendientes().count(),
    }
```

```python
# config/settings.py — registrar el context processor
TEMPLATES = [{
    ...
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            # Nuestro context processor personalizado:
            'envios.context_processors.estadisticas_globales',
        ],
    },
}]
```

```html
{# templates/navbar.html — usar las variables globales #}
<li class="nav-item">
  <a class="nav-link" href="{% url 'encomienda_lista' %}">
    Encomiendas
    {% if nav_retraso > 0 %}
    <span class="badge bg-danger rounded-pill">{{ nav_retraso }}</span>
    {% endif %}
  </a>
</li>
```

---

### Messages framework — notificaciones flash

```python
from django.contrib import messages

# En la vista — añadir mensajes antes del redirect
@login_required
def encomienda_crear(request):
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            enc = form.save()
            messages.success(request, f'Encomienda {enc.codigo} creada.')
            return redirect('encomienda_detalle', pk=enc.pk)
        else:
            messages.error(request, 'Corrige los errores del formulario.')

# Niveles disponibles:
messages.debug(request,   'Mensaje de depuración')
messages.info(request,    'Información general')
messages.success(request, 'Operación exitosa')
messages.warning(request, 'Atención: algo puede salir mal')
messages.error(request,   'Error: la operación falló')
```

---

## 4.2 Formularios en Django

### Creación de formularios

Existen dos tipos principales:
- **`forms.Form`**: Para formularios no vinculados directamente a un modelo (búsquedas, contacto). Cada campo se define manualmente.
- **`forms.ModelForm`**: Genera automáticamente campos a partir de un modelo existente. Incluye `.save()` para escribir en la BD.

### Lab 4.1 — EncomiendaForm con ModelForm

```python
# envios/forms.py
from django import forms
from .models import Encomienda
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoGeneral


class EncomiendaForm(forms.ModelForm):
    """Formulario para registrar una nueva encomienda"""

    class Meta:
        model  = Encomienda
        fields = [
            'codigo', 'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'destinatario', 'ruta',
            'costo_envio', 'fecha_entrega_est', 'observaciones',
        ]
        widgets = {
            'codigo':           forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peso_kg':          forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volumen_cm3':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remitente':        forms.Select(attrs={'class': 'form-select'}),
            'destinatario':     forms.Select(attrs={'class': 'form-select'}),
            'ruta':             forms.Select(attrs={'class': 'form-select'}),
            'costo_envio':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_entrega_est': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones':    forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'codigo':            'Código de encomienda',
            'peso_kg':           'Peso (kg)',
            'volumen_cm3':       'Volumen (cm³)',
            'fecha_entrega_est': 'Fecha estimada de entrega',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo clientes activos
        self.fields['remitente'].queryset   = Cliente.objects.activos()
        self.fields['destinatario'].queryset = Cliente.objects.activos()
        # Mostrar solo rutas activas
        self.fields['ruta'].queryset = Ruta.objects.activas()

    def clean(self):
        """Validaciones adicionales a nivel de formulario"""
        cleaned      = super().clean()
        remitente    = cleaned.get('remitente')
        destinatario = cleaned.get('destinatario')

        if remitente and destinatario and remitente == destinatario:
            raise forms.ValidationError(
                'El remitente y el destinatario no pueden ser la misma persona.'
            )
        return cleaned
```

#### Elementos clave de los formularios Django

| Elemento                   | Descripción                                                              |
|----------------------------|--------------------------------------------------------------------------|
| `{% csrf_token %}`         | Token de seguridad obligatorio en todo formulario POST. Protege contra CSRF |
| `{{ form.field.errors }}`  | Muestra los errores de un campo específico                               |
| `{{ form.non_field_errors }}`| Muestra errores que no pertenecen a ningún campo                       |
| `form.is_valid()`          | Valida todos los campos y ejecuta `clean()`                              |
| `form.cleaned_data`        | Diccionario con los datos validados y limpios                            |
| `form.save()`              | Guarda el formulario en la BD (solo `ModelForm`)                         |

---

### Renderizado de formularios: cuatro métodos

| Método                  | Código en el template   | Etiqueta HTML generada     | Cuándo usarlo                    |
|-------------------------|-------------------------|----------------------------|----------------------------------|
| `form.as_p()`           | `{{ form.as_p }}`       | `<p>` por campo            | Prototipado rápido               |
| `form.as_table()`       | `{{ form.as_table }}`   | `<tr>/<th>/<td>` por campo | Layouts tabulares simples        |
| `form.as_ul()`          | `{{ form.as_ul }}`      | `<li>` por campo           | Poco frecuente en la práctica    |
| **Campo por campo**     | `{{ form.campo }}`      | Control total del HTML     | **Producción con Bootstrap**     |

#### Variables disponibles por campo (método 4)

| Variable                       | Qué genera                              |
|--------------------------------|-----------------------------------------|
| `{{ form.campo }}`             | Solo el input HTML con sus atributos    |
| `{{ form.campo.label }}`       | El texto del label (sin etiqueta HTML)  |
| `{{ form.campo.label_tag }}`   | La etiqueta `<label for="...">` completa |
| `{{ form.campo.errors }}`      | Lista de errores del campo              |
| `{{ form.campo.help_text }}`   | El texto de ayuda definido en el Form   |
| `{{ form.non_field_errors }}`  | Errores globales (del método `clean()`) |

> **REGLA PRÁCTICA DEL CURSO**
> Para el Sistema de Encomiendas siempre usaremos **campo por campo**.
> Los métodos `as_p` / `as_table` / `as_ul` existen y es importante conocerlos,
> pero en un sistema real con Bootstrap el control campo por campo es lo estándar.

---

## 4.3 Django Admin Site

### Configuración avanzada del Admin

```python
# envios/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Empleado, Encomienda, HistorialEstado
from config.choices import EstadoEnvio


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    # Columnas visibles en el listado
    list_display  = ('codigo', 'remitente_nombre', 'destinatario_nombre',
                     'ruta', 'estado_badge', 'peso_kg', 'fecha_registro')
    # Filtros laterales
    list_filter   = ('estado', 'ruta', 'fecha_registro')
    # Búsqueda
    search_fields = ('codigo', 'remitente__apellidos',
                     'destinatario__apellidos', 'remitente__nro_doc')
    # Campos de solo lectura
    readonly_fields = ('codigo', 'fecha_registro', 'fecha_entrega_real')
    # Ordenamiento por defecto
    ordering      = ('-fecha_registro',)
    # Registros por página
    list_per_page = 20

    # Organizar los campos en secciones (fieldsets)
    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'descripcion', 'peso_kg', 'volumen_cm3')
        }),
        ('Partes', {
            'fields': ('remitente', 'destinatario', 'ruta', 'empleado_registro')
        }),
        ('Estado y fechas', {
            'fields': ('estado', 'costo_envio',
                       'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real')
        }),
        ('Notas', {
            'classes': ('collapse',),   # sección colapsable
            'fields': ('observaciones',)
        }),
    )

    def remitente_nombre(self, obj):
        return obj.remitente.nombre_completo
    remitente_nombre.short_description = 'Remitente'

    def destinatario_nombre(self, obj):
        return obj.destinatario.nombre_completo
    destinatario_nombre.short_description = 'Destinatario'

    def estado_badge(self, obj):
        colores = {
            'PE': '#6c757d', 'TR': '#0d6efd',
            'DE': '#fd7e14', 'EN': '#198754', 'DV': '#dc3545',
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'apellidos', 'nombres', 'cargo', 'email', 'estado')
    list_filter   = ('cargo', 'estado')
    search_fields = ('codigo', 'apellidos', 'nombres', 'email')


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display   = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    readonly_fields = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    list_filter    = ('estado_nuevo',)
    ordering       = ('-fecha_cambio',)
```

### Personalizar el título del Admin

```python
# config/urls.py
from django.contrib import admin

admin.site.site_header = 'Sistema de Gestión de Encomiendas'
admin.site.site_title  = 'Encomiendas Admin'
admin.site.index_title = 'Panel de Administración'
```

> **CREAR SUPERUSUARIO EN DOCKER**
> ```bash
> docker compose exec web python manage.py createsuperuser
> # Luego accede en: http://localhost:8000/admin
> ```

---

## 4.4 Django Authentication

Django incluye un sistema de autenticación completo: modelo de usuario, login/logout, protección de vistas y gestión de permisos.

### Configuración de autenticación

```python
# config/settings.py

# URL a donde redirigir si el usuario no está autenticado
LOGIN_URL = '/accounts/login/'

# URL a donde redirigir después de un login exitoso
LOGIN_REDIRECT_URL = '/'

# URL a donde redirigir después de logout
LOGOUT_REDIRECT_URL = '/accounts/login/'
```

### Vistas de autenticación

```python
# envios/views_auth.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm


def login_view(request):
    """Vista para el login de empleados"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user     = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}!')
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Cierra la sesión del usuario"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@login_required
def perfil_view(request):
    """Perfil del empleado autenticado"""
    return render(request, 'accounts/perfil.html', {'user': request.user})
```

### Template de login

```html
{# templates/accounts/login.html #}
{% extends 'base.html' %}
{% load static %}
{% block title %}Iniciar Sesión — Encomiendas{% endblock %}

{% block content %}
<div class="row justify-content-center mt-5">
  <div class="col-md-5">
    <div class="text-center mb-4">
      <i class="fas fa-box-open fa-4x text-primary mb-3"></i>
      <h2>Sistema de Encomiendas</h2>
      <p class="text-muted">Ingresa tus credenciales para continuar</p>
    </div>
    <div class="card shadow">
      <div class="card-body p-4">
        {% if form.errors %}
        <div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>Usuario o contraseña incorrectos
        </div>
        {% endif %}

        <form method="post" action="{% url 'login' %}">
          {% csrf_token %}
          <div class="mb-3">
            <label class="form-label">Usuario</label>
            <div class="input-group">
              <span class="input-group-text"><i class="fas fa-user"></i></span>
              <input type="text" name="username" class="form-control"
                     placeholder="Tu usuario" required autofocus>
            </div>
          </div>
          <div class="mb-4">
            <label class="form-label">Contraseña</label>
            <div class="input-group">
              <span class="input-group-text"><i class="fas fa-lock"></i></span>
              <input type="password" name="password" class="form-control"
                     placeholder="Tu contraseña" required>
            </div>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary btn-lg">
              <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
            </button>
          </div>
          <input type="hidden" name="next" value="{{ next }}">
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Proteger vistas con `@login_required`

```python
from django.contrib.auth.decorators import login_required

# Forma 1: decorator en la función
@login_required
def dashboard(request): ...

# Forma 2: en urls.py (sin modificar la vista)
urlpatterns = [
    path('', login_required(views.dashboard), name='dashboard'),
]

# Forma 3: verificar manualmente dentro de la vista
def mi_vista(request):
    if not request.user.is_authenticated:
        return redirect('login')
    ...

# En los templates: verificar si el usuario está autenticado
{% if user.is_authenticated %}
    <a href="{% url 'perfil' %}">{{ user.username }}</a>
    <a href="{% url 'logout' %}">Cerrar sesión</a>
{% else %}
    <a href="{% url 'login' %}">Iniciar sesión</a>
{% endif %}
```

### Registrar URLs de autenticación

```python
# config/urls.py
urlpatterns = [
    # Opción A: URLs built-in de Django (login, logout, cambiar contraseña)
    path('accounts/', include('django.contrib.auth.urls')),

    # Opción B: Vistas propias (más control)
    path('login/',  views_auth.login_view,  name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('perfil/', views_auth.perfil_view, name='perfil'),
]

# Si usas las URLs de Django, crea el template en:
# templates/registration/login.html
```

---

## 4.5 Sesiones en Django

Las sesiones permiten almacenar datos del usuario entre peticiones HTTP. Django las guarda en la base de datos por defecto y usa una cookie en el navegador para identificarlas.

| Aspecto        | Descripción                                                     |
|----------------|-----------------------------------------------------------------|
| Almacenamiento | BD (por defecto), caché, archivo o cookies firmadas             |
| Identificación | Cookie `sessionid` en el navegador del usuario                  |
| Acceso         | `request.session` (activo en toda la aplicación)                |
| Duración       | Configurable: expira al cerrar el navegador o en X segundos     |
| Seguridad      | El contenido se guarda en el servidor, no en la cookie          |

### Uso de `request.session`

```python
# En cualquier vista: guardar datos en la sesión
def seleccionar_ruta(request):
    if request.method == 'POST':
        ruta_id = request.POST.get('ruta_id')
        request.session['ruta_seleccionada']    = ruta_id
        request.session['ultimo_filtro_estado'] = request.POST.get('estado', 'PE')

# En otra vista: leer datos de la sesión
def nueva_encomienda(request):
    ruta_id = request.session.get('ruta_seleccionada')
    if ruta_id:
        from rutas.models import Ruta
        ruta_preseleccionada = Ruta.objects.get(pk=ruta_id)

# Eliminar un valor de sesión
del request.session['ruta_seleccionada']

# Eliminar toda la sesión
request.session.flush()

# Verificar si existe una clave
if 'ultimo_filtro_estado' in request.session:
    estado = request.session['ultimo_filtro_estado']
```

### Configuración de sesiones en `settings.py`

```python
# Motor de sesiones (base de datos por defecto)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Expirar cuando el navegador se cierra
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Tiempo de vida de la sesión en segundos (8 horas = jornada laboral)
SESSION_COOKIE_AGE = 60 * 60 * 8

# Solo enviar la cookie por HTTPS (activar en producción)
SESSION_COOKIE_SECURE = False   # True en producción

# Nombre de la cookie de sesión
SESSION_COOKIE_NAME = 'encomiendas_session'

# Asegurarse de tener sessions en INSTALLED_APPS y MIDDLEWARE:
INSTALLED_APPS = [
    ...
    'django.contrib.sessions',   # <- requerido
    ...
]

MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',   # <- requerido
    ...
]
```

### Flujo completo: Login → Dashboard → Logout

```bash
# 1. Levantar los contenedores
docker compose up -d

# 2. Aplicar migraciones (incluye tabla de sesiones)
docker compose exec web python manage.py migrate

# 3. Crear un superusuario para pruebas
docker compose exec web python manage.py createsuperuser

# 4. Verificar la tabla de sesiones en psql
docker compose exec db psql -U encomiendas_user -d encomiendas_db -c '\dt django_session;'

# 5. Abrir el navegador y probar el flujo:
# http://localhost:8000/           → redirige a login (no autenticado)
# http://localhost:8000/login/     → formulario de login
# Ingresar credenciales           → redirige al dashboard
# http://localhost:8000/admin/     → panel de administración
# http://localhost:8000/logout/    → cierra sesión y redirige a login
```

### Navbar con estado de autenticación

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container">
    <a class="navbar-brand" href="{% url 'dashboard' %}">
      <i class="fas fa-shipping-fast me-2"></i>Encomiendas
    </a>

    {% if user.is_authenticated %}
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link" href="{% url 'dashboard' %}">Dashboard</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="{% url 'encomienda_lista' %}">Encomiendas</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="{% url 'encomienda_crear' %}">Nueva</a>
        </li>
      </ul>
      <div class="d-flex">
        <span class="navbar-text me-3">
          <i class="fas fa-user me-1"></i>{{ user.username }}
        </span>
        <a href="{% url 'logout' %}" class="btn btn-outline-light btn-sm">
          <i class="fas fa-sign-out-alt me-1"></i>Salir
        </a>
      </div>
    </div>
    {% else %}
    <a href="{% url 'login' %}" class="btn btn-outline-light">
      <i class="fas fa-sign-in-alt me-1"></i>Iniciar sesión
    </a>
    {% endif %}
  </div>
</nav>
```

---

## Entregable de la Sesión 4

Al finalizar las semanas 6-7 debes poder demostrar:

**URLs, Views y Templates**
1. Dashboard funcional con contadores de encomiendas activas, en tránsito y con retraso.
2. Lista de encomiendas con paginación (15 por página) y filtro por estado.
3. Detalle de encomienda mostrando info completa y el historial de estados.
4. Navbar con links al dashboard, listado y creación.

**Formularios**
5. Formulario de nueva encomienda con validación client-side y server-side.
6. `EncomiendaForm` filtra solo clientes y rutas activos.
7. Mensajes flash de éxito/error en operaciones CRUD.

**Admin Site**
8. `EncomiendaAdmin` con badges de color por estado y fieldsets.
9. Título del admin personalizado con el nombre del sistema.

**Autenticación y Sesiones**
10. Login y logout funcionando correctamente.
11. Todas las vistas protegidas con `@login_required`.
12. Navbar muestra el usuario logueado y el botón de salir.
13. Redirige a login cuando se intenta acceder sin autenticar.

---

> **Repositorio actualizado en GitHub con todos los archivos nuevos.**
