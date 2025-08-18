from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.views import APIView
from django.db.models import Q, Avg
from .models import Matching, MatchingStatus
from .serializers import MatchCreateSerializer, MatchDetailSerializer
from apps.matches.services.recommend import recommend_top_n
from apps.matches.services.ai_recommend import recommend_top_n_with_ai
from apps.matches.services.explain_reason import explain_recommendation_reasons
from apps.profiles.ProfileSerializer import ProfileSimpleSerializer
from django.shortcuts import get_object_or_404, render
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
from apps.reviews.models import Review
from datetime import datetime
from django.utils import timezone

def wants_html(request):
    """클라이언트가 HTML을 원하는지 확인하는 헬퍼 함수"""
    return request.headers.get('Accept', '').find('text/html') != -1

# 1. 매칭 신청(POST)
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
        receiver = serializer.validated_data['receiver']

        if receiver == sender:
            raise serializers.ValidationError({"receiver": ["본인에게는 신청할 수 없습니다."]})

        exists_conflict = Matching.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).exists()
        if exists_conflict:
            raise serializers.ValidationError({"non_field_errors": ["이미 진행 중인 신청이 있습니다."]})

        serializer.save(sender=sender, receiver=receiver, status=MatchingStatus.PENDING)

class MatchStatusUpdateView(generics.UpdateAPIView):
    """
    매칭 상태 변경 API (PATCH)
    - 수신자만 상태를 변경할 수 있음
    - '수락됨'으로 변경 시 1:1 채팅방을 생성(또는 기존 방 재사용)
    - 성공 시 {room_id, room_url} 포함하여 반환
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MatchDetailSerializer
    queryset = Matching.objects.all()

    def patch(self, request, *args, **kwargs):
        matching = self.get_object()
        
        # 수신자만 상태 변경 가능
        if matching.receiver != request.user:
            raise PermissionDenied("수신자만 매칭 상태를 변경할 수 있습니다.")

        new_status = request.data.get('status')
        if not new_status:
            return Response({"error": "상태 정보가 필요합니다."}, status=400)

        # 상태 변경
        matching.status = new_status
        
        # 수락된 경우 채팅방 생성
        if new_status == MatchingStatus.ACCEPTED:
            matching.matched_at = timezone.now()
            
            # 기존 채팅방이 있는지 확인
            if not matching.chatroom:
                # 새 채팅방 생성
                chatroom = ChatRoom.objects.create()
                matching.chatroom = chatroom
                
                # 참여자 추가
                ChatParticipation.objects.create(
                    user=matching.sender,
                    chatroom=chatroom
                )
                ChatParticipation.objects.create(
                    user=matching.receiver,
                    chatroom=chatroom
                )

        matching.save()

        # 응답 데이터 구성
        response_data = self.get_serializer(matching).data
        
        if matching.chatroom:
            response_data.update({
                "room_id": matching.chatroom.id,
                "room_url": f"/chats/{matching.chatroom.id}/"
            })

        return Response(response_data, status=200)


# AI 추천 API
class AIRecommendationView(APIView):
    """
    AI 기반 매칭 추천 API
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """AI 추천 결과와 이유 반환"""
        try:
            user = request.user
            n = int(request.query_params.get('n', 3))
            
            # AI 추천 실행
            recommended_profiles = recommend_top_n_with_ai(user, n)
            
            if not recommended_profiles:
                return Response({
                    "message": "추천할 수 있는 프로필이 없습니다.",
                    "recommendations": []
                }, status=200)
            
            # 추천 이유 설명 생성
            explanations = explain_recommendation_reasons(user, recommended_profiles, n)
            
            # 응답 데이터 구성
            recommendations = []
            for i, profile in enumerate(recommended_profiles):
                reason = "추천 이유를 생성할 수 없습니다."
                if explanations.get("success") and explanations.get("explanations"):
                    for exp in explanations["explanations"]:
                        if exp.get("profile_id") == profile.profile_id:
                            reason = exp.get("reason", "추천 이유를 생성할 수 없습니다.")
                            break
                
                recommendations.append({
                    "profile_id": profile.profile_id,
                    "nickname": profile.nickname or "익명",
                    "age": profile.age,
                    "gender": profile.get_gender_display() if profile.gender else "없음",
                    "school": profile.school.school_name if profile.school else "없음",
                    "department": profile.department.department_name if profile.department else "없음",
                    "introduction": profile.introduction or "없음",
                    "recommendation_reason": reason
                })
            
            return Response({
                "message": f"AI 추천 {len(recommendations)}명을 성공적으로 생성했습니다.",
                "recommendations": recommendations,
                "total_count": len(recommendations)
            }, status=200)
            
        except Exception as e:
            print(f"AI 추천 API 오류: {e}")
            return Response({
                "error": "AI 추천 생성 중 오류가 발생했습니다.",
                "detail": str(e)
            }, status=500)


# 룰 기반 추천 API
class RuleBasedRecommendationView(APIView):
    """
    룰 기반 매칭 추천 API
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """룰 기반 추천 결과 반환"""
        try:
            user = request.user
            n = int(request.query_params.get('n', 3))
            
            # 룰 기반 추천 실행
            recommended_profiles = recommend_top_n(user, n)
            
            if not recommended_profiles:
                return Response({
                    "message": "추천할 수 있는 프로필이 없습니다.",
                    "recommendations": []
                }, status=200)
            
            # 응답 데이터 구성
            recommendations = []
            for profile in recommended_profiles:
                recommendations.append({
                    "profile_id": profile.profile_id,
                    "nickname": profile.nickname or "익명",
                    "age": profile.age,
                    "gender": profile.get_gender_display() if profile.gender else "없음",
                    "school": profile.school.school_name if profile.school else "없음",
                    "department": profile.department.department_name if profile.department else "없음",
                    "introduction": profile.introduction or "없음"
                })
            
            return Response({
                "message": f"룰 기반 추천 {len(recommendations)}명을 성공적으로 생성했습니다.",
                "recommendations": recommendations,
                "total_count": len(recommendations)
            }, status=200)
            
        except Exception as e:
            print(f"룰 기반 추천 API 오류: {e}")
            return Response({
                "error": "룰 기반 추천 생성 중 오류가 발생했습니다.",
                "detail": str(e)
            }, status=500)


# 4. 매칭 리스트 페이지 (HTML 또는 JSON)
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

    user_reviews = Review.objects.filter(user=user, match__in=base_qs)
    review_map = {review.match_id: review.rating for review in user_reviews} # 매칭아이디를 키로 리뷰 평점이 값
    print(review_map)

    context = {
        'matchings': base_qs,
        'MatchingStatus': MatchingStatus,
        'chatrooms': chat_qs,
        'user': user,
        'review_map': review_map,
    }
    return render(request, 'matches/matches.html', context)
    

KOR_TO_EN_DAY = {
    "월": "Monday", "화": "Tuesday", "수": "Wednesday",
    "목": "Thursday", "금": "Friday", "토": "Saturday", "일": "Sunday",
}

WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
WEEKEND = ["Saturday", "Sunday"]

def _normalize_days(day_values):
    result = []
    for v in day_values:
        v = v.strip()
        if v.lower() in ("weekday", "평일"):
            result.extend(WEEKDAY)
        elif v.lower() in ("weekend", "주말"):
            result.extend(WEEKEND)
        elif v in KOR_TO_EN_DAY:
            result.append(KOR_TO_EN_DAY[v])
        else:
            # 이미 "Monday" 같은 영어라면 그대로
            result.append(v)
    # 중복 제거
    return list(dict.fromkeys(result))

def _parse_time_range(s):
    # "오전 (09:00~12:00)" 또는 "09:00~12:00"
    if "(" in s and ")" in s:
        s = s[s.find("(")+1 : s.find(")")]
    if "~" not in s:
        return None
    start_str, end_str = s.split("~", 1)
    try:
        start_t = datetime.strptime(start_str.strip(), "%H:%M").time()
        end_t = datetime.strptime(end_str.strip(), "%H:%M").time()
        return start_t, end_t
    except ValueError:
        return None


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
    ).annotate(
        avg_rating=Avg('user__received_reviews__rating')  # ★ 평균 평점 추가
    )

    # --- GET 파라미터로 필터링 ---
    # 관심사
    selected_interests = request.GET.getlist('interests')
    if selected_interests:
        profiles = profiles.filter(interests__interest_id__in=selected_interests)

    # 시간대
    selected_times = request.GET.getlist('times')   # ["09:00~12:00", ...]
    selected_days_raw = request.GET.getlist('days') # ["weekday"] / ["Monday"] / ["월"] / ["주말"] ...

    if selected_times or selected_days_raw:
        time_filters = Q()

        # 요일 정규화 후 적용
        if selected_days_raw:
            selected_days = _normalize_days(selected_days_raw)
            time_filters &= Q(user__free_times__day_of_week__in=selected_days)

        # 시간 교집합(겹치면 OK)
        if selected_times:
            time_q = Q()
            for t in selected_times:
                parsed = _parse_time_range(t)
                if not parsed:
                    continue
                bucket_start, bucket_end = parsed
                time_q |= Q(
                    user__free_times__start_time__lt=bucket_end,
                    user__free_times__end_time__gt=bucket_start
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