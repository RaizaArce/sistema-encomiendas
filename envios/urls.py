from django.urls import path
from . import views
from . import views_auth

urlpatterns = [
    # Sistema
    path('',                              views.dashboard,                  name='dashboard'),
    path('encomiendas/',                  views.encomienda_lista,           name='encomienda_lista'),
    path('encomiendas/nueva/',            views.encomienda_crear,           name='encomienda_crear'),
    path('encomiendas/<int:pk>/',         views.encomienda_detalle,         name='encomienda_detalle'),
    path('encomiendas/<int:pk>/estado/',  views.encomienda_cambiar_estado,  name='encomienda_cambiar_estado'),
    path('encomiendas/<int:pk>/json/',    views.encomienda_estado_json,     name='encomienda_estado_json'),

    # Autenticacion
    path('login/',                        views_auth.login_view,            name='login'),
    path('logout/',                       views_auth.logout_view,           name='logout'),
    path('perfil/',                       views_auth.perfil_view,           name='perfil'),
]
