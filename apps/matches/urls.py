from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path("", views.MatchListCreateView.as_view(), name="match-list-create"),  # GET, POST
    path("<int:pk>/", views.MatchStatusUpdateView.as_view(), name="match-status-update"),  # PATCH
    path("mine", views.MyMatchListView.as_view(), name="my-match-list"),  # GET with status query param
    path("recommendations", views.MatchRecommendationView.as_view(), name="match-recommendations"),  # GET
    path("list/", views.matching_list, name="matching-list"),     # 매칭 리스트 페이지
    path('browse/', views.matching_browse, name='interest_list_page'),   # 탐색 페이지
    path("", views.matching_list, name="matching-list"),     # 매칭 리스트 페이지
    path("api/matches/", views.MatchListCreateView.as_view(), name="match-list-create"),  # GET, POST
    path("api/matches/<int:pk>/status/", views.MatchStatusUpdateView.as_view(), name="match-status-update"),  # PATCH
    path("api/matches/mine/", views.MyMatchListView.as_view(), name="my-match-list"),  # GET with status query param
    path("api/matches/recommendations/", views.MatchRecommendationView.as_view(), name="match-recommendations"),  # GET
]