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
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback/"

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
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback/"

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
    return redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}"
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
            "redirect_uri": os.environ.get("GOOGLE_CALLBACK_URI"),
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

# 마이페이지 편집 API 뷰들
# API 명세서:  1. 기본 정보 업데이트 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_basic(request):
    """
    기본 정보 업데이트 API
    
    엔드포인트: POST /users/update-basic/
    설명: 사용자의 기본 정보(닉네임, MBTI, 성별, 자기소개)를 업데이트합니다.
    
    요청 파라미터:
    - nickname (string, 필수): 사용자 닉네임
    - mbti (string, 필수): MBTI 유형 (예: ISTJ, ENFP 등)
    - gender (string, 필수): 성별 (M: 남성, F: 여성)
    - introduction (string, 필수): 자기소개
    
    응답:
    - 성공 (200): {"success": true, "message": "기본 정보가 성공적으로 업데이트되었습니다."}
    - 실패 (400): {"success": false, "message": "모든 필수 필드를 입력해주세요."}
    - 실패 (404): {"success": false, "message": "프로필을 찾을 수 없습니다."}
    """
    try:
        from apps.profiles.models import Profile
        
        profile = Profile.objects.get(user=request.user)
        
        # 필수 필드 검증
        nickname = request.data.get('nickname')
        mbti = request.data.get('mbti')
        gender = request.data.get('gender')
        introduction = request.data.get('introduction')
        
        if not all([nickname, mbti, gender, introduction]):
            return JsonResponse({
                'success': False,
                'message': '모든 필수 필드를 입력해주세요.'
            }, status=400)
        
        # 프로필 업데이트
        profile.nickname = nickname
        profile.mbti = mbti
        profile.gender = gender
        profile.introduction = introduction
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': '기본 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '프로필을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

# API 명세서:  2. 관심사 업데이트 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_interests(request):
    """
    관심사 업데이트 API
    
    엔드포인트: POST /users/update-interests/
    설명: 사용자의 관심사를 업데이트합니다. 정확한 매칭을 위해 4개의 관심사를 선택해야 합니다.
    
    요청 파라미터:
    - interests (string, 필수): 선택된 관심사 ID 배열 (JSON 문자열)
    
    응답:
    - 성공 (200): {"success": true, "message": "관심사가 성공적으로 업데이트되었습니다."}
    - 실패 (400): {"success": false, "message": "관심사 데이터가 없습니다."}
    - 실패 (404): {"success": false, "message": "프로필을 찾을 수 없습니다."}
    """
    try:
        from apps.profiles.models import Profile, ProfileInterest
        from apps.interests.models import Interest
        import json
        
        profile = Profile.objects.get(user=request.user)
        interests_data = request.data.get('interests')
        
        if not interests_data:
            return JsonResponse({
                'success': False,
                'message': '관심사 데이터가 없습니다.'
            }, status=400)
        
        # JSON 문자열을 파싱
        try:
            interest_ids = json.loads(interests_data)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 관심사 데이터 형식입니다.'
            }, status=400)
        
        # 기존 관심사 삭제
        ProfileInterest.objects.filter(profile=profile).delete()
        
        # 새로운 관심사 추가
        for interest_id in interest_ids:
            try:
                interest = Interest.objects.get(id=interest_id)
                ProfileInterest.objects.create(profile=profile, interest=interest)
            except Interest.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': '관심사가 성공적으로 업데이트되었습니다.'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '프로필을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

# API 명세서: 3. 스케줄 업데이트 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_schedule(request):
    """
    스케줄 업데이트 API
    
    엔드포인트: POST /users/update-schedule/
    설명: 사용자의 만날 수 있는 시간을 업데이트합니다. 최소 1개 이상의 시간을 선택해야 합니다.
    
    요청 파라미터:
    - schedule (string, 필수): 스케줄 매트릭스 (JSON 문자열) - 7x25 배열
    
    스케줄 매트릭스 구조:
    - 7일 (월~일)
    - 25개 시간 슬롯 (9:00~21:30, 30분 단위)
    - true: 선택된 시간, false: 선택되지 않은 시간
    
    응답:
    - 성공 (200): {"success": true, "message": "스케줄이 성공적으로 업데이트되었습니다."}
    - 실패 (400): {"success": false, "message": "스케줄 데이터가 없습니다."}
    """
    try:
        from apps.schedules.models import FreeTime, DayOfWeek
        import json
        from datetime import time
        
        schedule_data = request.data.get('schedule')
        
        if not schedule_data:
            return JsonResponse({
                'success': False,
                'message': '스케줄 데이터가 없습니다.'
            }, status=400)
        
        # JSON 문자열을 파싱
        try:
            schedule_matrix = json.loads(schedule_data)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 스케줄 데이터 형식입니다.'
            }, status=400)
        
        # 기존 스케줄 삭제
        FreeTime.objects.filter(user=request.user).delete()
        
        # 새로운 스케줄 추가
        time_slots = []
        for i in range(25):
            hour = 9 + (i // 2)
            minute = 30 if i % 2 else 0
            time_slots.append(time(hour, minute))
        
        # DayOfWeek 매핑 (0=월 ~ 6=일)
        day_choices = [
            DayOfWeek.MONDAY,
            DayOfWeek.TUESDAY,
            DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY,
            DayOfWeek.FRIDAY,
            DayOfWeek.SATURDAY,
            DayOfWeek.SUNDAY,
        ]

        for day_index, day_schedule in enumerate(schedule_matrix):
            for time_index, is_selected in enumerate(day_schedule):
                if is_selected and time_index < len(time_slots):
                    start_time = time_slots[time_index]
                    # 30분 후 종료 시간
                    end_minute = start_time.minute + 30
                    end_hour = start_time.hour + (end_minute // 60)
                    end_minute = end_minute % 60
                    end_time = time(end_hour, end_minute)
                    
                    FreeTime.objects.create(
                        user=request.user,
                        day_of_week=day_choices[day_index],
                        start_time=start_time,
                        end_time=end_time
                    )
        
        return JsonResponse({
            'success': True,
            'message': '스케줄이 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

# API 명세서 4. 상세 정보 업데이트 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_advanced(request):
    """
    상세 정보 업데이트 API
    
    엔드포인트: POST /users/update-advanced/
    설명: 사용자의 상세 정보(경험, 대화스타일, 활동위치, 성격키워드, 목표)를 업데이트합니다.
    
    요청 파라미터:
    - experience (string, 선택): 경험과 활동
    - conversation_style (string, 선택): 대화 스타일 (casual/deep/humor/debate)
    - activity_location (string, 선택): 주요 활동 위치
    - goal_or_concern (string, 선택): 현재 목표나 고민
    - personalities (string, 선택): 선택된 성격 키워드 ID 배열 (JSON 문자열)
    
    대화 스타일 옵션:
    - casual: ☕ 수다형
    - deep: 🎯 깊은대화형
    - humor: 😄 유머형
    - debate: 💼 토론형
    
    응답:
    - 성공 (200): {"success": true, "message": "상세 정보가 성공적으로 업데이트되었습니다."}
    - 실패 (400): {"success": false, "message": "잘못된 성격 키워드 데이터 형식입니다."}
    - 실패 (404): {"success": false, "message": "프로필을 찾을 수 없습니다."}
    """
    try:
        from apps.profiles.models import Profile, AdditionalInfo, Personality
        import json
        
        profile = Profile.objects.get(user=request.user)
        
        # 추가 정보 가져오기 또는 생성
        additional_info, created = AdditionalInfo.objects.get_or_create(profile=profile)
        
        # 데이터 업데이트
        additional_info.experience = request.data.get('experience', '')
        additional_info.conversation_style = request.data.get('conversation_style', '')
        additional_info.activity_location = request.data.get('activity_location', '')
        additional_info.goal_or_concern = request.data.get('goal_or_concern', '')
        additional_info.save()
        
        # 성격 키워드 업데이트
        personalities_data = request.data.get('personalities')
        if personalities_data:
            try:
                personality_ids = json.loads(personalities_data)
                # 기존 성격 키워드 삭제
                additional_info.personality_keyword.clear()
                # 새로운 성격 키워드 추가
                for personality_id in personality_ids:
                    try:
                        personality = Personality.objects.get(id=personality_id)
                        additional_info.personality_keyword.add(personality)
                    except Personality.DoesNotExist:
                        continue
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': '잘못된 성격 키워드 데이터 형식입니다.'
                }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': '상세 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '프로필을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

def user_logout(request):
    """
    로그아웃 API
    
    엔드포인트: GET /users/logout/
    설명: 사용자를 로그아웃 처리하고 로그인 페이지로 리다이렉트합니다.
    
    응답: 로그인 페이지로 리다이렉트 (/users/login/)
    """
    request.session.pop('access_token', None)
    request.session.pop('refresh_token', None)
    logout(request)
    return redirect('/users/login/')

