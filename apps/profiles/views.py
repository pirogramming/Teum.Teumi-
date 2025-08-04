# 안쓰는 모듈 
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# 필요한 모듈 import
from .models import Profile, School, Department, AdditionalInfo
from apps.users.models import User
from apps.interests.models import Interest
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from .models import School, Department, Profile, Personality

from apps.matches.services.recommend import recommend_top_n

# 필요한 모듈 import

#소셜 로그인후 프로필 1단계 보여주는 뷰
@login_required
def profile_step1(request):
    # 사용자의 현재 진행 단계 확인
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        
        # 현재 단계가 step1보다 나중이면 해당 단계로 리다이렉트
        if current_step != 'step1':
            step_mapping = {
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3', 
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'home'  # 완료되면 홈으로
            }
            if current_step in step_mapping:
                return redirect(step_mapping[current_step])
    except Profile.DoesNotExist:
        pass  # 프로필이 없으면 step1 진행
    
    universities = School.objects.all()
    return render(request, 'profiles/profile_1.html', {
        'universities': universities,
    })

# 학교에 맞는 학과명 보여주는 뷰
@login_required
def get_majors_by_school(request):
    school_name = request.GET.get('school_name')
    try:
        school = School.objects.get(school_name=school_name)
        majors = Department.objects.filter(school=school).values_list('department_name', flat=True)
        return JsonResponse({'majors': list(majors)})
    except School.DoesNotExist:
        return JsonResponse({'majors': []})

# 프로필 1단계 후 2단계 보여주는 뷰
@login_required
def profile_step2(request):
    # 사용자의 현재 진행 단계 확인
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        
        # step1을 완료하지 않았으면 step1으로 리다이렉트
        if current_step == 'step1':
            return redirect('profiles:profile_step1')
        
        # 현재 단계가 step2보다 나중이면 해당 단계로 리다이렉트
        if current_step not in ['step1', 'step2']:
            step_mapping = {
                'step3': 'profiles:profile_step3', 
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'home'
            }
            if current_step in step_mapping:
                return redirect(step_mapping[current_step])
    except Profile.DoesNotExist:
        return redirect('profiles:profile_step1')  # 프로필이 없으면 step1으로
    
    from apps.interests.models import Interest
    interests = Interest.objects.all()
    
    return render(request, 'profiles/profile_2.html', {
        'interests': interests,
    })

@login_required
def profile_step3(request):
    # 사용자의 현재 진행 단계 확인
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        
        # 이전 단계들을 완료하지 않았으면 해당 단계로 리다이렉트
        if current_step in ['step1', 'step2']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2'
            }
            return redirect(step_mapping[current_step])
        
        # 현재 단계가 step3보다 나중이면 해당 단계로 리다이렉트
        if current_step not in ['step1', 'step2', 'step3']:
            step_mapping = {
                'step4': 'profiles:profile_step4',
                'step5': 'profiles:profile_step5',
                'completed': 'home'
            }
            if current_step in step_mapping:
                return redirect(step_mapping[current_step])
    except Profile.DoesNotExist:
        return redirect('profiles:profile_step1')
    
    return render(request, 'profiles/profile_3.html')

@login_required
def profile_step4(request):
    # 사용자의 현재 진행 단계 확인
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        
        # 이전 단계들을 완료하지 않았으면 해당 단계로 리다이렉트
        if current_step in ['step1', 'step2', 'step3']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3'
            }
            return redirect(step_mapping[current_step])
        
        # 현재 단계가 step4보다 나중이면 해당 단계로 리다이렉트
        if current_step not in ['step1', 'step2', 'step3', 'step4']:
            step_mapping = {
                'step5': 'profiles:profile_step5',
                'completed': 'home'
            }
            if current_step in step_mapping:
                return redirect(step_mapping[current_step])
    except Profile.DoesNotExist:
        return redirect('profiles:profile_step1')
    
    return render(request, 'profiles/profile_4.html')

@login_required
def profile_step5(request):
    # 사용자의 현재 진행 단계 확인
    try:
        profile = Profile.objects.get(user=request.user)
        current_step = profile.current_step
        
        # 이전 단계들을 완료하지 않았으면 해당 단계로 리다이렉트
        if current_step in ['step1', 'step2', 'step3', 'step4']:
            step_mapping = {
                'step1': 'profiles:profile_step1',
                'step2': 'profiles:profile_step2',
                'step3': 'profiles:profile_step3',
                'step4': 'profiles:profile_step4'
            }
            return redirect(step_mapping[current_step])
        
        # 완료된 경우 홈으로 리다이렉트
        if current_step == 'completed':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('profiles:profile_step1')
    
    try:
        profile = Profile.objects.get(user=request.user)
        additional_info = getattr(profile, 'additional_info', None)
    except Profile.DoesNotExist:
        additional_info = None
    personality_keywords = list(Personality.objects.values_list('keyword', flat=True))
    return render(request, 'profiles/profile_5.html', {
        'additional_info': additional_info,
        'personality_keywords': personality_keywords,
    })

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

# 프로필 홈 페이지 뷰
def profile_home(request):
    """프로필 홈 페이지를 렌더링하는 뷰"""
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # 프로필이 없으면 step1로 리다이렉트
        return redirect('profiles:profile_step1')
    
    # 프로필이 비활성화 상태면 홈으로 리다이렉트
    if not profile.is_active:
        return redirect('home')
    
    # 프로필이 완료되지 않았다면 단계별 페이지로 리다이렉트
    if not profile.current_step == 'completed':
        # 현재 단계에 따라 적절한 페이지로 리다이렉트
        step_mapping = {
            'step1': 'profiles:profile_step1',
            'step2': 'profiles:profile_step2',
            'step3': 'profiles:profile_step3',
            'step4': 'profiles:profile_step4',
            'step5': 'profiles:profile_step5'
        }
        return redirect(step_mapping.get(profile.current_step, 'profiles:profile_step1'))
    
    # 프로필이 완료된 경우 홈 페이지 렌더링
    return render(request, 'profiles/profile_home.html', {'profile': profile})

# 프로필 상세 페이지 뷰
def profile_detail(request, profile_id):
    """프로필 상세 페이지를 렌더링하는 뷰"""
    
    try:
        profile = get_object_or_404(
            Profile.objects.select_related('user', 'school', 'department'),
            profile_id=profile_id,
            is_active=True
        )
    except Http404:
        raise Http404("프로필을 찾을 수 없습니다.")
    
    # 사용자 관심사 가져오기
    interests = Interest.objects.filter(userinterest__user=profile.user)
    
    # 추가 정보 가져오기
    try:
        additional_info = AdditionalInfo.objects.get(profile=profile)
        # 성격 키워드 가져오기
        personality_keywords = additional_info.personality_keyword.all()
    except AdditionalInfo.DoesNotExist:
        additional_info = None
        personality_keywords = []

    # AI 추천 대화 주제 생성 (더미 데이터)
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
    
    # 추천 매칭 대상 가져오기(상위 3명)
    top_matches = recommend_top_n(request.user)[:3]
    
    context = {
        'profile': profile,
        'interests': interests,
        'additional_info': additional_info,
        'personality_keywords': personality_keywords,
        'conversation_recommendations': conversation_recommendations,
        'top_matches': top_matches,
    }
    return render(request, 'profiles/profile_detail.html', context)
    
def patch(self, request):
    """기존 추가 정보 수정"""
    try:
        profile = Profile.objects.get(user=request.user)
        additional_info = getattr(profile, 'additional_info', None)
        
        if additional_info:
            serializer = AddtionalInfoSerializer(additional_info, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "추가 정보가 성공적으로 수정되었습니다."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 추가 정보가 없으면 새로 생성
            return self.post(request)
    except Profile.DoesNotExist:
        return Response({'error': '프로필을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
