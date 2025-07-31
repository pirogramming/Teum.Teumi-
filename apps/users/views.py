from django.shortcuts import render, redirect, reverse
import os
import requests
from django.contrib import messages
from django.core.files.base import ContentFile
from django.contrib.auth import login
from .models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from dotenv import load_dotenv

load_dotenv()

class SocialLoginException(Exception):
    pass

class KakaoException(Exception):
    pass


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profiles:profile')  # 로그인 후 이동
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def kakao_login(request):
    try:
        if request.user.is_authenticated:
            raise SocialLoginException("User already logged in")

        client_id = os.environ.get("KAKAO_ID")
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback/"

        if client_id is None:
            raise KakaoException("KAKAO_ID is not set properly in .env")

        return redirect(
            f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
        )

    except (KakaoException, SocialLoginException) as error:
        messages.error(request, str(error))
        return redirect("/")


@csrf_exempt
def kakao_login_callback(request):
    try:
        if request.user.is_authenticated:
            raise SocialLoginException("User already logged in")

        code = request.GET.get("code")
        if not code:
            raise KakaoException("Authorization code not provided")

        client_id = os.environ.get("KAKAO_ID")
        client_secret = os.environ.get("KAKAO_SECRET")
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback/"

        if not client_id or not client_secret:
            raise KakaoException("Kakao credentials not loaded")

        token_response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code": code,
                "client_secret": client_secret,
            },
        )

        token_json = token_response.json()
        if "error" in token_json:
            print("Token Error:", token_json)
            raise KakaoException("Failed to get access token")

        access_token = token_json.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_request = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers)
        profile_json = profile_request.json()

        kakao_account = profile_json.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        nickname = profile.get("nickname")
        avatar_url = profile.get("profile_image_url")
        email = kakao_account.get("email")
        gender = kakao_account.get("gender")

        if not email:
            raise KakaoException("Kakao did not return email")

        user = User.objects.filter(email=email).first()
        if user:
            if user.login_method != User.LOGIN_KAKAO:
                raise KakaoException(f"Please login with: {user.login_method}")
        else:
            user = User.objects.create_user(
                email=email,
                username=email,
                first_name=nickname or "",
                gender=gender,
                login_method=User.LOGIN_KAKAO,
            )

            if avatar_url:
                avatar_response = requests.get(avatar_url)
                user.avatar.save(
                    f"{nickname}-avatar.jpg", ContentFile(avatar_response.content)
                )

            user.set_unusable_password()
            user.save()

        login(request, user)
        messages.success(request, f"{user.email} logged in with Kakao successfully")
        return redirect("/")

    except (KakaoException, SocialLoginException) as error:
        messages.error(request, str(error))
        return redirect("/")