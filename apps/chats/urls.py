from django.urls import path
from .views import *

app_name = 'chats'

urlpatterns = [
    path("rooms/", create_chat_room), # POST, 채팅방 생성           
    path("rooms/list/", get_my_chat_rooms), # GET, 채팅방 목록 조회           
    path("rooms/<int:room_id>/messages/", get_chat_messages), # GET, 채팅 내역 조회  
]