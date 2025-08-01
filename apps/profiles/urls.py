from django.urls import path
from .views import SchoolProfileAPIView


urlpatterns = [
    path('school', SchoolProfileAPIView.as_view(), name='school-profile'),
]