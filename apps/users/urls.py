from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    path('login/', login, name='login'),
    path('login/kakao/', kakao_login, name='kakao-login'),
    path('login/kakao/callback/', kakao_callback, name='kakao-callback'),
    path('login/google/', google_login, name='google-login'),
    path('login/google/callback/', google_callback, name='google-callback'),
    path('login/google/finish/', GoogleLogin.as_view(), name='google-login-todjango'),
]