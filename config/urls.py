"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('',          include('envios.urls')),               # incluye login/logout propios
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)

# Personalizar el titulo del Admin
admin.site.site_header = 'Sistema de Gestion de Encomiendas'
admin.site.site_title  = 'Encomiendas Admin'
admin.site.index_title = 'Panel de Administracion'
