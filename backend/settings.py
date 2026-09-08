# settings.py (Channels config)

INSTALLED_APPS = [
    # ... other apps ...
    "daphne",
    "channels",
    "rest_framework",
]

# ASGI setup
ASGI_APPLICATION = "myproject.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
            # Scaling config
            "capacity": 2500,  # Max events in buffer
            "expiry": 10,       # Message expiry (seconds)
        },
    },
}

# WebSocket settings
WEBSOCKET_ACCEPT_ALL = False  # Require explicit accept()

# Cache for presence tracking
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
