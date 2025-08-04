# WebSocket 연결 시 JWT 토큰으로 사용자 인증을 수행하는 Channels 미들웨어

from urllib.parse import parse_qs # Query string 파싱
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser # 인증 실패 시 사용

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # 1. Query string에서 token 추출
        query_string = scope["query_string"].decode()
        token = parse_qs(query_string).get("token")

        if token:
            try: # 2. JWT 토큰 검증 및 user_id 추출
                access_token = AccessToken(token[0])
                user_id = access_token["user_id"]
                
                # 3. user_id로 DB에서 사용자 조회
                user = await User.objects.aget(id=user_id)
                scope["user"] = user

            except Exception as e: # 토큰 검증 실패 → 익명 사용자 처리
                scope["user"] = AnonymousUser()
        else: # 토큰 없음 → 익명 사용자 처리
            scope["user"] = AnonymousUser()

        #consumer로 전달
        return await super().__call__(scope, receive, send)
