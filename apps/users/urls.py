from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'users'

urlpatterns = [
    # path('login/', user_login, name='login'),
    path('login/kakao/', kakao_login, name='kakao-login'),
    path('login/kakao/callback/', kakao_callback, name='kakao-callback'),
    path('login/google/', google_login, name='google-login'),
    path('login/google/callback/', google_callback, name='google-callback'),
    path('login/google/finish/', GoogleLoginFinishView.as_view(), name='google-login-todjango'),
    path("logout/", user_logout, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # JWT 토큰 갱신 
]