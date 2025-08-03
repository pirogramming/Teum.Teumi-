from django.urls import path
from .views import (
    SchoolProfileAPIView,
    FreeTimeAPIView,
    InterestTagAPIView,
    BasicInfoAPIView,
    AddtionalInfoAPIView,
)
from .views import profile_input_page       # 임시이니 이따 지우자

urlpatterns = [
    path('school', SchoolProfileAPIView.as_view(), name='school-profile'),
    path('free_time', FreeTimeAPIView.as_view(), name='free-time'),
    path('interests', InterestTagAPIView.as_view(), name='interest-tag'),
    path('basic_info', BasicInfoAPIView.as_view(), name='nickname-mbti'),
    path('additional_info', AddtionalInfoAPIView.as_view(), name='additional-info'),
    path('1/', profile_input_page, name='profile_input_page'),      # 임시이니 이따 지우자
]