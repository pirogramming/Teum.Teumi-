from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 정규표현식 기반의 URL 패턴:
    # room_id 값을 추출하여 해당 채팅방에 연결
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]