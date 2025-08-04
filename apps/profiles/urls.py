from django.urls import path
from .views import (
    SchoolProfileAPIView,
    FreeTimeAPIView,
    InterestTagAPIView,
    BasicInfoAPIView,
    AddtionalInfoAPIView,
    profile_home,
    profile_detail,
)

urlpatterns = [
    path('profile/', profile_home, name='profile-home'),
    path('profile/<int:profile_id>/', profile_detail, name='profile-detail'),
    path('school', SchoolProfileAPIView.as_view(), name='school-profile'),
    path('free_time', FreeTimeAPIView.as_view(), name='free-time'),
    path('interests', InterestTagAPIView.as_view(), name='interest-tag'),
    path('basic_info', BasicInfoAPIView.as_view(), name='nickname-mbti'),
    path('additional_info', AddtionalInfoAPIView.as_view(), name='additional-info'),
]