from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatParticipation, Chat
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

User = get_user_model()

# 채팅방 생성 (여러 명 초대 가능, 확장성)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_chat_room(request):
    user = request.user
    participant_ids = request.data.get("participant_ids", [])

    # 본인이 빠져있으면 추가
    if user.id not in participant_ids:
        participant_ids.append(user.id)

    # 유효한 유저인지 검사
    participants = User.objects.filter(id__in=participant_ids)
    if participants.count() != len(set(participant_ids)):
        return Response({"detail": "유효하지 않은 유저 ID가 포함되어 있습니다."}, status=400)

    # 채팅방 생성
    room = ChatRoom.objects.create()

    # 참여자 등록
    ChatParticipation.objects.bulk_create([
        ChatParticipation(chatroom=room, user=participant) for participant in participants
    ])

    return Response({"room_id": room.id}, status=201)


# 내가 참여한 채팅방 목록 조회
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_chat_rooms(request):
    user = request.user
    participations = ChatParticipation.objects.filter(user=user).select_related("chatroom")

    result = []
    for participant in participations:
        chatroom = participant.chatroom
        other_users = chatroom.participations.exclude(user=user).select_related("user")

        last_message = chatroom.chats.order_by("-created_at").first()
        result.append({
            "room_id": chatroom.id,
            "participants": [u.user.username for u in other_users],
            "last_message": last_message.content if last_message else None,
            "last_time": str(last_message.created_at) if last_message else None
        })

    return Response(result)


# 채팅 내역 조회
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_messages(request, room_id):
    user = request.user

    # 참여자인지 확인
    if not ChatParticipation.objects.filter(chatroom_id=room_id, user=user).exists():
        return Response({"detail": "접근 권한이 없습니다."}, status=403)

    messages = Chat.objects.filter(chatroom_id=room_id).select_related("sender").order_by("created_at")

    data = [
        {
            "id": msg.id,
            "sender": msg.sender.username,
            "content": msg.content,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]

    return Response(data)

def chat_rooms_page(request):
    return render(request, 'chats/chat_rooms.html')

def chat_room_page(request, room_id):
    return render(request, 'chats/chat_room.html', {'room_id': room_id})