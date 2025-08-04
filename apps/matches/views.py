from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Matching
from .serializers import MatchCreateSerializer, MatchDetailSerializer
from apps.matches.services.recommend import recommend_top_n
from apps.profiles.ProfileSerializer import ProfileSimpleSerializer

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
