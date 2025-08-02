from django.urls import path
from .views import SchoolProfileAPIView
from .views import profile_input_page       # 임시이니 이따 지우자

urlpatterns = [
    path('school', SchoolProfileAPIView.as_view(), name='school-profile'),
    path('1/', profile_input_page, name='profile_input_page'),      # 임시이니 이따 지우자
]