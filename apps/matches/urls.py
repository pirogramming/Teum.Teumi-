from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('browse/', views.matching_browse, name='interest_list_page'),   # 탐색 페이지
    path("", views.matching_list, name="matching-list"),     # 매칭 리스트 페이지

    path("api/matches/", views.MatchListCreateView.as_view(), name="match-list-create"),  # 매칭신청
    path("api/matches/<int:pk>/status/", views.MatchStatusUpdateView.as_view(), name="match-status-update"),  # 매칭 상태 업데이트
    
    # 추천 API
    path("api/recommendations/ai/", views.AIRecommendationView.as_view(), name="ai-recommendations"),  # AI 추천
    path("api/recommendations/rule/", views.RuleBasedRecommendationView.as_view(), name="rule-recommendations"),  # 룰 기반 추천
]