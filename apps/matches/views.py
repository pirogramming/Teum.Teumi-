from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.views import APIView
from django.db.models import Q
from .models import Matching, MatchingStatus
from .serializers import MatchCreateSerializer, MatchDetailSerializer
from apps.matches.services.recommend import recommend_top_n
from apps.profiles.ProfileSerializer import ProfileSimpleSerializer
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from apps.profiles.models import School, Profile
from apps.interests.models import Interest
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.matches.models import Matching, MatchingStatus
from apps.matches.serializers import MatchDetailSerializer
from apps.chats.models import ChatRoom, ChatParticipation
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.profiles.models import Profile, Interest, School

def wants_html(request):
    """클라이언트가 HTML을 원하는지 확인하는 헬퍼 함수"""
    return request.headers.get('Accept', '').find('text/html') != -1

# 1. 매칭 목록 조회(GET) & 매칭 신청(POST)
class MatchListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = Matching.objects.filter(
            Q(sender=u) | Q(receiver=u)
        ).select_related(
            'sender__profile__department',
            'receiver__profile__department'
        ).order_by('-created_at')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MatchCreateSerializer
        return MatchDetailSerializer

    def perform_create(self, serializer):
        sender = self.request.user

        # 1) 기본: serializer에서 receiver를 받되,
        # 2) 누락되었거나 잘못 매핑될 수 있으므로 to_profile_id 로 보강
        receiver = serializer.validated_data.get('receiver', None)

        if receiver is None:
            # 프론트가 전달하는 대상 프로필 id 보조 키
            raw_profile_id = self.request.data.get('to_profile_id') or self.request.data.get('profile_id')
            if raw_profile_id is not None:
                try:
                    profile_id = int(raw_profile_id)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({"receiver": ["대상 프로필 ID가 올바르지 않습니다."]})
                try:
                    target_profile = Profile.objects.select_related('user').get(pk=profile_id)
                except Profile.DoesNotExist:
                    raise serializers.ValidationError({"receiver": ["대상 프로필을 찾을 수 없습니다."]})
                receiver = target_profile.user

        if receiver is None:
            raise serializers.ValidationError({"receiver": ["수신자 정보가 누락되었습니다."]})

        # 자기 자신에게 신청 방지
        if receiver == sender:
            raise serializers.ValidationError({"receiver": ["본인에게는 신청할 수 없습니다."]})

        # 양방향 중복 매칭 방지: 거절된 건만 예외, 그 외 상태는 모두 차단
        exists_conflict = Matching.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).exclude(status=MatchingStatus.REJECTED).exists()
        if exists_conflict:
            raise serializers.ValidationError({"non_field_errors": ["이미 진행 중인 신청이 있습니다."]})

        # 정상 저장
        serializer.save(sender=sender, receiver=receiver, status=MatchingStatus.PENDING)


class MatchStatusUpdateView(generics.UpdateAPIView):
    """
    매칭 상태 변경 API (PATCH)
    - 수신자만 상태를 변경할 수 있음
    - '수락됨'으로 변경 시 1:1 채팅방을 생성(또는 기존 방 재사용)
    - 성공 시 {room_id, room_url} 포함하여 반환
    """
    permission_classes = [IsAuthenticated]
    queryset = Matching.objects.all()
    serializer_class = MatchDetailSerializer  # 응답 스키마 재사용

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        match = self.get_object()

        # 권한 체크: 수신자만 수락/거절 가능
        if match.receiver != request.user:
            raise PermissionDenied("수락 또는 거절은 수신자만 할 수 있습니다.")

        # 부분 업데이트 수행
        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(match, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 변경된 상태 확인 (한글 값: '대기중' / '수락됨' / '거절됨')
        new_status = serializer.validated_data.get('status', serializer.instance.status)

        room = None
        if new_status == MatchingStatus.ACCEPTED:  # '수락됨'
            sender = match.sender
            receiver = match.receiver

            # 두 사용자 모두 참여한 기존 방 조회 (through: ChatParticipation, related_name='participations')
            room = (
                ChatRoom.objects
                .filter(participations__user=sender)
                .filter(participations__user=receiver)
                .distinct()
                .first()
            )

            # 없으면 새 방 생성 + 두 참가자 등록 (idempotent)
            if room is None:
                room = ChatRoom.objects.create()
                ChatParticipation.objects.get_or_create(chatroom=room, user=sender)
                ChatParticipation.objects.get_or_create(chatroom=room, user=receiver)
                
            # ✅ 추가된 로직: Matching 객체에 ChatRoom 연결
            match.chatroom = room
            match.save()  # 변경사항을 DB에 저장

        # 기본 응답 + room info
        data = self.get_serializer(serializer.instance).data
        if room is not None:
            data.update({
                "room_id": room.id,
                "room_url": f"/chats/rooms/{room.id}/",
            })
        return Response(data, status=status.HTTP_200_OK)


# 3. 상태별 필터링된 내 매칭 조회 (GET)
class MyMatchListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatchDetailSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Matching.objects.filter(
            Q(sender=u) | Q(receiver=u)
        ).select_related(
            'sender__profile__department',
            'receiver__profile__department'
        ).order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# 4. AI 추천 매칭 대상 반환 (GET)
class MatchRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_users = recommend_top_n(request.user)
        data = ProfileSimpleSerializer([user.profile for user in top_users], many=True, context={'request': request}).data
        return Response(data)


@api_view(['GET']) # 이 데코레이터를 추가하여 API 뷰로 만듭니다.
@permission_classes([IsAuthenticated])
def matching_list(request):
    user = request.user

    base_qs = Matching.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related(
        'sender__profile__department',
        'receiver__profile__department'
    ).order_by('-created_at')

    chat_qs = ChatRoom.objects.filter(
        participations__user=user
    ).distinct().select_related(
        'iscompleted__chatroom',
    ).order_by('-completed_at')

    # 클라이언트가 HTML 페이지를 요청한 경우
    if wants_html(request):
        context = {
            'matchings': base_qs,
            'MatchingStatus': MatchingStatus,
            'chatrooms': chat_qs,
            'user': user,
        }
        return render(request, 'matches/matches.html', context)
    
    # 클라이언트가 JSON 데이터를 요청한 경우 (비동기 요청)
    else:
        status_filter = request.GET.get('status')
        if status_filter:
            qs = base_qs.filter(status=status_filter)
        else:
            qs = base_qs

        # Serializer를 사용하여 데이터를 JSON으로 변환
        serializer = MatchDetailSerializer(qs, many=True)
        return Response(serializer.data, status=200)


# 탐색 페이지
def matching_browse(request):
    interests = Interest.objects.all()
    universities = School.objects.prefetch_related('departments').all()

    # 실제 프로필 데이터 가져오기 (완료된 프로필만)
    profiles = Profile.objects.filter(
        current_step='completed',
        is_active=True
    ).exclude(
        user=request.user  # 본인 제외
    ).select_related(
        'user',
        'school',
        'department'
    ).prefetch_related(
        'interests__interest'
    )

    # --- GET 파라미터로 필터링 ---
    # 관심사
    selected_interests = request.GET.getlist('interests')
    if selected_interests:
        profiles = profiles.filter(interests__interest_id__in=selected_interests)

    # 시간대
    selected_times = request.GET.getlist('times')  # 예: ["09:00~12:00"]
    selected_days = request.GET.getlist('days')    # 예: ["Monday", "Tuesday"]

    if selected_times or selected_days:
        time_filters = Q()
        if selected_days:
            time_filters &= Q(user__free_times__day_of_week__in=selected_days)
        if selected_times:
            time_q = Q()
            for t in selected_times:
                # 괄호 제거
                if "(" in t and ")" in t:
                    t = t[t.find("(")+1 : t.find(")")]
                
                if "~" not in t:
                    continue

                start_str, end_str = t.split("~")
                time_q |= Q(
                    user__free_times__start_time__lt=end_str.strip(),
                    user__free_times__end_time__gt=start_str.strip()
                )
            time_filters &= time_q
        profiles = profiles.filter(time_filters)

    # 대학교
    school_id = request.GET.get('school_name')
    if school_id:
        profiles = profiles.filter(school_id=school_id)

    # 학과
    department_id = request.GET.get('department_name')
    if department_id:
        profiles = profiles.filter(department_id=department_id)

    # distinct 먼저, 그 다음 슬라이스
    profiles = profiles.distinct()[:10]

    # 직렬화하여 학과 포함한 JSON 생성
    universities_data = []
    for uni in universities:
        universities_data.append({
            'school_id': uni.school_id,
            'school_name': uni.school_name,
            'departments': [
                {'department_id': dept.department_id, 'department_name': dept.department_name}
                for dept in uni.departments.all()
            ]
        })

    context = {
        'interests': interests,
        'universities': universities,
        'universities_json': universities_data,  # 템플릿에서 JSON으로 사용
        'profiles': profiles,  # 실제 프로필 데이터
    }
    return render(request, 'matches/browse.html', context)