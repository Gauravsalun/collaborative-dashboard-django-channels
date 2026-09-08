# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

django_asgi_app = get_asgi_application()

from myapp.consumers import DashboardConsumer
from django.urls import path

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("ws/dashboard/<str:room_id>/", DashboardConsumer.as_asgi()),
            ])
        )
    ),
})
