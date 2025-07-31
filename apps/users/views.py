from django.shortcuts import render, redirect, reverse
import os
import requests
from django.contrib import messages
from django.core.files.base import ContentFile
from django.contrib.auth import login
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from json import JSONDecodeError
from django.http import JsonResponse
from rest_framework import status
from allauth.socialaccount.models import SocialAccount
from dotenv import load_dotenv
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.google import views as google_view
from django.conf import settings


GOOGLE_CALLBACK_URI = settings.GOOGLE_CALLBACK_URI

state = os.environ.get("STATE")
BASE_URL = 'http://localhost:8000/'

class GoogleLogin(SocialLoginView):
    adapter_class = google_view.GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_URI
    client_class = OAuth2Client

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
def kakao_callback(request):
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
    
def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}")

def google_callback(request):
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("SOCIAL_AUTH_GOOGLE_SECRET")
    code = request.GET.get('code')

    token_req = requests.post(f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}&state={state}")
    
    token_req_json = token_req.json()
    error = token_req_json.get("error")

    if error is not None:
        raise JSONDecodeError(error)

    access_token = token_req_json.get('access_token')

    email_req = requests.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}")
    email_req_status = email_req.status_code

    if email_req_status != 200:
        return JsonResponse({'err_msg': 'failed to get email'}, status=status.HTTP_400_BAD_REQUEST)
    
    email_req_json = email_req.json()
    email = email_req_json.get('email')

    try:
        user = User.objects.get(email=email)

        social_user = SocialAccount.objects.get(user=user)

        if social_user.provider != 'google':
            return JsonResponse({'err_msg': 'no matching social type'}, status=status.HTTP_400_BAD_REQUEST)

        data = {'access_token': access_token, 'code': code}
        accept = requests.post(f"{BASE_URL}api/user/google/login/finish/", data=data)
        accept_status = accept.status_code

        if accept_status != 200:
            return JsonResponse({'err_msg': 'failed to signin'}, status=accept_status)

        accept_json = accept.json()
        accept_json.pop('user', None)
        return JsonResponse(accept_json)

    except User.DoesNotExist:
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(f"{BASE_URL}api/user/google/login/finish/", data=data)
        accept_status = accept.status_code

        if accept_status != 200:
            return JsonResponse({'err_msg': 'failed to signup'}, status=accept_status)

        accept_json = accept.json()
        accept_json.pop('user', None)
        return JsonResponse(accept_json)
    
    except SocialAccount.DoesNotExist:
        return JsonResponse({'err_msg': 'email exists but not social user'}, status=status.HTTP_400_BAD_REQUEST)

print(GOOGLE_CALLBACK_URI)