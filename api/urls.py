from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from envios.viewsets import EncomiendaViewSet
from envios import api_views

router = DefaultRouter()
router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    # Autenticacion JWT
    path('auth/token/',         TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),   name='token_refresh'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Clientes y Rutas (vistas genericas)
    path('clientes/', api_views.ClienteListView.as_view(),    name='cliente-list'),
    path('rutas/',    api_views.RutaListView.as_view(),       name='ruta-list'),

    # ViewSets
    path('', include(router.urls)),

    # Documentacion
    path('schema/', SpectacularAPIView.as_view(),   name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(), name='swagger'),
    path('redoc/',  SpectacularRedocView.as_view(),   name='redoc'),
]
