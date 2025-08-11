from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Matching, MatchingStatus
from .serializers import MatchCreateSerializer, MatchDetailSerializer
from apps.matches.services.recommend import recommend_top_n
from apps.profiles.ProfileSerializer import ProfileSimpleSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.profiles.models import School
from apps.interests.models import Interest

# 1. 매칭 목록 조회(GET) & 매칭 신청(POST)
class MatchListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Matching.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MatchCreateSerializer
        return MatchDetailSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

# 2. 매칭 상태 변경 (PATCH)
class MatchStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Matching.objects.all()
    serializer_class = MatchDetailSerializer  # 또는 MatchUpdateSerializer

    def perform_update(self, serializer):
        match = self.get_object()
        if match.receiver != self.request.user:
            raise PermissionDenied("수락 또는 거절은 수신자만 할 수 있습니다.")
        serializer.save()

# 3. 상태별 필터링된 내 매칭 조회 (GET)
class MyMatchListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatchDetailSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        return Matching.objects.filter(
            (Q(sender=self.request.user) | Q(receiver=self.request.user)) &
            Q(status=status_filter)
        )

# 4. AI 추천 매칭 대상 반환 (GET)
class MatchRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_users = recommend_top_n(request.user)
        data = ProfileSimpleSerializer([user.profile for user in top_users], many=True, context={'request': request}).data
        return Response(data)
    
# 매칭 리스트 페이지
@login_required
def matching_list(request):
    user = request.user

    matchings = Matching.objects.filter(
        Q(sender=user) | Q(receiver=user)       # 내가 보낸 매칭이거나 내가 받은 매칭인 경우 모두 가져오는 조건
    ).select_related(
        'sender__profile__department',
        'receiver__profile__department'
    ).order_by('-created_at')       # 최신순 정렬

    context = {
        'matchings': matchings,
        'MatchingStatus': MatchingStatus,
        'user' : user,
    }
    return render(request, 'matches/matches.html', context)

def explore_list(request):
    interests = Interest.objects.all()
    universities = School.objects.prefetch_related('departments').all()

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
        'interests' : interests,
        'universities' : universities,
        'universities_json': universities_data,  # 템플릿에서 JSON으로 사용
    }
    return render(request, 'matches/browse.html', context)