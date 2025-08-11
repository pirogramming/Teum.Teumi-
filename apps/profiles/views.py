#apps.profiles.views.py
# 안쓰는 모듈 
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Profile, School, Department, AdditionalInfo, ProfileInterest
from apps.users.models import User
from apps.interests.models import Interest
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse
from django.urls import reverse

from .models import School, Department, Profile, Personality

from apps.matches.services.recommend import recommend_top_n


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
#  - 세션의 access/refresh 토큰을 템플릿 변수로 주입
#  - 실제 데이터는 프론트 JS가 /profiles/step1/ API로 호출
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
# [API] 프로필 1단계 데이터 조회/분기
#  - HTML 요청: 템플릿 렌더 (wants_html 참일 때)
#  - JSON 요청: 단계/다음 경로(next_step) 응답
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step1(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')
        if current_step != 'step1':
            step_mapping = {
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3',
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'profiles:profile-home'  # 완료되면 홈으로
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({
                'current_step': current_step,
                'next_step': reverse(next_name) if next_name else None
            }, status=200)
    except Profile.DoesNotExist:
        if wants_html(request):
            universities = School.objects.all()
            return render(request, 'profiles/profile_1.html', {
                'universities': universities,
                'current_step': 'step1',
                'access_token': request.session.get('access_token'),
                'refresh_token': request.session.get('refresh_token'),
            })
        return Response({'current_step': 'step1', 'note': 'profile not found; proceed with step1'}, status=200)

    universities = School.objects.all()
    if wants_html(request):
        return render(request, 'profiles/profile_1.html', {
            'universities': universities,
            'current_step': 'step1',
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    universities_data = [{'id': u.id, 'school_name': u.school_name} for u in universities]
    return Response({'current_step': 'step1', 'universities': universities_data}, status=200)

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
# [API] 프로필 2단계 데이터 조회/분기
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step2(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        if current_step == 'step1':
            if wants_html(request):
                return redirect(reverse('profiles:profile_step1'))
            return Response({'current_step': current_step, 'next_step': reverse('profiles:profile_step1')}, status=200)
        if current_step not in ['step1', 'step2']:
            step_mapping = {
                'step3': 'profiles:profile_step3',
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'profiles:profile-home'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
    except Profile.DoesNotExist:
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'next_step': reverse('profiles:profile_step1')}, status=404)

    interests = Interest.objects.all()
    if wants_html(request):
        return render(request, 'profiles/profile_2.html', {
            'interests': interests,
            'current_step': 'step2',
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    interests_data = [{'id': i.id, 'name': i.name} for i in interests]
    return Response({'current_step': 'step2', 'interests': interests_data}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 3단계 데이터 조회/분기
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step3(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        if current_step in ['step1', 'step2']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
        if current_step not in ['step1', 'step2', 'step3']:
            step_mapping = {
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'profiles:profile-home'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
    except Profile.DoesNotExist:
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'next_step': reverse('profiles:profile_step1')}, status=404)

    if wants_html(request):
        return render(request, 'profiles/profile_3.html', {
            'current_step': 'step3',
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response({'current_step': 'step3', 'message': 'Step 3: Please enter your free time.'}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 4단계 데이터 조회/분기
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step4(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        if current_step in ['step1', 'step2', 'step3']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
        if current_step not in ['step1', 'step2', 'step3', 'step4']:
            step_mapping = {
                'step5': 'profiles:profile_step5',
                'completed': 'profiles:profile-home'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
    except Profile.DoesNotExist:
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'next_step': reverse('profiles:profile_step1')}, status=404)

    if wants_html(request):
        return render(request, 'profiles/profile_4.html', {
            'current_step': 'step4',
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response({'current_step': 'step4', 'message': 'Step 4: Please enter your basic info.'}, status=200)

#
# -------------------------------------------------------------------
# [API] 프로필 5단계 데이터 조회/분기
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step5(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        if current_step in ['step1', 'step2', 'step3', 'step4']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3',
                'step4': 'profiles:profile_step4'
            }
            next_name = step_mapping.get(current_step)
            if wants_html(request) and next_name:
                return redirect(reverse(next_name))
            return Response({'current_step': current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
        if current_step == 'completed':
            if wants_html(request):
                return redirect(reverse('profiles:profile-home'))
            return Response({'current_step': current_step, 'next_step': reverse('profiles:profile-home')}, status=200)
    except Profile.DoesNotExist:
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'next_step': reverse('profiles:profile_step1')}, status=404)

    try:
        profile = Profile.objects.get(user=request.user)
        additional_info = getattr(profile, 'additional_info', None)
        additional_info_data = {
            'experience': additional_info.experience if additional_info else None,
            'conversation_style': additional_info.conversation_style if additional_info else None,
            'activity_location': additional_info.activity_location if additional_info else None,
            'goal_or_concern': additional_info.goal_or_concern if additional_info else None,
            'personality_keywords': list(additional_info.personality_keyword.values_list('keyword', flat=True)) if additional_info else [],
        }
    except Profile.DoesNotExist:
        additional_info_data = {}
    personality_keywords = list(Personality.objects.values_list('keyword', flat=True))

    if wants_html(request):
        return render(request, 'profiles/profile_5.html', {
            'current_step': 'step5',
            'additional_info': additional_info_data,
            'personality_keywords': personality_keywords,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })

    return Response({
        'current_step': 'step5',
        'additional_info': additional_info_data,
        'personality_keywords': personality_keywords,
    }, status=200)

# 프로필 5단계 후 홈화면 보여주는 뷰

# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from .ProfileSerializer import SchoolProfileSerializer, FreeTimeListSerializer, InterestSerializer, BasicInfoSerializer, AddtionalInfoSerializer

#
# -------------------------------------------------------------------
# [API] 학교/학과/학년/나이 저장
# -------------------------------------------------------------------
class SchoolProfileAPIView(APIView):
    def post(self, request):
        serializer = SchoolProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()   
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
            from apps.schedules.models import FreeTime
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
# [API] 프로필 홈 데이터 (추천/인기) + 단계 분기
#  - current_step != 'completed' 이면 next_step 안내 또는 HTML 리다이렉트
#  - completed 이면 추천/인기 프로필 데이터 제공
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_home(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
      
        if wants_html(request):
            return redirect(reverse('profiles:profile_step1'))
        return Response({'error': 'profile_not_found', 'next_step': reverse('profiles:profile_step1')}, status=404)

    if not profile.is_active:
        if wants_html(request):
            return redirect(reverse('home'))
        return Response({'error': 'inactive_profile', 'next_step': reverse('home')}, status=403)

    if profile.current_step != 'completed':
        step_mapping = {
            'step1': 'profiles:profile_step1',
            'step2': 'profiles:profile_step2', 
            'step3': 'profiles:profile_step3',
            'step4': 'profiles:profile_step4',
            'step5': 'profiles:profile_step5'
        }
        
        # 4단계 이상 완성 - 홈 페이지 렌더링
        # AI 추천 프로필 가져오기
        
        next_name = step_mapping.get(profile.current_step)
        if wants_html(request) and next_name:
            return redirect(reverse(next_name))
        return Response({'current_step': profile.current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)
        # 이하 추천/인기 프로필 데이터는 그대로 유지

    try:
        from apps.matches.services.recommend import recommend_top_n, calculate_match_score
        from apps.reviews.models import Review
        from django.db.models import Avg

        # 내 관심사(교집합 계산용)
        my_interest_names = set(
            Interest.objects.filter(profileinterest__profile=profile)
            .values_list('name', flat=True)
        )

        # 추천 3명
        recommended_users = recommend_top_n(request.user, n=3)
        recommendations = []

        for recommended_user in recommended_users:
            p = recommended_user.profile

            # 상대 관심사: 최대 4개 (feat 로직)
            other_interest_names = list(
                Interest.objects.filter(profileinterest__profile=p)
                .values_list('name', flat=True)[:4]
            )

            # 공통 관심사
            common_interests = list(my_interest_names & set(other_interest_names))

            # 매칭 점수 (실패 시 기본값)
            try:
                matching_score = calculate_match_score(profile, p)
            except Exception:
                matching_score = 75

            # 매너온도(리뷰 평균) - 없으면 4.0
            avg_rating = Review.objects.filter(target=recommended_user).aggregate(r=Avg('rating'))['r'] or 4.0

            # 모델 인스턴스 직접 append 금지 → dict로 직렬화
            recommendations.append({
                'profile_id': p.profile_id,
                'nickname': p.nickname,
                'school': p.school.school_name if p.school else None,
                'department': p.department.department_name if p.department else None,
                'age': p.age,
                'introduction': p.introduction,
                'user_interests': other_interest_names,     # 최대 4개
                'common_interests': common_interests,       # 교집합
                'matching_score': matching_score,
                'average_rating': float(avg_rating),
            })

    except Exception as e:
        print(f"추천 시스템 오류: {e}")
        recommendations = []
    
    try:
        from django.db.models import Avg, Case, When, Value, IntegerField, F
        from django.db.models.functions import Length
        from apps.reviews.models import Review
        
        # 자기소개 길이와 리뷰 평점을 모두 고려한 가중치 계산
        popular_users = Profile.objects.filter(
            current_step='completed',
            is_active=True
        ).exclude(user=request.user).annotate(

            avg_rating=Avg('user__received_reviews__rating'),
            intro_length=Length('introduction')
        ).annotate(
            # 자기소개 길이 가중치 (0-100점)
            intro_score=Case(
                When(intro_length__gte=200, then=Value(100)),  # 200자 이상: 100점
                When(intro_length__gte=150, then=Value(80)),   # 150자 이상: 80점
                When(intro_length__gte=100, then=Value(60)),   # 100자 이상: 60점
                When(intro_length__gte=50, then=Value(40)),    # 50자 이상: 40점
                default=Value(20),  # 50자 미만: 20점
                output_field=IntegerField(),
            ),
            # 리뷰 평점 (0-100점으로 변환)
            rating_score=Case(
                When(avg_rating__isnull=False, then=F('avg_rating') * 20),  # 5점 만점을 100점으로 변환
                default=Value(60),  # 리뷰 없으면 기본 60점
                output_field=IntegerField(),
            )
        ).annotate(
            # 최종 점수: 리뷰 평점 60% + 자기소개 40%
            final_score=(F('rating_score') * 0.6) + (F('intro_score') * 0.4)
        ).order_by('-final_score', '-created_at')[:5]
        
        # 만약 프로필이 부족하면, 자기소개 길이 기준으로 보완
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
#  - HTML 요청: 템플릿 렌더, JSON 요청: 상세 데이터 반환
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
        from apps.schedules.models import FreeTime
        user_freetimes = FreeTime.objects.filter(user=profile.user)
        
        for freetime in user_freetimes:

            # DayOfWeek enum의 인덱스 계산 (Monday=0, Tuesday=1, ...)
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            day_index = day_mapping.get(freetime.day_of_week, 0)
            
            # 시간을 30분 단위로 분할 (9:00-21:00)

            start_hour = freetime.start_time.hour
            start_minute = freetime.start_time.minute
            end_hour = freetime.end_time.hour
            end_minute = freetime.end_time.minute
            # 30분 단위 인덱스 계산
            start_index = (start_hour - 9) * 2 + (1 if start_minute >= 30 else 0)
            end_index = (end_hour - 9) * 2 + (1 if end_minute >= 30 else 0)
            
            # 해당 시간 슬롯들을 True로 설정
            for i in range(max(0, start_index), min(25, end_index)):
                schedule_data[day_index][i] = True
    except Exception as e:
        print(f"스케줄 로드 오류: {e}")
    
    # 디버깅: 스케줄 데이터 확인
    print(f"스케줄 데이터: {schedule_data}")
    print(f"사용자 FreeTime 개수: {user_freetimes.count() if 'user_freetimes' in locals() else 0}")
    
    # 매칭 점수 및 공통 관심사 계산
    matching_score = 0
    common_interests_count = 0
    
    try:
        from apps.matches.services.recommend import calculate_match_score
        
        # 현재 로그인한 사용자의 프로필
        my_profile = Profile.objects.get(user=request.user)
        
        # calculate_match_score 함수로 매칭 점수 계산
        matching_score = calculate_match_score(my_profile, profile)
        
        # 공통 관심사 계산
        my_interests = Interest.objects.filter(profileinterest__profile=my_profile)
        my_interest_names = set(my_interests.values_list('name', flat=True))
        other_interest_names = set(interests.values_list('name', flat=True))
        common_interests_count = len(my_interest_names & other_interest_names)
        
    except Exception as e:
        print(f"매칭 계산 오류: {e}")
        matching_score = 70  # 기본값
        common_interests_count = 0
    
    import json
    
    context = {
        'profile': profile,
        'interests': interests,
        'additional_info': additional_info,
        'personality_keywords': personality_keywords,
        'conversation_recommendations': conversation_recommendations,
        'schedule': json.dumps(schedule_data),  # JSON 문자열로 변환  스케줄 데이터 업로드

        'matching_score': matching_score,
        'common_interests_count': common_interests_count,
    }
    if wants_html(request):
        return render(request, 'profiles/profile_detail.html', {
            **context,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })
    return Response(context, status=200)
    
# -------------------------------------------------------------------
# [API] 마이페이지 데이터 반환 (관심사/성격 키워드 등)
# -------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage(request):
    """마이페이지를 반환하는 API 뷰"""
    if not request.user.is_authenticated:
        return redirect('/users/login/')

    profile = Profile.objects.select_related('user', 'school', 'department').get(user=request.user)

    # 사용자 관심사
    user_interests = ProfileInterest.objects.filter(profile=profile).select_related('interest')
    selected_interests = [{'id': ui.interest.id, 'name': ui.interest.name} for ui in user_interests]

    # 모든 관심사
    available_interests = [{'id': i.id, 'name': i.name} for i in Interest.objects.all()]

    # 추가 정보 및 성격 키워드
    try:
        additional_info = AdditionalInfo.objects.get(profile=profile)
        personality_keywords = additional_info.personality_keyword.all()
        selected_personalities = [{'id': p.id, 'keyword': p.keyword} for p in personality_keywords]
    except AdditionalInfo.DoesNotExist:
        additional_info = None
        personality_keywords = []
        selected_personalities = []

    # 모든 성격 키워드
    available_personalities = [{'id': p.id, 'keyword': p.keyword} for p in Personality.objects.all()]

    # 사용자 스케줄 (템플릿에서 기존 스케줄 표시 용)
    try:
        from apps.schedules.models import FreeTime
        user_schedule = FreeTime.objects.filter(user=request.user).order_by('day_of_week', 'start_time')
    except Exception:
        user_schedule = []

    data = {
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        },
        'selected_interests': selected_interests,
        'available_interests': available_interests,
        'selected_personalities': selected_personalities,
        'available_personalities': available_personalities,
        'user_schedule': user_schedule,
        'mbti_options': [choice[0] for choice in Profile.MBTI_CHOICES],
    }

    # 🔁 HTML 요청이면 템플릿 렌더, JSON 요청이면 그대로 반환
    if wants_html(request):
        return render(request, 'users/mypage.html', {
            **data,
            'access_token': request.session.get('access_token'),
            'refresh_token': request.session.get('refresh_token'),
        })

    return Response(data)
