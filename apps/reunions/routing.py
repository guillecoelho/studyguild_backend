from django.urls import re_path

from .consumers import ReunionConsumer

websocket_urlpatterns = [
    re_path(r"ws/reunions/(?P<reunion_id>\d+)/$", ReunionConsumer.as_asgi()),
]
