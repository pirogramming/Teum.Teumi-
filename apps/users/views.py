from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth import login as django_login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google import views as google_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dotenv import load_dotenv
from json import JSONDecodeError
import requests
import os
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

load_dotenv()

GOOGLE_CALLBACK_URI = settings.GOOGLE_CALLBACK_URI
BASE_URL = 'http://localhost:8000/'

class SocialLoginException(Exception):
    pass

class KakaoException(Exception):
    pass

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profiles:profile')
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
        print(f"[kakao_login error] {error}")
        messages.error(request, str(error))
        return JsonResponse({'error': '로그인 실패'}, status=400)

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
                user.avatar.save(f"{nickname}-avatar.jpg", ContentFile(avatar_response.content))

            user.set_unusable_password()
            user.save()

        login(request, user)

        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_email': user.email
        })

    except (KakaoException, SocialLoginException) as error:
        return JsonResponse({'error': str(error)}, status=400)


def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    return redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}"
    )

def google_callback(request):
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("SOCIAL_AUTH_GOOGLE_SECRET")
    code = request.GET.get('code')

    token_req = requests.post(
        "https://oauth2.googleapis.com/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": os.environ.get("GOOGLE_CALLBACK_URI"),
            "code": code
        }
    )

    token_json = token_req.json()
    if "error" in token_json:
        return JsonResponse({"err_msg": f"Google token error: {token_json['error_description']}"}, status=400)

    access_token = token_json.get("access_token")

    email_req = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={'access_token': access_token}
    )

    if email_req.status_code != 200:
        return JsonResponse({'err_msg': 'Failed to fetch user info'}, status=400)

    email_info = email_req.json()
    email = email_info.get('email')
    name = email_info.get('name', '')
    picture = email_info.get('picture', '')

    if not email:
        return JsonResponse({'err_msg': 'Email not found in response'}, status=400)

    user = None     # 유저 객체 미리 선언

    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)

        if social_user.provider != 'google':
            return JsonResponse({'err_msg': 'No matching social type'}, status=400)

    except User.DoesNotExist:
        user = User.objects.create_user(        # 유저 생성
            email=email,
            username=email,
            first_name=name,
            login_method=User.LOGIN_GOOGLE
        )
        user.set_unusable_password()
        user.save()

        SocialAccount.objects.create(user=user, provider='google', uid=email_info.get('id'))

    except SocialAccount.DoesNotExist:
        return JsonResponse({'err_msg': 'Email exists but not social user'}, status=400)

    refresh = RefreshToken.for_user(user)   # JWT 발급
    django_login(request, user)

    return JsonResponse({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_email': user.email,
    })

class GoogleLoginFinishView(APIView):
    def post(self, request):
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({'error': 'access_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        google_user_info_url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
        params = {'access_token': access_token}
        user_info_response = requests.get(google_user_info_url, params=params)

        if user_info_response.status_code != 200:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        email = user_info.get('email')

        if not email:
            return Response({'error': 'Email not found in Google response'}, status=status.HTTP_400_BAD_REQUEST)

        try:        
            user = User.objects.get(email=email)    
            social_user = SocialAccount.objects.filter(user=user).first()
            if social_user and social_user.provider != 'google':
                return Response({'error': f'Please login with {social_user.provider}'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            user = User.objects.create_user(    # 처음 로그인하는 거라면 회원가입 처리
                email=email,
                username=email,
                login_method=User.LOGIN_GOOGLE,
            )
            user.set_unusable_password()
            user.save()

            SocialAccount.objects.create(
                user=user,
                uid=email,
                provider='google'
            )

        refresh = RefreshToken.for_user(user)   # JWT 발급
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    
def user_logout(request):   # 로그아웃
    logout(request)
    return redirect("/")