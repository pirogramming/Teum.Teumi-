from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path("", views.ReviewCreateView.as_view(), name="review-create"),   # POST
    path("summary/<int:user_id>/", views.ReviewSummaryView.as_view(), name="review-summary"),
]