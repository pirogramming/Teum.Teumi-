from django.urls import path
from . import views
from .views import (
    SchoolProfileAPIView,
    FreeTimeAPIView,
    InterestTagAPIView,
    BasicInfoAPIView,
    AddtionalInfoAPIView,
    profile_home,
    profile_detail,
    profile_step1,
    profile_step2,
    profile_step3,
    profile_step4,
    profile_step5,
)
<<<<<<< HEAD
=======
app_name = 'profiles'
>>>>>>> 14e4f1ebf7a39731be06b076a544d1b3ee1cb184

urlpatterns = [
  
    #홈화면,프로필정보 상세페이지
    path('profile/', profile_home, name='profile-home'),
    path('profile/<int:profile_id>/', profile_detail, name='profile-detail'),

    # API 엔드포인트
    path('api/school/', SchoolProfileAPIView.as_view(), name='school'),
    path('api/free_time/', FreeTimeAPIView.as_view(), name='free-time'),
    path('api/interests/', InterestTagAPIView.as_view(), name='interests'),
    path('api/basic_info/', BasicInfoAPIView.as_view(), name='basic-info'),
    path('api/additional-info/', AddtionalInfoAPIView.as_view(), name='additional-info'),
    
    # 프로필 단계별 페이지
    path('step1/', profile_step1, name='profile_step1'),
    path('step2/', profile_step2, name='profile_step2'),
    path('step3/', profile_step3, name='profile_step3'),
    path('step4/', profile_step4, name='profile_step4'),
    path('step5/', profile_step5, name='profile_step5'),
    
    # 기타 API
    path('api/majors/', views.get_majors_by_school, name='get_majors_by_school'),
]

