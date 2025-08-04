import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.profiles.models import Profile
from django.utils import timezone
from .models import ChatRoom, Chat

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL에서 room_id 추출하고 그룹 이름 설정
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"chat_{self.room_id}"

        # 채팅방 그룹에 현재 소켓 채널 추가
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # WebSocket 연결 수락
        await self.accept()

    async def disconnect(self, close_code):
        # 채팅방 그룹에서 현재 소켓 채널 제거
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # 클라이언트로부터 메시지 수신
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']

        # 채팅방 존재 확인
        try:
            room = await ChatRoom.objects.aget(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return

        # 메시지 DB 저장
        chat = await Chat.objects.acreate(
            chatroom=room,
            sender=user,
            content=message,
            created_at=timezone.now()
        )

        # 사용자 프로필에서 닉네임 조회 (없으면 "익명")
        profile = await Profile.objects.filter(user=user, is_active=True).afirst()
        nickname = profile.nickname if profile and profile.nickname else "익명"

        # 채팅방 그룹에 메시지 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': nickname,
                "created_at": str(chat.created_at),
            }
        )

    async def chat_message(self, event): # 그룹에서 받은 메시지를 클라이언트에 전송
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            "created_at": event["created_at"]
        }))
