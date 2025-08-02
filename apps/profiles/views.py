from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ProfileSerializer import SchoolProfileSerializer
from .models import Profile, Department, School 
from django.shortcuts import get_object_or_404

# 학교 및 학과 프로필 API 뷰
class SchoolProfileAPIView(APIView):
    def post(self, request):
        serializer = SchoolProfileSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            school_name = serializer.validated_data["school_name"]
            department_name = serializer.validated_data["department"]
            grade = serializer.validated_data["grade"]

            # school / department 객체 가져오기
            school = get_object_or_404(School, school_name=school_name)
            department = get_object_or_404(Department, department_name=department_name, school=school)

            # 프로필 업데이트
            profile = Profile.objects.get(user=user)
            profile.school = school
            profile.department = department
            profile.grade = grade
            profile.save()

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


def profile_input_page(request):        # 임시이니 이따 지우자
    universities = ["학교1", "학교2", "학교3"]
    majors = ["컴퓨터공학", "경영학", "심리학"]
    return render(request, "profiles/profile_2.html", {"universities": universities, "majors": majors})
