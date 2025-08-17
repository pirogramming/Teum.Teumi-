# apps/profiles/urls.py
from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # --- API 엔드포인트 ---
    path('api/majors/', views.get_majors_by_school, name='get_majors_by_school'),
    path('api/school/', views.SchoolProfileAPIView.as_view(), name='school_profile'),
    path('api/interests/', views.InterestTagAPIView.as_view(), name='interests'),
    path('api/free_time/', views.FreeTimeAPIView.as_view(), name='free_time'),
    path('api/basic_info/', views.BasicInfoAPIView.as_view(), name='basic_info'),
    path('api/additional-info/', views.AddtionalInfoAPIView.as_view(), name='additional-info'),

    # --- AI 자기소개 생성 API ---
    path('api/introduction/step/', views.generate_ai_introduction_step, name='generate_ai_introduction_step'),
    path('api/introduction/enhanced/', views.generate_ai_introduction_enhanced, name='generate_ai_introduction_enhanced'),
    path('api/introduction/analyze/', views.analyze_introduction, name='analyze_introduction'),
    path('api/introduction/save-choice/', views.save_introduction_choice, name='save_introduction_choice'),

    # --- 단계별(동일 뷰) ---
    path('step1/', views.profile_step1, name='profile_step1'),
    path('step2/', views.profile_step2, name='profile_step2'),
    path('step3/', views.profile_step3, name='profile_step3'),
    path('step4/', views.profile_step4, name='profile_step4'),
    path('step5/', views.profile_step5, name='profile_step5'),

    # --- 페이지 전용 URL도 동일 뷰로 연결 (별도 *_page 함수 없음) ---
    path('step1/page/', views.profile_step1, name='profile_step1_page'),
    path('step2/page/', views.profile_step2, name='profile_step2_page'),
    path('step3/page/', views.profile_step3, name='profile_step3_page'),
    path('step4/page/', views.profile_step4, name='profile_step4_page'),
    path('step5/page/', views.profile_step5, name='profile_step5_page'),

    # --- 홈/상세 ---
    path('profile/', views.profile_home, name='profile-home'),
    path('profile/page/', views.profile_home, name='profile_home_page'),
    path('profile/<int:profile_id>/', views.profile_detail, name='profile-detail'),
    path('profile/<int:profile_id>/page/', views.profile_detail, name='profile_detail_page'),

    # --- 마이페이지 ---
    path('mypage/', views.mypage, name='mypage'),
    # 마이페이지 편집 API (users에서 이동)
    path('update-basic/', views.update_basic, name='update-basic'),
    path('update-interests/', views.update_interests, name='update-interests'),
    path('update-schedule/', views.update_schedule, name='update-schedule'),
    path('update-advanced/', views.update_advanced, name='update-advanced'),
]