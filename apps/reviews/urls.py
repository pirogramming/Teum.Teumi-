from django.urls import path
from . import views

urlpatterns = [
    path("", views.ReviewCreateView.as_view(), name="review-create"),   # POST
    path("", views.ReviewListView.as_view(), name="review-list"),       # GET
]