from django.db import models
from apps.core.models import BaseEntity
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoom(BaseEntity):
    is_completed = models.BooleanField(default=False)  # 만남 완료 여부
    completed_at = models.DateTimeField(null=True, blank=True)  # 만남 완료 누른 시각

class ChatParticipation(BaseEntity):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name = 'participations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'chatrooms')

    class Meta:
        unique_together = ('chatroom', 'user')

class Chat(BaseEntity):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name = 'chats')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_checked = models.BooleanField(default=False)