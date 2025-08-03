from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from django.http import Http404
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# 필요한 모듈 import
from .models import Profile, School, Department, AdditionalInfo
from apps.users.models import User, UserInterest
from apps.interests.models import Interest

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
    def post(self, request):
        serializer = InterestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "관심사가 성공적으로 저장되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#공강시간 등록
class FreeTimeAPIView(APIView):
    def post(self, request):
        serializer = FreeTimeListSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "공강 시간이 성공적으로 등록되었습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
# Basic Info (Nickname, MBTI, 성별, 자기소개) 등록
class BasicInfoAPIView(APIView):
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
    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = AddtionalInfoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response({"message": "추가 정보가 성공적으로 저장되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 프로필 홈 페이지 뷰
def profile_home(request):
    """프로필 홈 페이지를 렌더링하는 뷰"""
    
    # 현재 사용자 제외하고 프로필이 있는 사용자들 가져오기
    all_profiles = Profile.objects.exclude(
        user=request.user if request.user.is_authenticated else None
    ).filter(
        is_active=True,
        nickname__isnull=False
    ).select_related('user', 'school', 'department')
    
    # AI 추천 프로필 (랜덤으로 3명 선택)
    recommendations = list(all_profiles)
    random.shuffle(recommendations)
    recommendations = recommendations[:3]
    
    # 각 추천 프로필에 추가 정보 붙이기
    for profile in recommendations:
        # 사용자 관심사 가져오기
        profile.interests = Interest.objects.filter(
            userinterest__user=profile.user
        )[:4]  # 최대 4개만
        
        # 평균 평점 (더미 데이터)
        profile.average_rating = round(random.uniform(4.2, 4.9), 1)
        
        # 매칭 점수 (더미 데이터)
        profile.matching_score = random.randint(75, 95)
        
        # 공통 관심사 (더미 데이터)
        profile.common_interests = list(profile.interests)[:2]
    
    # 인기 프로필 (프로필이 완성도가 높은 순으로 정렬)
    popular_profiles = all_profiles.filter(
        introduction__isnull=False,
        age__isnull=False,
        mbti__isnull=False
    )[:6]
    
    # 인기 프로필에도 추가 정보 붙이기
    for profile in popular_profiles:
        profile.interests = Interest.objects.filter(
            userinterest__user=profile.user
        )[:1]  # 첫 번째 관심사만
        profile.average_rating = round(random.uniform(4.0, 4.8), 1)
    
    context = {
        'recommendations': recommendations,
        'popular_profiles': popular_profiles,
    }
    
    return render(request, 'profiles/profile.home.html', context)

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
    
    # 더미 시간표 데이터 (실제로는 schedules 앱에서 가져와야 함)
    dummy_schedule = [
        # 월요일부터 일요일까지 각각 25개 슬롯 (9:00-21:00, 30분 단위)
        [False] * 25 for _ in range(7)
    ]
    
    # 랜덤하게 몇 개 시간대를 사용 가능으로 설정
    for day in range(7):
        available_slots = random.sample(range(25), random.randint(3, 8))
        for slot in available_slots:
            dummy_schedule[day][slot] = True
    
    context = {
        'profile': profile,
        'interests': interests,
        'additional_info': additional_info,
        'personality_keywords': personality_keywords,
        'conversation_recommendations': conversation_recommendations,
        'schedule': dummy_schedule,
        'average_rating': round(random.uniform(4.0, 4.8), 1),
        'matching_score': random.randint(75, 95),
        'common_interests_count': random.randint(2, 5),
    }
    
    return render(request, 'profiles/profile_detail.html', context)