"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

# .env 환경변수 로딩
import dotenv
dotenv.load_dotenv()

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Django의 앱, 모델 등을 사용할 수 있도록 초기화 (ASGI 환경에서는 수동 호출 필요)
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.users.middleware import JWTAuthMiddleware
import apps.chats.routing # 웹소켓 URL 패턴 정의


application = ProtocolTypeRouter(
    {
            "http": get_asgi_application(),
            "websocket": JWTAuthMiddleware(
                URLRouter(apps.chats.routing.websocket_urlpatterns)
            ),
    }
)
