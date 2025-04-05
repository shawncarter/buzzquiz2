from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Updated regex to be more flexible with game codes
    re_path(r'ws/game/(?P<game_code>[A-Za-z0-9]+)/$', consumers.GameConsumer.as_asgi()),
]