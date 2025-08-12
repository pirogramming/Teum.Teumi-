from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth import login as django_login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from allauth.socialaccount.models import SocialAccount
from dotenv import load_dotenv
import requests
import os

from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated



load_dotenv()

GOOGLE_CALLBACK_URI = settings.GOOGLE_CALLBACK_URI

class SocialLoginException(Exception):
    pass

class KakaoException(Exception):
    pass

def user_login(request):
    """
    로그인 페이지 진입점
    - 카카오/구글 콜백에서 `/users/login/?access=...&refresh=...`로 리다이렉트되면
      반드시 이 템플릿을 렌더해서 프론트 JS가 토큰을 localStorage에 저장할 수 있도록 함.
    - 세션 기반 분기에서는 Profile의 `is_completed` 대신 `current_step == 'completed'`로 판단.
    """
    # 0) 세션에 저장된 토큰이 있으면 템플릿 변수로 주입하여 렌더
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')
    if access_token and refresh_token:
        form = AuthenticationForm()
        return render(request, 'users/login.html', {'form': form, 'access_token': access_token, 'refresh_token': refresh_token})

    # 2) 이미 로그인된 경우: 프로필 진행 단계에 따라 분기
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            try:
                if getattr(request.user.profile, 'current_step', None) == 'completed':
                    return redirect('profiles:profile-home')
                else:
                    return redirect('profiles:profile_step1')
            except Exception:
                # profile 접근 중 예외가 나도 안전하게 step1로 보냄
                return redirect('profiles:profile_step1')
        else:
            return redirect('profiles:profile_step1')

    # 3) 일반 폼 로그인 처리 (선택적으로 유지)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profiles:profile-home') # 프로필 완성 상태에 따라 적절한 페이지로 리다이렉트
    else:
        form = AuthenticationForm()

    # 기본: 로그인 템플릿 렌더
    return render(request, 'users/login.html', {'form': form})

def kakao_login(request):
    try:
        if request.user.is_authenticated:
            return redirect('profiles:profile-home')

        client_id = os.environ.get("KAKAO_ID")
        # 운영 도메인 고정 (요청 도메인과 무관하게 teumteumi.site 사용)
        redirect_uri = "https://teumteumi.site/users/login/kakao/callback/"

        if client_id is None:
            raise KakaoException("KAKAO_ID is not set properly in .env")

        return redirect(
            f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
        )

    except (KakaoException, SocialLoginException) as error:
        print(f"[kakao_login error] {error}")
        messages.error(request, str(error))
        return JsonResponse({'error': '로그인 실패'}, status=400, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def kakao_callback(request):
    try:
        # 이미 로그인된 사용자는 JWT 발급 후 토큰과 함께 렌더
        if request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            access_token_jwt = str(refresh.access_token)
            refresh_token_jwt = str(refresh)
            request.session['access_token'] = access_token_jwt
            request.session['refresh_token'] = refresh_token_jwt
            return render(request, 'users/login.html', {
                'access_token': access_token_jwt,
                'refresh_token': refresh_token_jwt
            })

        code = request.GET.get("code")
        if not code:        # 카카오에서 제공한 인가 코드가 없다면 실패 처리
            raise KakaoException("Authorization code not provided")

        client_id = os.environ.get("KAKAO_ID")      # .env 파일에서 가져오기
        client_secret = os.environ.get("KAKAO_SECRET")
        # 운영 도메인 고정 콜백 URL
        redirect_uri = "https://teumteumi.site/users/login/kakao/callback/"

        token_response = requests.post(     # 카카오에게 엑세스 토큰 요청
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
        if "error" in token_json:       # 정상적으로 토큰을 받지 못했다면 예외 처리
            raise KakaoException("Failed to get access token")

        access_token = token_json.get("access_token")       # 엑세스 토큰을 이용해 사용자 정보를 가져옴
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_request = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers)
        profile_json = profile_request.json()

        kakao_account = profile_json.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        nickname = profile.get("nickname")
        email = kakao_account.get("email")

        if not email:       # 메일이 없으면 예외 처리
            raise KakaoException("Kakao did not return email")

        user = User.objects.filter(email=email).first()
        if user:        # 같은 이메일로 가입한 유저가 있다면, 카카오로 가입한 것인지 확인
            if user.login_method != User.LOGIN_KAKAO:
                raise KakaoException(f"Please login with: {user.login_method}")
        else:
            user = User.objects.create_user(        # 유저 생성
                email=email,
                username=email,
                first_name=nickname or "",
                login_method=User.LOGIN_KAKAO,
            )

            user.set_unusable_password()        # 일반 로그인 방지
            user.save()

        login(request, user)

        refresh = RefreshToken.for_user(user)
        access_token_jwt = str(refresh.access_token)
        refresh_token_jwt = str(refresh)
        request.session['access_token'] = access_token_jwt
        request.session['refresh_token'] = refresh_token_jwt
        return render(request, 'users/login.html', {
            'access_token': access_token_jwt,
            'refresh_token': refresh_token_jwt
        })

        '''return JsonResponse({                      #Json 응답
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_email': user.email
        })'''
        # 프로필 완성 상태에 따라 적절한 페이지로 리다이렉트로 임시 수정
        return redirect('profiles:profile-home') 

    except (KakaoException, SocialLoginException) as error:
        return JsonResponse({'error': str(error)}, status=400)


def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    redirect_uri = "https://teumteumi.site/users/login/google/callback/"
    return redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    )

def google_callback(request):
    # 이미 로그인된 사용자는 JWT 발급 후 토큰과 함께 렌더
    if request.user.is_authenticated:
        refresh = RefreshToken.for_user(request.user)
        access_token_jwt = str(refresh.access_token)
        refresh_token_jwt = str(refresh)
        request.session['access_token'] = access_token_jwt
        request.session['refresh_token'] = refresh_token_jwt
        return render(request, 'users/login.html', {
            'access_token': access_token_jwt,
            'refresh_token': refresh_token_jwt
        })
        
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("SOCIAL_AUTH_GOOGLE_SECRET")
    code = request.GET.get('code')

    token_req = requests.post(      # 엑세스 토큰 받아옴
        "https://oauth2.googleapis.com/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "https://teumteumi.site/users/login/google/callback/",
            "code": code
        }
    )

    token_json = token_req.json()
    if "error" in token_json:       # 실패 시 오류 메시지 리턴
        return JsonResponse({"err_msg": f"Google token error: {token_json['error_description']}"}, status=400)

    access_token = token_json.get("access_token")

    email_req = requests.get(       # 사용자 정보 요청
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={'access_token': access_token}
    )

    if email_req.status_code != 200:
        return JsonResponse({'err_msg': 'Failed to fetch user info'}, status=400)

    email_info = email_req.json()       # 사용자 정보 받아옴
    email = email_info.get('email')
    name = email_info.get('name', '')
    picture = email_info.get('picture', '')

    if not email:
        return JsonResponse({'err_msg': 'Email not found in response'}, status=400)

    user = None     # 유저 객체 미리 선언

    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)

        if social_user.provider != 'google':        # 구글 이메일이 아닌 경우 오류
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

    # 로그인 처리 및 세션 설정
    django_login(request, user)
    request.session.set_expiry(0)  # 브라우저 세션 유지
    
    # JWT 토큰 생성
    refresh = RefreshToken.for_user(user)
    access_token_jwt = str(refresh.access_token)
    refresh_token_jwt = str(refresh)
    request.session['access_token'] = access_token_jwt
    request.session['refresh_token'] = refresh_token_jwt
    return render(request, 'users/login.html', {
        'access_token': access_token_jwt,
        'refresh_token': refresh_token_jwt
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
    
###여기서 부터 프로필과 중복 확인해볼 필요 있음###
##중복 제거 
def user_logout(request):
    """
    로그아웃 API
    
    엔드포인트: GET /users/logout/
    설명: 사용자를 로그아웃 처리하고 로그인 페이지로 리다이렉트합니다.
    
    응답: 로그인 페이지로 리다이렉트 (/users/login/)
    """
    # 1) 세션/서버 측 상태 정리
    refresh_in_session = request.session.pop('refresh_token', None)
    request.session.pop('access_token', None)

    # Django 인증 세션 로그아웃
    logout(request)

    # 2) 클라이언트 측 로컬 상태도 제거해야 완전 로그아웃 (localStorage/쿠키)
    #    템플릿 없이도 동작하도록 스크립트를 직접 반환 후 /users/login/ 으로 이동
    from django.http import HttpResponse
    script = """
    <script>
      try {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        sessionStorage.clear();
      } catch (e) {}
      // 쿠키 제거는 서버가 지시
      window.location.replace('/users/login/');
    </script>
    """

    response = HttpResponse(script)
    # 3) 관련 쿠키 제거 지시 (있을 경우)
    for name in ['access', 'refresh', 'access_token', 'refresh_token', 'csrftoken', 'sessionid']:
        response.delete_cookie(name)

    return response



