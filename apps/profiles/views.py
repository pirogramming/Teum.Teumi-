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
from rest_framework.permissions import IsAuthenticated
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

# 필요한 모듈 import

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_step1(request):
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        if current_step != 'step1':
            step_mapping = {
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3',
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'profiles:profile-home',
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
            })
        return Response({'current_step': 'step1', 'note': 'profile not found; proceed with step1'}, status=200)

    universities = School.objects.all()
    if wants_html(request):
        return render(request, 'profiles/profile_1.html', {
            'universities': universities,
            'current_step': 'step1',
        })
    universities_data = [{'id': u.id, 'school_name': u.school_name} for u in universities]
    return Response({'current_step': 'step1', 'universities': universities_data}, status=200)

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
        })
    interests_data = [{'id': i.id, 'name': i.name} for i in interests]
    return Response({'current_step': 'step2', 'interests': interests_data}, status=200)

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
        return render(request, 'profiles/profile_3.html', {'current_step': 'step3'})
    return Response({'current_step': 'step3', 'message': 'Step 3: Please enter your free time.'}, status=200)

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
        return render(request, 'profiles/profile_4.html', {'current_step': 'step4'})
    return Response({'current_step': 'step4', 'message': 'Step 4: Please enter your basic info.'}, status=200)

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
        })

    return Response({
        'current_step': 'step5',
        'additional_info': additional_info_data,
        'personality_keywords': personality_keywords,
    }, status=200)

# 프로필 5단계 후 홈화면 보여주는 뷰

# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from .ProfileSerializer import SchoolProfileSerializer, FreeTimeListSerializer, InterestSerializer, BasicInfoSerializer, AddtionalInfoSerializer

# 학교 및 학과 프로필 API 뷰
class SchoolProfileAPIView(APIView):
    def post(self, request):
        serializer = SchoolProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()   
            return Response({"message": "학교 및 학과, 학년, 나이 정보가 성공적으로 저장되었습니다."}, status=200)
        else:
            return Response(serializer.errors, status=400)

#관심사 태그 등록
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

#공강시간 등록
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
        
# Basic Info (Nickname, MBTI, 성별, 자기소개) 등록
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

# Additional Info 등록
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
        next_name = step_mapping.get(profile.current_step)
        if wants_html(request) and next_name:
            return redirect(reverse(next_name))
        return Response({'current_step': profile.current_step, 'next_step': reverse(next_name) if next_name else None}, status=200)

    # 이하 추천/인기 프로필 데이터는 그대로 유지
    try:
        recommended_users = recommend_top_n(request.user, n=6)
        recommendations = []
        for recommended_user in recommended_users:
            recommended_profile = recommended_user.profile
            profile_interests = Interest.objects.filter(profileinterest__profile=recommended_profile)[:3]
            my_interests = Interest.objects.filter(profileinterest__profile=profile)
            my_interest_names = set(my_interests.values_list('name', flat=True))
            other_interest_names = set(profile_interests.values_list('name', flat=True))
            recommendations.append({
                'profile_id': recommended_profile.profile_id,
                'nickname': recommended_profile.nickname,
                'school': recommended_profile.school.school_name if recommended_profile.school else None,
                'department': recommended_profile.department.department_name if recommended_profile.department else None,
                'user_interests': [i.name for i in profile_interests],
                'average_rating': 4.5,
                'matching_score': 85,
                'common_interests': list(my_interest_names & other_interest_names)
            })
    except Exception as e:
        print(f"추천 시스템 오류: {e}")
        recommendations = []

    try:
        from django.db.models import Count
        from apps.profiles.models import ProfileInterest
        popular_users = Profile.objects.filter(
            current_step='completed',
            is_active=True
        ).exclude(user=request.user).annotate(
            interest_count=Count('interests', distinct=True)
        ).order_by('-interest_count', '-created_at')[:6]
        popular_profiles = []
        for popular_profile in popular_users:
            profile_interests = Interest.objects.filter(profileinterest__profile=popular_profile)[:3]
            popular_profiles.append({
                'profile_id': popular_profile.profile_id,
                'nickname': popular_profile.nickname,
                'school': popular_profile.school.school_name if popular_profile.school else None,
                'department': popular_profile.department.department_name if popular_profile.department else None,
                'user_interests': [i.name for i in profile_interests],
                'average_rating': 4.3
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
    }
    if wants_html(request):
        return render(request, 'profiles/profile_home.html', data)
    return Response(data, status=200)

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
        personality_keywords = list(additional_info.personality_keyword.values_list('keyword', flat=True))
    except AdditionalInfo.DoesNotExist:
        additional_info = None
        personality_keywords = []

    from apps.schedules.models import FreeTime, DayOfWeek
    schedule_data = [[] for _ in range(7)]
    try:
        user_freetimes = FreeTime.objects.filter(user=profile.user)
        for freetime in user_freetimes:
            day_index = freetime.day_of_week.value - 1
            start_hour = freetime.start_time.hour
            start_minute = freetime.start_time.minute
            end_hour = freetime.end_time.hour
            end_minute = freetime.end_time.minute
            start_index = (start_hour - 9) * 2 + (1 if start_minute >= 30 else 0)
            end_index = (end_hour - 9) * 2 + (1 if end_minute >= 30 else 0)
            for i in range(max(0, start_index), min(25, end_index)):
                if len(schedule_data[day_index]) <= i:
                    schedule_data[day_index].extend([False] * (i + 1 - len(schedule_data[day_index])))
                schedule_data[day_index][i] = True
            while len(schedule_data[day_index]) < 25:
                schedule_data[day_index].append(False)
    except Exception as e:
        print(f"스케줄 로드 오류: {e}")
        schedule_data = [[False] * 25 for _ in range(7)]

    matching_score = 85
    try:
        my_interests = Interest.objects.filter(profileinterest__profile__user=request.user)
        my_interest_names = set(my_interests.values_list('name', flat=True))
        other_interest_names = set(interests.values_list('name', flat=True))
        common_interests_count = len(my_interest_names & other_interest_names)
        if common_interests_count > 0:
            matching_score = min(95, 70 + (common_interests_count * 5))
    except Exception as e:
        print(f"매칭 계산 오류: {e}")
        common_interests_count = 0

    context = {
        'profile': {
            'profile_id': profile.profile_id,
            'nickname': profile.nickname,
            'school': profile.school.school_name if profile.school else None,
            'department': profile.department.department_name if profile.department else None,
        },
        'interests': list(interests.values_list('name', flat=True)),
        'additional_info': {
            'experience': additional_info.experience if additional_info else None,
            'conversation_style': additional_info.conversation_style if additional_info else None,
            'activity_location': additional_info.activity_location if additional_info else None,
            'goal_or_concern': additional_info.goal_or_concern if additional_info else None,
            'personality_keywords': personality_keywords,
        },
        'schedule': schedule_data,
        'matching_score': matching_score,
        'common_interests_count': common_interests_count,
    }
    if wants_html(request):
        return render(request, 'profiles/profile_detail.html', context)
    return Response(context, status=200)
    
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
    }
    return Response(data)
