from django.urls import path
from .views import *

urlpatterns = [
    path("", interest_list, name = "interest-list")
]