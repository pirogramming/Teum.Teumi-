from django.urls import path
from .views import *

app_name = 'interests'

urlpatterns = [
    path("", interest_list, name = "interest-list"),
]