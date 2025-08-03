from django.urls import path
from . import views

urlpatterns = [
    path("matches/", views.MatchListCreateView.as_view(), name="match-list-create"),  # GET, POST
    path("matches/<int:pk>/", views.MatchStatusUpdateView.as_view(), name="match-status-update"),  # PATCH
    path("matches/mine", views.MyMatchListView.as_view(), name="my-match-list"),  # GET with status query param
    path("matches/recommendations", views.MatchRecommendationView.as_view(), name="match-recommendations"),  # GET
]