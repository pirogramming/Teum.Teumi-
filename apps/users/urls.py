from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    path('login/', login, name='login'),
    path('login/kakao/', kakao_login, name='kakao-login'),
    path('login/kakao/callback/', kakao_login_callback, name='kakao-callback'),
]