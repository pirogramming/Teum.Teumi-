from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from apps.profiles.views import mypage

app_name = 'users'

urlpatterns = [
    path('mypage/', mypage, name='mypage'),
    path('login/', user_login, name='login'),
    path('login/kakao/', kakao_login, name='kakao-login'),
    path('login/kakao/callback/', kakao_callback, name='kakao-callback'),
    path('login/google/', google_login, name='google-login'),
    path('login/google/callback/', google_callback, name='google-callback'),
    path('login/google/finish/', GoogleLoginFinishView.as_view(), name='google-login-todjango'),
    path("logout/", user_logout, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # JWT 토큰 갱신 
    
    # 마이페이지 편집 API 엔드포인트들
    # API 명세서: API_SPECIFICATION.md 참조
    path('update-basic/', update_basic, name='update-basic'),      # 1. 기본 정보 업데이트 API
    path('update-interests/', update_interests, name='update-interests'),  # 2. 관심사 업데이트 API
    path('update-schedule/', update_schedule, name='update-schedule'),     # 3. 스케줄 업데이트 API
    path('update-advanced/', update_advanced, name='update-advanced'),     # 4. 상세 정보 업데이트 API
]