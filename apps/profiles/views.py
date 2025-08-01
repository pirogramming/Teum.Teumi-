from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

# 필요한 모델 import
from .models import Profile, Department, School 

# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from .ProfileSerializer import SchoolProfileSerializer

# 학교 및 학과 프로필 API 뷰
class SchoolProfileAPIView(APIView):
    def post(self, request):
        serializer = SchoolProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()   
            return Response({"message": "학교 및 학과 정보가 성공적으로 저장되었습니다."}, status=200)
        else:
            return Response(serializer.errors, status=400)

#공강시간 등록
class FreeTimeAPIView(APIView):
    pass
#관심사 태그 등록
class InterestTagAPIView(APIView):
    pass
# Basic Info (Nickname, MBTI) 등록
class BasicInfoAPIView(APIView):
    pass
# Additional Info 등록
class AddtionalInfoAPIView(APIView):
    pass