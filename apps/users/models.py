from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):

    """ Custom User model """

    LOGIN_EMAIL = "email"
    LOGIN_KAKAO = "kakao"
    LOGIN_GOOGLE = "google"

    LOGIN_CHOICES = (
        (LOGIN_EMAIL, "Email"),
        (LOGIN_KAKAO, "Kakao"),
        (LOGIN_GOOGLE, "Google"),
    )

    login_method = models.CharField(
        max_length=6, choices=LOGIN_CHOICES, default=LOGIN_EMAIL
    )

    avatar = models.ImageField(upload_to="avatars", blank=True, null=True)  # 이미지