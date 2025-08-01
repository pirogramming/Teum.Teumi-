from django.urls import path
from .views import *

app_name = 'chats'

urlpatterns = [
    path('auth-test/',chat_auth_test,name='chat-auth-test')
]