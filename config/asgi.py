import os
import django

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from envios.routing import websocket_urlpatterns
from channels_middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
