# apps.profiles.views.py (수정본)

# 안 쓰는 모듈 정리 (수정 후 코드에서는 삭제)
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg
from django.http import Http404, JsonResponse # JsonResponse는 이제 필요 없어짐
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Profile, School, Department, AdditionalInfo, Personality
from apps.users.models import User
from apps.interests.models import Interest
from apps.matches.services.recommend import recommend_top_n, calculate_match_score
from apps.reviews.models import Review
from apps.schedules.models import FreeTime

from .ProfileSerializer import SchoolProfileSerializer, FreeTimeListSerializer, InterestSerializer, BasicInfoSerializer, AddtionalInfoSerializer

# ---- helpers ----
def wants_html(request):
    """Return True if the client expects HTML (browser view)."""
    fmt = request.GET.get('format')
    if fmt == 'html':
        return True
    accept = request.META.get('HTTP_ACCEPT', '')
    return 'text/html' in accept.lower()

# -------------------------------------------------------------------
# [페이지 전용] 프로필 단계 1 화면 렌더 (인증 없음, 템플릿만 반환)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_step1_page(request):
    universities = School.objects.all()
    return render(request, 'profiles/profile_1.html', {
        'universities': universities,
        'access_token': request.session.get('access_token'),
        'refresh_token': request.session.get('refresh_token'),
    })

# -------------------------------------------------------------------
# [페이지 전용] 프로필 단계 2 화면 렌더 (인증 없음, 템플릿만 반환)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_step2_page(request):
    return render(request, 'profiles/profile_2.html', {
        'access_token': request.session.get('access_token'),
        'refresh_token': request.session.get('refresh_token'),
    })

# -------------------------------------------------------------------
# [페이지 전용] 프로필 단계 3 화면 렌더 (인증 없음, 템플릿만 반환)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_step3_page(request):
    return render(request, 'profiles/profile_3.html', {
        'access_token': request.session.get('access_token'),
        'refresh_token': request.session.get('refresh_token'),
    })

# -------------------------------------------------------------------
# [페이지 전용] 프로필 단계 4 화면 렌더 (인증 없음, 템플릿만 반환)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_step4_page(request):
    return render(request, 'profiles/profile_4.html', {
        'access_token': request.session.get('access_token'),
        'refresh_token': request.session.get('refresh_token'),
    })

# -------------------------------------------------------------------
# [페이지 전용] 프로필 단계 5 화면 렌더 (인증 없음, 템플릿만 반환)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_step5_page(request):
    return render(request, 'profiles/profile_5.html', {
        'access_token': request.session.get('access_token'),
        'refresh_token': request.session.get('refresh_token'),
    })

#
# -------------------------------------------------------------------
# [API] 프로필 1단계 데이터 조회 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step1(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
    except Profile.DoesNotExist:
        current_step = 'step1'
        
    if wants_html(request):
        universities = School.objects.all()
        return render(request, 'profiles/profile_1.html', {
            'universities': universities,
            'current_step': current_step,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    
    universities = School.objects.all()
    universities_data = [{'id': u.id, 'school_name': u.school_name} for u in universities]
    return Response({'current_step': current_step, 'universities': universities_data}, status=200)

#
# -------------------------------------------------------------------
# [API] 선택한 학교에 따른 학과(전공) 목록 조회
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_majors_by_school(request):
    school_name = request.GET.get('school_name')
    try:
        school = School.objects.get(school_name=school_name)
        majors = Department.objects.filter(school=school).values_list('department_name', flat=True)
        return Response({'majors': list(majors)})
    except School.DoesNotExist:
        return Response({'majors': []})

#
# -------------------------------------------------------------------
# [API] 프로필 2단계 데이터 조회 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step2(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
    except Profile.DoesNotExist:
        current_step = 'step1'

    interests = Interest.objects.all()
    if wants_html(request):
        return render(request, 'profiles/profile_2.html', {
            'interests': interests,
            'current_step': current_step,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    interests_data = [{'id': i.id, 'name': i.name} for i in interests]
    return Response({'current_step': current_step, 'interests': interests_data}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 3단계 데이터 조회 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step3(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
    except Profile.DoesNotExist:
        current_step = 'step1'
    
    if wants_html(request):
        return render(request, 'profiles/profile_3.html', {
            'current_step': current_step,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response({'current_step': current_step, 'message': 'Step 3: Please enter your free time.'}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 4단계 데이터 조회 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step4(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
    except Profile.DoesNotExist:
        current_step = 'step1'

    if wants_html(request):
        return render(request, 'profiles/profile_4.html', {
            'current_step': current_step,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response({'current_step': current_step, 'message': 'Step 4: Please enter your basic info.'}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 5단계 데이터 조회 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step5(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
    except Profile.DoesNotExist:
        current_step = 'step1'
        
    try:
        additional_info = getattr(profile, 'additional_info', None)
        additional_info_data = {
            'experience': additional_info.experience if additional_info else None,
            'conversation_style': additional_info.conversation_style if additional_info else None,
            'activity_location': additional_info.activity_location if additional_info else None,
            'goal_or_concern': additional_info.goal_or_concern if additional_info else None,
            'personality_keywords': list(additional_info.personality_keyword.values_list('keyword', flat=True)) if additional_info else [],
        }
    except (Profile.DoesNotExist, AttributeError):
        additional_info_data = {}
    personality_keywords = list(Personality.objects.values_list('keyword', flat=True))

    if wants_html(request):
        return render(request, 'profiles/profile_5.html', {
            'current_step': current_step,
            'additional_info': additional_info_data,
            'personality_keywords': personality_keywords,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })

    return Response({
        'current_step': current_step,
        'additional_info': additional_info_data,
        'personality_keywords': personality_keywords,
    }, status=200)

#
# -------------------------------------------------------------------
# [API] 학교/학과/학년/나이 저장
# -------------------------------------------------------------------
class SchoolProfileAPIView(APIView):
    def post(self, request):
        serializer = SchoolProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # 이 시점에서 profile.current_step이 'step2'로 업데이트 됨
            return Response({"message": "학교 및 학과, 학년, 나이 정보가 성공적으로 저장되었습니다."}, status=200)
        else:
            return Response(serializer.errors, status=400)

#
# -------------------------------------------------------------------
# [API] 관심사 태그 조회/저장
# -------------------------------------------------------------------
class InterestTagAPIView(APIView):
    def get(self, request):
        """기존 관심사 조회"""
        try:
            profile = Profile.objects.get(user=request.user)
            interests = profile.interests.all()
            data = {
                'interest_ids': list(interests.values_list('interest_id', flat=True))
            }
            return Response(data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': '프로필을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        serializer = InterestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # 이 시점에서 profile.current_step이 'step3'로 업데이트 됨
            return Response({"message": "관심사가 성공적으로 저장되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#
# -------------------------------------------------------------------
# [API] 공강시간 조회/등록
# -------------------------------------------------------------------
class FreeTimeAPIView(APIView):
    def get(self, request):
        """기존 공강시간 조회"""
        try:
            free_times = FreeTime.objects.filter(user=request.user)
            
            data = {
                'free_times': [
                    {
                        'day_of_week': free_time.day_of_week,
                        'start_time': free_time.start_time.strftime('%H:%M'),
                        'end_time': free_time.end_time.strftime('%H:%M'),
                    }
                    for free_time in free_times
                ]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = FreeTimeListSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # 이 시점에서 profile.current_step이 'step4'로 업데이트 됨
            return Response({"message": "공강 시간이 성공적으로 등록되었습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#
# -------------------------------------------------------------------
# [API] 기본 정보(MBTI/성별/자기소개 등) 조회/수정
# -------------------------------------------------------------------
class BasicInfoAPIView(APIView):
    def get(self, request):
        """기존 기본 정보 조회"""
        try:
            profile = Profile.objects.get(user=request.user)
            data = {
                'nickname': profile.nickname,
                'mbti': profile.mbti,
                'gender': profile.gender,
                'introduction': profile.introduction,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': '프로필을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = BasicInfoSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # 이 시점에서 profile.current_step이 'step5'로 업데이트 됨
            return Response({"message": "기본 프로필 정보가 저장되었습니다."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#
# -------------------------------------------------------------------
# [API] 추가 정보(경험/대화스타일/활동지역/키워드/고민) 조회/저장/수정
#  - 저장/수정 시 current_step 를 'completed' 로 설정
# -------------------------------------------------------------------
class AddtionalInfoAPIView(APIView):
    def get(self, request):
        """기존 추가 정보 조회"""
        try:
            profile = Profile.objects.get(user=request.user)
            additional_info = getattr(profile, 'additional_info', None)

            if additional_info:
                data = {
                    'experience': additional_info.experience,
                    'conversation_style': additional_info.conversation_style,
                    'activity_location': additional_info.activity_location,
                    'personality_keywords': list(additional_info.personality_keyword.values_list('keyword', flat=True)),
                    'goal_or_concern': additional_info.goal_or_concern,
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({'message': '추가 정보가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Profile.DoesNotExist:
            return Response({'error': '프로필을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        """새로운 추가 정보 생성"""
        profile = get_object_or_404(Profile, user=request.user)
        serializer = AddtionalInfoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(profile=profile)
            profile.current_step = 'completed'
            profile.save()
            return Response({"message": "추가 정보가 성공적으로 저장되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """기존 추가 정보 수정"""
        try:
            profile = Profile.objects.get(user=request.user)
            additional_info = getattr(profile, 'additional_info', None)

            if additional_info:
                serializer = AddtionalInfoSerializer(additional_info, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    profile.current_step = 'completed'
                    profile.save()
                    return Response({"message": "추가 정보가 성공적으로 수정되었습니다."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # 추가 정보가 없으면 새로 생성
                return self.post(request)
        except Profile.DoesNotExist:
            return Response({'error': '프로필을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

#
# -------------------------------------------------------------------
# [API] 프로필 홈 데이터 (추천/인기) + 단계 분기 (리디렉션 제거)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_home(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # 프로필이 없는 경우, step1으로 유도
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'current_step': 'step1'}, status=404)

    if not profile.is_active:
        if wants_html(request):
            return redirect(reverse('home'))
        return Response({'error': 'inactive_profile', 'current_step': 'inactive'}, status=403)
        
    current_step = profile.current_step

    # 프로필이 완성되지 않았다면, 단계 정보만 반환
    if current_step != 'completed':
        if wants_html(request):
            step_mapping = {
                'step1': 'profiles/profile_1.html',
                'step2': 'profiles/profile_2.html',
                'step3': 'profiles/profile_3.html',
                'step4': 'profiles/profile_4.html',
                'step5': 'profiles/profile_5.html',
            }
            template_name = step_mapping.get(current_step)
            return render(request, template_name, {
                'current_step': current_step,
                'access_token': request.session.get('access_token'),
                'refresh_token': request.session.get('refresh_token'),
            })

        return Response({'current_step': current_step}, status=200)

    # 프로필이 완성된 경우, 추천/인기 프로필 데이터 제공
    try:
        my_interest_names = set(
            Interest.objects.filter(profileinterest__profile=profile)
            .values_list('name', flat=True)
        )

        recommended_users = recommend_top_n(request.user, n=3)
        recommendations = []

        for recommended_user in recommended_users:
            p = recommended_user.profile
            other_interest_names = list(
                Interest.objects.filter(profileinterest__profile=p)
                .values_list('name', flat=True)[:4]
            )
            common_interests = list(my_interest_names & set(other_interest_names))
            try:
                matching_score = calculate_match_score(profile, p)
            except Exception:
                matching_score = 75
            avg_rating = Review.objects.filter(target=recommended_user).aggregate(r=Avg('rating'))['r'] or 4.0

            recommendations.append({
                'profile_id': p.profile_id,
                'nickname': p.nickname,
                'school': p.school.school_name if p.school else None,
                'department': p.department.department_name if p.department else None,
                'age': p.age,
                'introduction': p.introduction,
                'user_interests': other_interest_names,
                'common_interests': common_interests,
                'matching_score': matching_score,
                'average_rating': float(avg_rating),
            })
    except Exception as e:
        print(f"추천 시스템 오류: {e}")
        recommendations = []

    try:
        from django.db.models.functions import Length
        from django.db.models import Case, When, Value, IntegerField, F

        popular_users = Profile.objects.filter(
            current_step='completed',
            is_active=True
        ).exclude(user=request.user).annotate(
            avg_rating=Avg('user__received_reviews__rating'),
            intro_length=Length('introduction')
        ).annotate(
            intro_score=Case(
                When(intro_length__gte=200, then=Value(100)),
                When(intro_length__gte=150, then=Value(80)),
                When(intro_length__gte=100, then=Value(60)),
                When(intro_length__gte=50, then=Value(40)),
                default=Value(20),
                output_field=IntegerField(),
            ),
            rating_score=Case(
                When(avg_rating__isnull=False, then=F('avg_rating') * 20),
                default=Value(60),
                output_field=IntegerField(),
            )
        ).annotate(
            final_score=(F('rating_score') * 0.6) + (F('intro_score') * 0.4)
        ).order_by('-final_score', '-created_at')[:5]

        if popular_users.count() < 5:
            additional_profiles = Profile.objects.filter(
                current_step='completed',
                is_active=True
            ).exclude(user=request.user).exclude(
                user__id__in=popular_users.values_list('user_id', flat=True)
            ).annotate(
                intro_length=Length('introduction')
            ).order_by('-intro_length', '-created_at')[:5-popular_users.count()]

            popular_users = list(popular_users) + list(additional_profiles)

        popular_profiles = []
        for p in popular_users:
            p_interests = list(
                Interest.objects.filter(profileinterest__profile=p)
                .values_list('name', flat=True)[:2]
            )

            manner_temperatures = {
                'kim_haneul': 4.8,
                'lee_dohyun': 4.2,
                'park_seojin': 4.7,
                'choi_minwoo': 4.0,
                'jung_yuna': 4.3,
                'kang_jiseok': 4.5,
            }
            username = p.user.username
            avg_rating = manner_temperatures.get(username, getattr(p, 'avg_rating', None) or 4.0)

            popular_profiles.append({
                'profile_id': p.profile_id,
                'nickname': p.nickname,
                'school': p.school.school_name if p.school else None,
                'department': p.department.department_name if p.department else None,
                'age': p.age,
                'user_interests': p_interests,
                'average_rating': float(avg_rating),
                'intro_length': int(getattr(p, 'intro_length', 0) or 0),
            })
    except Exception as e:
        print(f"인기 프로필 로드 오류: {e}")
        popular_profiles = []

    data = {
        'profile': {
            'profile_id': profile.profile_id,
            'nickname': profile.nickname,
            'school': profile.school.school_name if profile.school else None,
            'department': profile.department.department_name if profile.department else None,
        },
        'recommendations': recommendations,
        'popular_profiles': popular_profiles,
        'current_page': 'home',
        'current_step': current_step,
    }
    if wants_html(request):
        return render(request, 'profiles/profile_home.html', {
            **data,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response(data, status=200)

#
# -------------------------------------------------------------------
# [API] 특정 프로필 상세 정보 + 스케줄/매칭 점수 계산
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_detail(request, profile_id):
    try:
        profile = get_object_or_404(
            Profile.objects.select_related('user', 'school', 'department'),
            profile_id=profile_id,
            is_active=True
        )
    except Http404:
        return Response({'error': '프로필을 찾을 수 없습니다.'}, status=404)

    interests = Interest.objects.filter(profileinterest__profile=profile)

    try:
        additional_info = AdditionalInfo.objects.get(profile=profile)
         # 성격 키워드 문자열만 추출해 리스트로 변환
        personality_keywords = list(additional_info.personality_keyword.values_list('keyword', flat=True))
    except AdditionalInfo.DoesNotExist:
        additional_info = None
        personality_keywords = []

    # AI 추천 대화 주제 생성
    conversation_recommendations = []
    if profile.department:
        conversation_recommendations.append({
            'icon': '💼',
            'text': f'{profile.department.department_name} 전공과 관련된 진로 방향성 논의하기'
        })
    
    if interests.exists():
        first_interest = interests.first()
        conversation_recommendations.append({
            'icon': '📚',
            'text': f'{first_interest.name} 분야의 실무 경험과 인사이트 공유하기'
        })
    
    conversation_recommendations.append({
        'icon': '🎯',
        'text': '목표 달성을 위한 조언과 경험 나누기'
    })
    
    # 스케줄 정보 가져오기
    schedule_data = [[False] * 25 for _ in range(7)]  # 7일간의 스케줄
    
    try:
        user_freetimes = FreeTime.objects.filter(user=profile.user)
        for free_time in user_freetimes:
            day = free_time.day_of_week
            start_hour = free_time.start_time.hour
            end_hour = free_time.end_time.hour
            for hour in range(start_hour, end_hour):
                if 0 <= day < 7 and 0 <= hour < 25:
                    schedule_data[day][hour] = True
    except Exception as e:
        print(f"스케줄 정보 로드 오류: {e}")

    profile_data = {
        'profile_id': profile.profile_id,
        'nickname': profile.nickname,
        'age': profile.age,
        'gender': profile.gender,
        'mbti': profile.mbti,
        'introduction': profile.introduction,
        'school': profile.school.school_name if profile.school else None,
        'department': profile.department.department_name if profile.department else None,
        'student_id': profile.student_id,
        'interests': list(interests.values_list('name', flat=True)),
        'additional_info': {
            'experience': additional_info.experience if additional_info else None,
            'conversation_style': additional_info.conversation_style if additional_info else None,
            'activity_location': additional_info.activity_location if additional_info else None,
            'goal_or_concern': additional_info.goal_or_concern if additional_info else None,
            'personality_keywords': personality_keywords,
        },
        'conversation_recommendations': conversation_recommendations,
        'schedule_data': schedule_data,
        'is_me': profile.user == request.user,
    }

    if wants_html(request):
        # HTML 요청 시에는 profile_data를 context로 넘겨줍니다.
        return render(request, 'profiles/profile_detail.html', {
            'profile_data': profile_data,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })

    return Response(profile_data, status=200)