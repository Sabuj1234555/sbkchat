from django.urls import re_path
from . import consumes
websocket_urlpatterns = [
    re_path(r"ws/chat/$",consumes.ChatConsumer.as_asgi())
]