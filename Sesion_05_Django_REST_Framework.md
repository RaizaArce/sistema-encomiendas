# Taller de Lenguajes de Programación
## Sesión 05: Django REST Framework — API

---

## Introducción

Este laboratorio te guiará a través de la creación de una API RESTful completa utilizando Django REST Framework (DRF). Trabajaremos con el sistema de encomiendas existente para crear endpoints que permitan acceder y manipular datos.

**Temas que implementaremos:**

1. Serializers (incluyendo serializers dinámicos y anidados)
2. Vistas basadas en funciones y clases
3. Mixins y vistas genéricas
4. ViewSets y enrutamiento
5. Filtrado y paginación
6. Throttling
7. Autenticación y seguridad
8. Validaciones
9. Versionamiento de APIs
10. Manejo de errores y personalización de respuestas

> **PUNTO DE PARTIDA**
> Para esta sesión necesitas tener listo de sesiones anteriores:
> - Proyecto Django corriendo en Docker con PostgreSQL (Sesión 2)
> - Modelos: Cliente, Empleado, Ruta, Encomienda, HistorialEstado (Sesión 3)
> - Managers personalizados: `con_relaciones()`, `activas()`, `pendientes()` (Sesión 3)
> - Validadores y método `cambiar_estado()` en el modelo (Sesión 3)
> - Archivos `choices.py`, `validators.py` y `querysets.py` existentes

---

## Introducción a Django REST Framework

### ¿Qué es REST?

REST (Representational State Transfer) es un estilo arquitectónico para diseñar aplicaciones en red. Principios clave:

- **Sin estado:** Cada solicitud contiene toda la información necesaria para procesarla.
- **Basado en recursos:** Las API se organizan en torno a recursos (artículos, productos, usuarios).
- **Utiliza métodos HTTP estándar:** GET, POST, PUT, DELETE, etc.
- **Orientado a la representación:** Los recursos pueden tener múltiples representaciones (JSON, XML, etc.)

### ¿Qué es Django REST Framework?

DRF es un potente conjunto de herramientas para construir APIs Web en Django. Proporciona: serialización para convertir modelos a JSON/XML, autenticación y permisos, interfaz API navegable, ViewSets y routers para desarrollo rápido, y amplia documentación.

---

## Paso 1 — Instalar dependencias dentro del contenedor Docker

```bash
# 1. Asegúrate de que los contenedores están corriendo
docker compose up -d

# 2. Verificar que el contenedor web está activo
docker compose ps

# 3. Instalar las librerías dentro del contenedor
docker compose exec web pip install djangorestframework
docker compose exec web pip install djangorestframework-simplejwt
docker compose exec web pip install django-filter
docker compose exec web pip install drf-spectacular
docker compose exec web pip install django-cors-headers
```

## Paso 2 — Actualizar requirements.txt

```bash
docker compose exec web pip freeze > requirements.txt
docker compose exec web pip show djangorestframework

# El requirements.txt ahora incluirá:
# djangorestframework==3.15.x
# djangorestframework-simplejwt==5.x.x
# django-filter==24.x
# drf-spectacular==0.27.x
# django-cors-headers==4.x.x
```

## Paso 3 — Registrar las apps en settings.py

```python
# config/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del proyecto (ya existían)
    'envios',
    'clientes',
    'rutas',
    # Nuevas librerías de API <-- NUEVO
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
]
```

## Paso 4 — Configuración de DRF en settings.py

```python
# config/settings.py
from datetime import timedelta

# ── Django REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ── JWT: configuración de tokens ────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

# ── CORS ─────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # solo en desarrollo

# ── Documentación de la API ───────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE':       'API Sistema de Encomiendas',
    'DESCRIPTION': 'API REST para gestionar el ciclo de vida de encomiendas.',
    'VERSION':     '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Encomiendas', 'description': 'Gestión de envíos'},
        {'name': 'Clientes',    'description': 'Listado de clientes activos'},
        {'name': 'Rutas',       'description': 'Rutas disponibles'},
        {'name': 'Auth',        'description': 'Autenticación JWT'},
    ],
}
```

## Paso 5 — Agregar CORS al middleware

```python
# config/settings.py
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # <-- PRIMERO en la lista
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## Paso 6 — Crear la app `api` y configurar URLs

```bash
docker compose exec web python manage.py startapp api
```

```python
# api/urls.py  <-- archivo NUEVO
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
# Aquí se registrarán los ViewSets en los siguientes pasos
# router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    # Endpoints de autenticación JWT
    path('auth/token/',         TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),   name='token_refresh'),
    # Documentación interactiva
    path('schema/', SpectacularAPIView.as_view(),   name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(), name='swagger'),
    # URLs del router (ViewSets)
    path('', include(router.urls)),
]
```

```python
# config/urls.py — registrar la app api
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',          include('envios.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/v1/',   include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
```

## Paso 7 — Verificar que todo funciona

```bash
docker compose restart web
docker compose exec web python manage.py check
# Salida esperada: System check identified no issues (0 silenced).

# Probar el endpoint de login con curl:
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "tu_superuser", "password": "tu_password"}'
# Respuesta: {"access": "eyJhbGc...", "refresh": "eyJhbGc..."}
```

---

## 5.1. REST in Action — Endpoints del sistema

| Método | URL                                         | Acción                 | Status   |
|--------|---------------------------------------------|------------------------|----------|
| GET    | `/api/v1/encomiendas/`                      | Listar todas           | 200 OK   |
| POST   | `/api/v1/encomiendas/`                      | Crear nueva            | 201 Created |
| GET    | `/api/v1/encomiendas/{id}/`                 | Detalle                | 200 OK   |
| PUT    | `/api/v1/encomiendas/{id}/`                 | Actualizar completo    | 200 OK   |
| PATCH  | `/api/v1/encomiendas/{id}/`                 | Actualizar parcial     | 200 OK   |
| DELETE | `/api/v1/encomiendas/{id}/`                 | Eliminar               | 204 No Content |
| POST   | `/api/v1/encomiendas/{id}/cambiar_estado/`  | Acción personalizada   | 200 OK   |
| GET    | `/api/v1/encomiendas/con_retraso/`          | Acción de lista        | 200 OK   |
| GET    | `/api/v1/clientes/`                         | Listar clientes activos| 200 OK   |
| GET    | `/api/v1/rutas/`                            | Listar rutas activas   | 200 OK   |
| POST   | `/api/v1/auth/token/`                       | Obtener JWT            | 200 OK   |
| POST   | `/api/v1/auth/token/refresh/`              | Renovar JWT            | 200 OK   |

### Status codes HTTP más usados

| Código | Nombre                | Cuándo usarlo                            |
|--------|-----------------------|------------------------------------------|
| 200    | OK                    | GET o PUT exitoso                        |
| 201    | Created               | POST exitoso: recurso creado             |
| 204    | No Content            | DELETE exitoso: sin cuerpo de respuesta  |
| 400    | Bad Request           | Datos inválidos: errores de validación   |
| 401    | Unauthorized          | Sin token o token inválido               |
| 403    | Forbidden             | Token válido pero sin permiso            |
| 404    | Not Found             | Recurso no existe                        |
| 405    | Method Not Allowed    | Método HTTP no soportado en ese endpoint |
| 429    | Too Many Requests     | Se excedió el límite de peticiones       |
| 500    | Internal Server Error | Error no controlado en el servidor       |

---

## 5.2. Serializers y FBV con `@api_view`

Los Serializers convierten objetos Python (instancias de modelo) a JSON y viceversa. Son el equivalente de los formularios de Django pero para APIs.

### 5.2.1 ModelSerializer

Un `ModelSerializer` crea campos automáticamente basándose en el modelo, genera validadores predeterminados e incluye implementaciones de `.create()` y `.update()`.

```python
# envios/serializers.py
from rest_framework import serializers
from .models import Encomienda, HistorialEstado, Empleado
from clientes.models import Cliente
from rutas.models import Ruta


class ClienteSerializer(serializers.ModelSerializer):
    # @property del modelo expuesta como campo de solo lectura
    nombre_completo = serializers.ReadOnlyField()
    esta_activo     = serializers.ReadOnlyField()

    class Meta:
        model  = Cliente
        fields = [
            'id', 'tipo_doc', 'nro_doc',
            'nombres', 'apellidos', 'nombre_completo',
            'telefono', 'email', 'esta_activo',
        ]


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Ruta
        fields = ['id', 'codigo', 'origen', 'destino', 'precio_base', 'dias_entrega', 'estado']


class HistorialEstadoSerializer(serializers.ModelSerializer):
    empleado_nombre        = serializers.ReadOnlyField(source='empleado.__str__')
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display    = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model  = HistorialEstado
        fields = [
            'id', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display',
            'empleado_nombre', 'observacion', 'fecha_cambio',
        ]


class EncomiendaSerializer(serializers.ModelSerializer):
    # Campos de solo escritura: aceptar ID para crear/actualizar
    remitente_id    = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente_id', 'destinatario_id', 'ruta_id',
            'estado', 'costo_envio', 'fecha_registro',
            'fecha_entrega_est', 'fecha_entrega_real', 'observaciones',
        ]
        read_only_fields = ['codigo', 'fecha_registro']
```

### 5.2.2 FBV con `@api_view`

El decorador `@api_view` convierte funciones en endpoints REST. Maneja: filtrado de métodos, análisis de la solicitud, negociación de contenido y gestión de errores.

```python
# envios/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Encomienda
from .serializers import EncomiendaSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list(request):
    if request.method == 'GET':
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(empleado_registro=request.user.empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def encomienda_detail(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'GET':
        return Response(EncomiendaSerializer(enc).data)

    elif request.method in ['PUT', 'PATCH']:
        s = EncomiendaSerializer(enc, data=request.data, partial=(request.method == 'PATCH'))
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    elif request.method == 'DELETE':
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## 5.3. Class Based Views — APIView

`APIView` es la clase base CBV de DRF. Organiza la lógica en métodos `get()`, `post()`, `put()`, etc. Gestiona automáticamente la autenticación, permisos, negociación de contenido y errores.

```python
# envios/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Encomienda
from .serializers import EncomiendaSerializer, EncomiendaDetailSerializer


class EncomiendaListAPIView(APIView):
    """GET /api/v1/encomiendas/   POST /api/v1/encomiendas/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(empleado_registro=request.user.empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncomiendaDetailAPIView(APIView):
    """GET/PUT/PATCH/DELETE /api/v1/encomiendas/{pk}/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)

    def get(self, request, pk):
        enc = self.get_object(pk)
        return Response(EncomiendaDetailSerializer(enc).data)

    def put(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(enc, data=request.data, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def patch(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(enc, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        enc = self.get_object(pk)
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## 5.4. Mixins

Los Mixins aportan métodos concretos y se combinan con `GenericAPIView`. La ventaja sobre `APIView` es que los métodos CRUD ya están implementados.

| Mixin                  | Método que aporta           | Equivale a                |
|------------------------|-----------------------------|---------------------------|
| `ListModelMixin`       | `list()`                    | GET `/recursos/`          |
| `CreateModelMixin`     | `create()`                  | POST `/recursos/`         |
| `RetrieveModelMixin`   | `retrieve()`                | GET `/recursos/{pk}/`     |
| `UpdateModelMixin`     | `update()` + `partial_update()` | PUT/PATCH `/recursos/{pk}/` |
| `DestroyModelMixin`    | `destroy()`                 | DELETE `/recursos/{pk}/`  |

```python
# envios/api_views.py
from rest_framework import mixins, generics
from rest_framework.permissions import IsAuthenticated
from .models import Encomienda
from .serializers import EncomiendaSerializer


# ── List + Create ─────────────────────────────────────────────────
class EncomiendaListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset            = Encomienda.objects.con_relaciones()
    serializer_class    = EncomiendaSerializer
    permission_classes  = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)


# ── Retrieve + Update + Destroy ───────────────────────────────────
class EncomiendaDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    queryset            = Encomienda.objects.con_relaciones()
    serializer_class    = EncomiendaSerializer
    permission_classes  = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
```

---

## 5.5. Vistas Genéricas

Las vistas genéricas son combinaciones predefinidas de Mixins + GenericAPIView. Permiten implementar un CRUD completo con muy pocas líneas.

| Vista genérica                    | Métodos HTTP              | Descripción          |
|-----------------------------------|---------------------------|----------------------|
| `ListAPIView`                     | GET                       | Solo listar          |
| `CreateAPIView`                   | POST                      | Solo crear           |
| `RetrieveAPIView`                 | GET `/{pk}`               | Solo detalle         |
| `UpdateAPIView`                   | PUT/PATCH `/{pk}`         | Solo actualizar      |
| `DestroyAPIView`                  | DELETE `/{pk}`            | Solo eliminar        |
| `ListCreateAPIView`               | GET + POST                | Listar y crear       |
| `RetrieveUpdateAPIView`           | GET + PUT/PATCH `/{pk}`   | Detalle y actualizar |
| `RetrieveDestroyAPIView`          | GET + DELETE `/{pk}`      | Detalle y eliminar   |
| `RetrieveUpdateDestroyAPIView`    | GET + PUT + PATCH + DELETE `/{pk}` | Detalle completo |

```python
# envios/api_views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Encomienda
from clientes.models import Cliente
from rutas.models import Ruta
from .serializers import EncomiendaSerializer, EncomiendaDetailSerializer, ClienteSerializer, RutaSerializer


class EncomiendaListCreateView(generics.ListCreateAPIView):
    queryset            = Encomienda.objects.con_relaciones()
    serializer_class    = EncomiendaSerializer
    permission_classes  = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)


class EncomiendaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset            = Encomienda.objects.con_relaciones()
    permission_classes  = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EncomiendaDetailSerializer   # con objetos anidados
        return EncomiendaSerializer             # solo IDs para escritura


class ClienteListView(generics.ListAPIView):
    serializer_class   = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.activos()


class RutaListView(generics.ListAPIView):
    serializer_class   = RutaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ruta.objects.activas()
```

---

## 6.1. ViewSets y Router

Un ViewSet agrupa en una sola clase todos los endpoints de un recurso. El Router genera automáticamente las URLs del CRUD.

**Tipos de ViewSets:**
- **`ViewSet`**: Clase más básica, debes definir las acciones manualmente.
- **`GenericViewSet`**: Hereda de `GenericAPIView`, permite usar mixins.
- **`ReadOnlyModelViewSet`**: Solo `list` y `retrieve`.
- **`ModelViewSet`**: Todas las operaciones CRUD completas.

**Tipos de Routers:**
- **`SimpleRouter`**: Genera rutas básicas para CRUD.
- **`DefaultRouter`**: Igual al SimpleRouter más una vista raíz con todos los enlaces.

```python
# envios/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Encomienda, Empleado
from .serializers import EncomiendaSerializer, EncomiendaDetailSerializer
from config.choices import EstadoEnvio


class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet genera automáticamente:
    list()          → GET    /encomiendas/
    create()        → POST   /encomiendas/
    retrieve()      → GET    /encomiendas/{pk}/
    update()        → PUT    /encomiendas/{pk}/
    partial_update()→ PATCH  /encomiendas/{pk}/
    destroy()       → DELETE /encomiendas/{pk}/
    """
    queryset            = Encomienda.objects.con_relaciones()
    serializer_class    = EncomiendaSerializer
    permission_classes  = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)

    # ── Acción de detalle: POST /encomiendas/{pk}/cambiar_estado/
    @action(detail=True, methods=['post'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        enc          = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response({'error': 'El campo estado es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            return Response(EncomiendaSerializer(enc).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── Acción de lista: GET /encomiendas/con_retraso/
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        qs = Encomienda.objects.con_retraso().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)

    # ── Acción de lista: GET /encomiendas/pendientes/
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        qs = Encomienda.objects.pendientes().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)


# ── Router: registrar el ViewSet ─────────────────────────────────
# api/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from envios.viewsets import EncomiendaViewSet
from . import api_views

router = DefaultRouter()
router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    path('', include(router.urls)),
    path('clientes/', api_views.ClienteListView.as_view()),
    path('rutas/',    api_views.RutaListView.as_view()),
]
```

---

## 6.2. Nested Serializers

Un nested serializer representa relaciones entre modelos devolviendo el objeto relacionado completo en lugar de solo su ID.

```python
# envios/serializers.py
class EncomiendaDetailSerializer(serializers.ModelSerializer):
    """
    Para GET: devuelve objetos anidados completos
    Para POST/PUT/PATCH: acepta solo IDs (write_only)
    """
    # Campos de solo lectura: objetos anidados completos
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    # Campos de solo escritura: aceptar ID para crear/actualizar
    remitente_id    = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    # Historial: los últimos 5 cambios de estado
    historial        = serializers.SerializerMethodField()
    esta_entregada   = serializers.ReadOnlyField()
    tiene_retraso    = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg',
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'estado', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            'historial', 'observaciones',
        ]

    def get_historial(self, obj):
        return HistorialEstadoSerializer(obj.historial.all()[:5], many=True).data
```

---

## 6.3. Paginación

```python
# api/pagination.py
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination


class EncomiendaPagination(PageNumberPagination):
    """Uso: GET /api/v1/encomiendas/?page=2&page_size=30"""
    page_size             = 15
    page_size_query_param = 'page_size'
    max_page_size         = 100
    page_query_param      = 'page'


class ClientePagination(PageNumberPagination):
    """Uso: GET /api/v1/clientes/?page=2"""
    page_size             = 20
    page_size_query_param = 'page_size'
    max_page_size         = 50


class HistorialPagination(LimitOffsetPagination):
    """Uso: GET /api/v1/encomiendas/1/historial/?limit=5&offset=10"""
    default_limit = 10
    max_limit     = 50


class EncomiendaCursorPagination(CursorPagination):
    """Paginación eficiente para grandes volúmenes."""
    page_size = 15
    ordering  = '-fecha_registro'
```

**Aplicar en el ViewSet:**

```python
# envios/viewsets.py
from api.pagination import EncomiendaPagination, HistorialPagination

class EncomiendaViewSet(viewsets.ModelViewSet):
    pagination_class = EncomiendaPagination   # 15 por página

    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        """GET /api/v1/encomiendas/{pk}/historial/?limit=5&offset=10"""
        enc       = self.get_object()
        qs        = enc.historial.select_related('empleado').order_by('-fecha_cambio')
        paginator = HistorialPagination()
        page      = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = HistorialEstadoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        return Response(HistorialEstadoSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """GET /api/v1/encomiendas/estadisticas/ — sin paginación"""
        from django.utils import timezone
        hoy = timezone.now().date()
        return Response({
            'total_activas':  Encomienda.objects.activas().count(),
            'en_transito':    Encomienda.objects.en_transito().count(),
            'con_retraso':    Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(estado='EN', fecha_entrega_real=hoy).count(),
        })
```

**Formato de respuesta paginada:**

```json
{
    "count": 120,
    "next": "http://localhost:8000/api/v1/encomiendas/?page=2",
    "previous": null,
    "results": [
        {"id": 45, "codigo": "ENC-2026-045", "estado": "TR", ...}
    ]
}
```

---

## 6.4. Filtering

```python
# api/filters.py
from django_filters.rest_framework import FilterSet, CharFilter, ChoiceFilter
from django.utils import timezone
from envios.models import Encomienda
from config.choices import EstadoEnvio

class EncomiendaFilter(FilterSet):
    estado      = ChoiceFilter(choices=EstadoEnvio.choices)
    ruta        = CharFilter(field_name='ruta__codigo', lookup_expr='iexact')
    remitente   = CharFilter(field_name='remitente__nro_doc')
    desde       = CharFilter(field_name='fecha_registro__date', lookup_expr='gte')
    hasta       = CharFilter(field_name='fecha_registro__date', lookup_expr='lte')
    con_retraso = CharFilter(method='filter_retraso')

    def filter_retraso(self, queryset, name, value):
        if value.lower() == 'true':
            return queryset.con_retraso()
        return queryset

    class Meta:
        model  = Encomienda
        fields = ['estado', 'ruta', 'remitente', 'desde', 'hasta']
```

```python
# envios/viewsets.py
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from api.filters import EncomiendaFilter

class EncomiendaViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EncomiendaFilter
    search_fields   = ['codigo', 'remitente__apellidos', 'destinatario__apellidos', 'descripcion']
    ordering_fields = ['fecha_registro', 'peso_kg', 'costo_envio']
    ordering        = ['-fecha_registro']

# Ejemplos de uso:
# GET /api/v1/encomiendas/?estado=TR
# GET /api/v1/encomiendas/?search=Lima
# GET /api/v1/encomiendas/?ordering=-peso_kg
# GET /api/v1/encomiendas/?desde=2026-01-01&hasta=2026-04-30
# GET /api/v1/encomiendas/?con_retraso=true
```

---

## 6.5. Seguridad y Autenticación

### 6.5.1 JWT con SimpleJWT

```python
# config/settings.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES':        ('Bearer',),
}
```

```python
# config/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

urlpatterns += [
    path('api/v1/auth/token/',           TokenObtainPairView.as_view(),   name='token_obtain'),
    path('api/v1/auth/token/refresh/',   TokenRefreshView.as_view(),      name='token_refresh'),
    path('api/v1/auth/token/blacklist/', TokenBlacklistView.as_view(),    name='token_blacklist'),
]
```

**JWT personalizado con datos del empleado:**

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class EncomiendaTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email']    = user.email
        try:
            emp = user.empleado
            token['empleado_id']  = emp.id
            token['empleado_cod'] = emp.codigo
            token['cargo']        = emp.cargo
        except Exception:
            pass
        return token

class EncomiendaTokenView(TokenObtainPairView):
    serializer_class = EncomiendaTokenSerializer
```

**Flujo de autenticación:**

```bash
# 1. Obtener tokens:
# POST /api/v1/auth/token/
# Body: {"username": "juan", "password": "secret"}
# Respuesta: {"access": "eyJhbGc...", "refresh": "eyJhbGc..."}

# 2. Usar el token en cada request:
# GET /api/v1/encomiendas/
# Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5...

# 3. Renovar cuando expira:
# POST /api/v1/auth/token/refresh/
# Body: {"refresh": "eyJhbGc..."}
```

### 6.5.2 Permisos personalizados

```python
# api/permissions.py
from rest_framework.permissions import BasePermission
from envios.models import Empleado

class EsEmpleadoActivo(BasePermission):
    """Solo empleados activos del sistema pueden acceder"""
    message = 'Solo empleados activos tienen acceso a esta API.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return Empleado.objects.filter(email=request.user.email, estado=1).exists()


class EsPropietarioOAdmin(BasePermission):
    """El usuario puede ver/editar solo sus propias encomiendas, a menos que sea admin"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.empleado_registro.email == request.user.email


# Uso en el ViewSet
class EncomiendaViewSet(viewsets.ModelViewSet):
    permission_classes = [EsEmpleadoActivo]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [EsEmpleadoActivo(), EsPropietarioOAdmin()]
        return [EsEmpleadoActivo()]
```

### 6.5.3 HttpOnly Cookies

```python
# envios/api_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class LoginCookieView(APIView):
    permission_classes = []

    def post(self, request):
        user = authenticate(username=request.data.get('username'), password=request.data.get('password'))
        if not user:
            return Response({'error': 'Credenciales inválidas.'}, status=401)

        refresh  = RefreshToken.for_user(user)
        response = Response({'message': 'Login exitoso.'})
        response.set_cookie(key='access_token',  value=str(refresh.access_token),
                            httponly=True, secure=True, samesite='Lax', max_age=3600)
        response.set_cookie(key='refresh_token', value=str(refresh),
                            httponly=True, secure=True, samesite='Lax', max_age=604800)
        return response


class LogoutCookieView(APIView):
    def post(self, request):
        response = Response({'message': 'Logout exitoso.'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
```

---

## 6.6. Validaciones en Serializers

| Nivel                   | Método               | Cuándo usarlo                              |
|-------------------------|----------------------|--------------------------------------------|
| Validators en el campo  | `validators=[...]`   | Reglas simples y reutilizables             |
| Validación de campo     | `validate_{nombre}()`| Regla sobre un campo específico            |
| Validación cruzada      | `validate()`         | Reglas que involucran más de un campo      |

```python
# envios/serializers.py
class EncomiendaSerializer(serializers.ModelSerializer):

    # ── Validator de campo: validate_{nombre} ───────────────────────
    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0 kg.')
        if value > 500:
            raise serializers.ValidationError('El peso máximo permitido es 500 kg.')
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError('El código debe comenzar con ENC-')
        return value.upper()

    def validate_costo_envio(self, value):
        if value < 0:
            raise serializers.ValidationError('El costo no puede ser negativo.')
        return value

    # ── Validación cruzada: validate() ──────────────────────────────
    def validate(self, data):
        errors = {}

        if data.get('remitente') == data.get('destinatario'):
            errors['destinatario'] = 'El destinatario no puede ser el mismo que el remitente.'

        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = 'La fecha estimada no puede ser en el pasado.'

        ruta  = data.get('ruta')
        costo = data.get('costo_envio')
        if ruta and costo and costo < float(ruta.precio_base):
            errors['costo_envio'] = f'El costo mínimo para esta ruta es S/ {ruta.precio_base}.'

        if errors:
            raise serializers.ValidationError(errors)
        return data
```

---

## 6.7. Documentación de la API con drf-spectacular

`drf-spectacular` genera documentación OpenAPI 3.0 automáticamente. Produce una interfaz Swagger UI interactiva.

```bash
# Verificar instalación
docker compose exec web pip show drf-spectacular

# Generar y validar el schema
docker compose exec web python manage.py spectacular --validate
# Resultado: 'Schema validated successfully!'

# Exportar el schema a YAML
docker compose exec web python manage.py spectacular --file schema.yml
```

**URLs en el navegador:**
- `http://localhost:8000/api/docs/` → Swagger UI (interactiva)
- `http://localhost:8000/api/redoc/` → ReDoc (solo lectura)
- `http://localhost:8000/api/schema/` → Schema raw YAML

**Anotar el ViewSet con `@extend_schema`:**

```python
# envios/viewsets.py
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

@extend_schema_view(
    list=extend_schema(summary='Listar encomiendas', tags=['Encomiendas']),
    create=extend_schema(summary='Crear encomienda', tags=['Encomiendas']),
    retrieve=extend_schema(summary='Detalle de encomienda', tags=['Encomiendas']),
    update=extend_schema(summary='Actualizar encomienda', tags=['Encomiendas']),
    partial_update=extend_schema(summary='Actualizar parcial', tags=['Encomiendas']),
    destroy=extend_schema(summary='Eliminar encomienda', tags=['Encomiendas']),
)
class EncomiendaViewSet(viewsets.ModelViewSet):
    ...

    @extend_schema(
        summary='Cambiar estado de encomienda',
        description='Cambia el estado y registra el cambio en el historial. Estados: PE, TR, DE, EN, DV.',
        responses={200: EncomiendaSerializer, 400: OpenApiResponse(description='Estado inválido')},
        examples=[
            OpenApiExample('Pasar a En tránsito', value={'estado': 'TR', 'observacion': 'Recogido en agencia Lima'}, request_only=True),
            OpenApiExample('Marcar como Entregado', value={'estado': 'EN', 'observacion': 'Entregado al destinatario'}, request_only=True),
        ],
        tags=['Encomiendas'],
    )
    @action(detail=True, methods=['post'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        ...
```

| Característica | Swagger UI                            | ReDoc                            |
|----------------|---------------------------------------|----------------------------------|
| Interactividad | Permite probar endpoints (Try it out) | Solo lectura                     |
| Autenticación  | Botón Authorize integrado             | No aplica                        |
| Mejor para     | Desarrollo y pruebas del equipo       | Documentar a clientes externos   |

---

## 6.8. API Versioning

El versionado permite introducir cambios sin romper los clientes que consumen la v1. La v1 devuelve solo IDs; la v2 devuelve objetos anidados completos y campos adicionales.

```python
# config/settings.py
REST_FRAMEWORK = {
    # ... claves ya existentes ...
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'DEFAULT_VERSION':  'v1',
    'VERSION_PARAM':    'version',
}
```

```python
# config/urls.py
# La URL captura la versión dinámicamente
urlpatterns = [
    path('api/<version>/', include('api.urls')),
    # Auth JWT (igual para todas las versiones)
    path('api/v1/auth/token/',         TokenObtainPairView.as_view()),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view()),
]
# GET /api/v1/encomiendas/ <- versión 1
# GET /api/v2/encomiendas/ <- versión 2
```

**Serializer para v2:**

```python
# envios/serializers.py
class EncomiendaV2Serializer(serializers.ModelSerializer):
    """v2: objetos anidados + campos de análisis + meta"""
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    # Para escritura: seguir aceptando IDs
    remitente_id    = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.activos(), write_only=True, source='remitente')
    destinatario_id = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.activos(), write_only=True, source='destinatario')
    ruta_id         = serializers.PrimaryKeyRelatedField(queryset=Ruta.objects.activas(), write_only=True, source='ruta')

    dias_en_transito  = serializers.ReadOnlyField()
    tiene_retraso     = serializers.ReadOnlyField()
    esta_entregada    = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()
    meta              = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta', 'peso_kg', 'costo_envio',
            'remitente', 'remitente_id', 'destinatario', 'destinatario_id', 'ruta', 'ruta_id',
            'estado', 'fecha_registro', 'dias_en_transito', 'tiene_retraso', 'esta_entregada',
            'observaciones', 'meta',
        ]

    def get_meta(self, obj):
        from django.utils import timezone
        return {
            'version':     'v2',
            'generado':    timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'puede_editar': not obj.esta_entregada,
        }
```

**ViewSet con manejo de versiones:**

```python
class EncomiendaViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        version = getattr(self.request, 'version', 'v1')
        if version == 'v2':
            return EncomiendaV2Serializer
        if self.action == 'list':
            return EncomiendaListSerializer
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['X-API-Version'] = getattr(request, 'version', 'v1')
        return response
```

**Esquemas de versionado disponibles:**

| Esquema                   | Cómo se usa                           | Cuándo elegirlo                        |
|---------------------------|---------------------------------------|----------------------------------------|
| `URLPathVersioning`       | `GET /api/v2/encomiendas/`            | Proyectos nuevos. URL clara, cacheable |
| `AcceptHeaderVersioning`  | `Accept: application/json; version=v2`| APIs públicas. URL limpia              |
| `QueryParameterVersioning`| `GET /api/encomiendas/?version=v2`    | Prototipado rápido                     |
| `HostNameVersioning`      | `v2.api.encomiendas.pe/encomiendas/`  | Grandes plataformas con subdominios    |

---

## 6.9. Testing de APIs con DRF

DRF provee `APIClient` para simular peticiones HTTP sin levantar un servidor real.

```bash
# Agregar al requirements.txt
pytest-django==4.8.0
factory-boy==3.3.0
faker==24.0.0

docker compose down && docker compose build && docker compose up -d
```

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files  = tests.py test_*.py *_tests.py
python_classes = *Tests
python_functions = test_*
addopts = -v --tb=short
```

```python
# conftest.py (raiz del proyecto)
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='test_empleado', email='empleado@enc.pe', password='test1234')

@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client
```

```python
# envios/tests/factories.py
import factory
from decimal import Decimal
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from clientes.models import Cliente
from rutas.models import Ruta
from envios.models import Empleado, Encomienda
from config.choices import EstadoGeneral, TipoDocumento

class ClienteFactory(DjangoModelFactory):
    class Meta: model = Cliente
    tipo_doc  = TipoDocumento.DNI
    nro_doc   = factory.Sequence(lambda n: f'{10000000 + n}')
    nombres   = factory.Faker('first_name', locale='es_PE')
    apellidos = factory.Faker('last_name',  locale='es_PE')
    estado    = EstadoGeneral.ACTIVO

class RutaFactory(DjangoModelFactory):
    class Meta: model = Ruta
    codigo      = factory.Sequence(lambda n: f'RUT-{n:03d}')
    origen      = 'Lima'
    destino     = factory.Sequence(lambda n: f'Ciudad-{n}')
    precio_base = Decimal('25.00')
    dias_entrega = 2
    estado      = EstadoGeneral.ACTIVO

class EmpleadoFactory(DjangoModelFactory):
    class Meta: model = Empleado
    codigo        = factory.Sequence(lambda n: f'EMP-{n:03d}')
    nombres       = factory.Faker('first_name', locale='es_PE')
    apellidos     = factory.Faker('last_name',  locale='es_PE')
    cargo         = 'Operador de Envios'
    email         = factory.LazyAttribute(lambda o: f'{o.codigo}@enc.pe')
    fecha_ingreso = factory.Faker('date_this_decade')
    estado        = EstadoGeneral.ACTIVO

class EncomiendaFactory(DjangoModelFactory):
    class Meta: model = Encomienda
    codigo             = factory.Sequence(lambda n: f'ENC-2026-{n:04d}')
    descripcion        = factory.Faker('sentence', locale='es_PE')
    peso_kg            = Decimal('3.50')
    remitente          = factory.SubFactory(ClienteFactory)
    destinatario       = factory.SubFactory(ClienteFactory)
    ruta               = factory.SubFactory(RutaFactory)
    empleado_registro  = factory.SubFactory(EmpleadoFactory)
    costo_envio        = Decimal('25.00')
    estado             = 'PE'
```

**Ejecutar los tests:**

```bash
# Todos los tests
docker compose exec web pytest

# Una clase específica
docker compose exec web pytest envios/tests/test_api.py::TestCrearEncomienda -v

# Por palabra clave
docker compose exec web pytest -k 'estado' -v

# Detener al primer fallo
docker compose exec web pytest -x

# Con cobertura
docker compose exec web pytest --cov=envios --cov-report=term-missing
```

---

## 6.10. Throttling — Control de tasa de peticiones

El throttling limita el número de peticiones que un cliente puede hacer en un período de tiempo.

```python
# config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':          '20/hour',    # 20 requests/hora para no autenticados
        'user':          '500/hour',   # 500 requests/hora para autenticados
        'empleado':      '100/min',
        'cambio_estado': '30/hour',
        'login_attempt': '5/min',
    }
}
```

```python
# api/throttles.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """Limitar intentos de login: 5 por minuto"""
    scope = 'login_attempt'

class EmpleadoRateThrottle(UserRateThrottle):
    """Empleados: 100 peticiones por minuto"""
    scope = 'empleado'

class CambioEstadoThrottle(UserRateThrottle):
    """Limitar cambios de estado: 30 por hora"""
    scope = 'cambio_estado'


# Aplicar en el ViewSet
from api.throttles import EmpleadoRateThrottle, CambioEstadoThrottle

class EncomiendaViewSet(viewsets.ModelViewSet):
    throttle_classes = [EmpleadoRateThrottle]

    def get_throttles(self):
        if self.action == 'cambiar_estado':
            return [CambioEstadoThrottle()]
        return super().get_throttles()


# Aplicar en el endpoint de login
class EncomiendaTokenView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
    serializer_class = EncomiendaTokenSerializer

# Respuesta cuando se supera el límite (status 429):
# {"detail": "Request was throttled. Expected available in 42 seconds."}
# Header: Retry-After: 42
```

---

## 6.11. Manejo de Errores Personalizado

Un exception handler personalizado garantiza que TODA la API devuelve errores con el mismo formato JSON.

```python
# api/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def encomiendas_exception_handler(exc, context):
    """
    Devuelve siempre el mismo formato:
    {
        'error': True,
        'code': 'VALIDATION_ERROR',
        'message': 'Descripción legible del error',
        'detail': { ...errores por campo... }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = 'API_ERROR'
        message    = 'Ha ocurrido un error procesando la solicitud.'

        if response.status_code == 400:
            error_code, message = 'VALIDATION_ERROR', 'Los datos enviados contienen errores de validación.'
        elif response.status_code == 401:
            error_code, message = 'AUTHENTICATION_REQUIRED', 'Se requiere autenticación para acceder.'
        elif response.status_code == 403:
            error_code, message = 'PERMISSION_DENIED', 'No tienes permiso para realizar esta acción.'
        elif response.status_code == 404:
            error_code, message = 'NOT_FOUND', 'El recurso solicitado no existe.'
        elif response.status_code == 429:
            error_code, message = 'RATE_LIMIT_EXCEEDED', 'Se excedió el límite de solicitudes.'

        response.data = {
            'error':   True,
            'code':    error_code,
            'message': message,
            'detail':  response.data,
        }
        return response

    # Error no controlado: loggear y devolver 500
    logger.error(f'Error no controlado en {context["view"].__class__.__name__}: {exc}', exc_info=True)
    return Response({
        'error': True, 'code': 'INTERNAL_ERROR',
        'message': 'Error interno del servidor.', 'detail': None,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

```python
# config/settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.exceptions.encomiendas_exception_handler',
}
```

**Excepciones personalizadas de negocio:**

```python
# api/exceptions.py
from rest_framework.exceptions import APIException

class EstadoInvalidoError(APIException):
    status_code  = 422
    default_code = 'ESTADO_INVALIDO'
    default_detail = 'La transición de estado no está permitida.'

class EncomiendaYaEntregadaError(APIException):
    status_code  = 409
    default_code = 'YA_ENTREGADA'
    default_detail = 'La encomienda ya fue entregada y no puede modificarse.'
```

---

## 6.12. CORS — Cross-Origin Resource Sharing

```bash
pip install django-cors-headers
```

```python
# config/settings.py
INSTALLED_APPS = [..., 'corsheaders']

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # <- PRIMERO
    'django.middleware.common.CommonMiddleware',
    ...
]

# Desarrollo
CORS_ALLOW_ALL_ORIGINS = True

# Producción
CORS_ALLOW_ALL_ORIGINS  = False
CORS_ALLOWED_ORIGINS    = [
    'https://encomiendas-frontend.vercel.app',
    'http://localhost:3000',   # React en desarrollo
    'http://localhost:5173',   # Vite en desarrollo
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS     = ['accept', 'authorization', 'content-type', 'x-csrftoken', 'x-requested-with']
CORS_ALLOW_METHODS     = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
```

---

## 6.13. Serializers Avanzados

### `to_representation()` — Personalizar la salida JSON

```python
# envios/serializers.py
class EncomiendaSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Agregar campos calculados del modelo
        data['ruta_codigo']  = instance.ruta.codigo
        data['ruta_destino'] = instance.ruta.destino
        data['ruta_origen']  = instance.ruta.origen
        data['costo_display'] = f'S/ {instance.costo_envio:.2f}'

        # Badge de color según el estado
        colores = {'PE': 'gray', 'TR': 'blue', 'DE': 'orange', 'EN': 'green', 'DV': 'red'}
        data['estado_color'] = colores.get(instance.estado, 'gray')

        # Ocultar campos sensibles para usuarios no-staff
        request = self.context.get('request')
        if request and not request.user.is_staff:
            data.pop('observaciones', None)
            data.pop('empleado_registro', None)

        return data
```

### `to_internal_value()` — Normalizar datos entrantes

```python
    def to_internal_value(self, data):
        # 1. Convertir el código a mayúsculas
        if 'codigo' in data and data['codigo']:
            data['codigo'] = str(data['codigo']).upper().strip()

        # 2. Limpiar la descripcion: quitar espacios extra
        if 'descripcion' in data and data['descripcion']:
            data['descripcion'] = str(data['descripcion']).strip()

        # 3. Normalizar costo a 2 decimales
        if 'costo_envio' in data and data['costo_envio']:
            try:
                from decimal import Decimal, ROUND_HALF_UP
                costo = Decimal(str(data['costo_envio']))
                data['costo_envio'] = str(costo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except Exception:
                pass

        return super().to_internal_value(data)
```

### Bulk operations con `ListSerializer`

```python
# envios/serializers.py
class EncomiendaBulkSerializer(serializers.ListSerializer):
    """Se activa automáticamente cuando se usa EncomiendaSerializer(many=True)."""

    def create(self, validated_data):
        """Crear múltiples encomiendas con una sola query SQL."""
        encomiendas = [Encomienda(**item) for item in validated_data]
        return Encomienda.objects.bulk_create(encomiendas)

    def update(self, instances, validated_data):
        instance_map = {enc.id: enc for enc in instances}
        updated = []
        for item in validated_data:
            enc_id = item.pop('id', None)
            enc    = instance_map.get(enc_id)
            if enc:
                for campo, valor in item.items():
                    setattr(enc, campo, valor)
                updated.append(enc)
        if updated:
            Encomienda.objects.bulk_update(updated, ['estado', 'observaciones', 'costo_envio'])
        return updated


class EncomiendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encomienda
        fields = [...]
        list_serializer_class = EncomiendaBulkSerializer   # activa el bulk serializer
```

**Acciones bulk en el ViewSet:**

```python
@action(detail=False, methods=['post'], url_path='bulk_create')
def bulk_create(self, request):
    """POST /api/v1/encomiendas/bulk_create/ — Body: [{enc1}, {enc2}]"""
    serializer = self.get_serializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    empleado    = Empleado.objects.get(email=request.user.email)
    encomiendas = serializer.save(empleado_registro=empleado)
    return Response(self.get_serializer(encomiendas, many=True).data, status=status.HTTP_201_CREATED)


@action(detail=False, methods=['patch'], url_path='bulk_estado')
def bulk_estado(self, request):
    """PATCH /api/v1/encomiendas/bulk_estado/ — Body: {"ids": [1,2,3], "estado": "TR"}"""
    ids          = request.data.get('ids', [])
    nuevo_estado = request.data.get('estado')
    observacion  = request.data.get('observacion', '')

    empleado     = Empleado.objects.get(email=request.user.email)
    encomiendas  = Encomienda.objects.filter(id__in=ids)
    actualizadas, errores = [], []

    for enc in encomiendas:
        try:
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            actualizadas.append(enc.id)
        except ValueError as e:
            errores.append({'id': enc.id, 'error': str(e)})

    ids_procesados = list(encomiendas.values_list('id', flat=True))
    no_encontrados = [i for i in ids if i not in ids_procesados]

    return Response({
        'actualizadas':   actualizadas,
        'errores':        errores,
        'no_encontrados': no_encontrados,
        'total':          len(actualizadas),
    })
```

---

## 6.14. Optimización de Consultas — Problema N+1

El problema N+1 ocurre cuando se hacen N consultas adicionales para acceder a datos relacionados. Con 100 encomiendas, acceder a `enc.remitente.nombre` genera 101 queries en lugar de 2.

```sql
-- SIN OPTIMIZAR: 61 queries para 15 encomiendas
SELECT * FROM encomiendas LIMIT 15;
SELECT * FROM clientes WHERE id = 5;   -- query 2
SELECT * FROM clientes WHERE id = 12;  -- query 3
-- ... repite para cada encomienda ...
```

**La solución — `con_relaciones()`:**

```python
# envios/querysets.py (ya existe desde la Sesión 3)
class EncomiendaQuerySet(models.QuerySet):
    def con_relaciones(self):
        """
        Sin esto: 1 + N*4 queries (N = número de encomiendas)
        Con esto: 2 queries siempre, sin importar cuántas encomiendas haya
        """
        return self.select_related(
            'remitente', 'destinatario', 'ruta', 'empleado_registro'
        ).prefetch_related(
            'historial', 'historial__empleado'
        )
```

```python
# Verificar desde el shell
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True

# SIN OPTIMIZAR
reset_queries()
encomiendas = list(Encomienda.objects.all()[:15])
for enc in encomiendas:
    _ = enc.remitente.nombre_completo
print(f'Queries: {len(connection.queries)}')  # 61

# CON OPTIMIZACIÓN
reset_queries()
encomiendas = list(Encomienda.objects.con_relaciones()[:15])
for enc in encomiendas:
    _ = enc.remitente.nombre_completo
print(f'Queries: {len(connection.queries)}')  # 2
```

**Resultados finales:**
- Listado: **2 queries en lugar de 61** (reducción del 96%)
- Tiempo respuesta: **~8ms en lugar de ~180ms**

**Serializer ligero para el listado:**

```python
class EncomiendaListSerializer(serializers.ModelSerializer):
    """Solo los campos necesarios para mostrar la tabla del listado."""
    remitente_nombre    = serializers.ReadOnlyField(source='remitente.nombre_completo')
    destinatario_nombre = serializers.ReadOnlyField(source='destinatario.nombre_completo')
    ruta_destino        = serializers.ReadOnlyField(source='ruta.destino')
    estado_display      = serializers.SerializerMethodField()
    tiene_retraso       = serializers.ReadOnlyField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'estado', 'estado_display',
            'remitente_nombre', 'destinatario_nombre',
            'ruta_destino', 'peso_kg', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'tiene_retraso',
        ]

    def get_estado_display(self, obj):
        return obj.get_estado_display()
```

---

## 6.15. Caching con Redis

Redis almacena temporalmente los resultados de endpoints costosos. Es compartido entre todos los workers.

```yaml
# docker-compose.yml
services:
  web:
    depends_on:
      - db
      - redis
  db:
    image: postgres:15-alpine
  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
pip install django-redis
```

```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND':  'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS':  {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}
CACHE_TTL = 60 * 15   # 15 minutos por defecto
```

```python
# envios/viewsets.py
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from config.settings import CACHE_TTL

class RutaViewSet(viewsets.ReadOnlyModelViewSet):
    """Las rutas cambian poco — cachear el listado 15 minutos"""
    queryset         = Ruta.objects.activas()
    serializer_class = RutaSerializer

    @method_decorator(cache_page(CACHE_TTL))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EncomiendaViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas globales — se calculan cada 5 minutos"""
        cache_key = f'estadisticas_empleado_{request.user.id}'
        data = cache.get(cache_key)

        if data is None:
            data = {
                'activas':       Encomienda.objects.activas().count(),
                'en_transito':   Encomienda.objects.en_transito().count(),
                'con_retraso':   Encomienda.objects.con_retraso().count(),
                'entregadas_mes': Encomienda.objects.filter(
                    estado='EN', fecha_entrega_real__month=timezone.now().month
                ).count(),
            }
            cache.set(cache_key, data, CACHE_TTL)

        return Response(data)

    def perform_update(self, serializer):
        """Invalidar caché cuando se actualiza una encomienda"""
        super().perform_update(serializer)
        cache.delete(f'estadisticas_empleado_{self.request.user.id}')
```

---

## Entregable Final — Sesión 05: DRF Completo

Al finalizar debes poder demostrar:

**Fundamentos DRF**
1. Instalación y configuración de DRF en el proyecto de encomiendas.
2. `EncomiendaSerializer` y `EncomiendaDetailSerializer` con `@property` del modelo.
3. Endpoints FBV con `@api_view` para listar y detalle de encomiendas.
4. Endpoints CBV con `APIView` con métodos `get/post/patch/delete`.
5. Mixins combinados para List+Create y Retrieve+Update+Destroy.
6. Generic Views: `ListCreateAPIView` y `RetrieveUpdateDestroyAPIView`.

**DRF Avanzado**
7. `EncomiendaViewSet` con `ModelViewSet` y `@action` para `cambiar_estado`.
8. Acciones de lista: `con_retraso`, `pendientes`, `estadisticas`.
9. Router registrado y URLs generadas automáticamente.
10. `EncomiendaDetailSerializer` con objetos anidados y historial.
11. Paginación: `PageNumberPagination` con `page_size=15`.
12. Filtros: estado, búsqueda de texto, ordenamiento y `con_retraso`.
13. JWT: obtención, uso en cabecera, renovación y payload personalizado.
14. Permisos: `EsEmpleadoActivo` y `EsPropietarioOAdmin` funcionando.
15. Validaciones: `validate_peso_kg`, `validate_codigo` y `validate()` cruzado.
16. Swagger en `http://localhost:8000/api/docs/` con `@extend_schema`.
17. Versionado: `/api/v1/` y `/api/v2/` con serializer distinto.

**Temas adicionales**
18. Tests: al menos 6 tests cubriendo list, create, error 400 y cambiar_estado.
19. Throttling: `EmpleadoRateThrottle` en el ViewSet y `LoginRateThrottle` en auth.
20. Exception handler devuelve el mismo formato JSON en todos los errores.
21. CORS configurado con `CORS_ALLOWED_ORIGINS`.
22. `to_representation()` personaliza la salida ocultando campos según el usuario.
23. Bulk: `POST /api/v1/encomiendas/bulk_create/` y `PATCH /bulk_estado/` funcionan.
24. `select_related` y `prefetch_related` en `con_relaciones()`: máximo 2 queries por lista.
25. Redis en `docker-compose.yml`: endpoint `/estadisticas/` cacheado 15 minutos.

---

> **Repositorio en GitHub con todos los archivos, tests pasando y README actualizado.**
