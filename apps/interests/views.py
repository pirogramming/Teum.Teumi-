from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.interests.models import Interest 
from .serializers import InterestSerializer
from apps.profiles.models import School

@api_view(['GET'])
@permission_classes([AllowAny])
def interest_list(request):
    interests = Interest.objects.all()
    serializer = InterestSerializer(interests, many=True)
    return Response(serializer.data)

def interest_list_page(request):
    interests = Interest.objects.all()
    universities = School.objects.prefetch_related('departments').all()

    # 직렬화하여 학과 포함한 JSON 생성
    universities_data = []
    for uni in universities:
        universities_data.append({
            'school_id': uni.school_id,
            'school_name': uni.school_name,
            'departments': [
                {'department_id': dept.department_id, 'department_name': dept.department_name}
                for dept in uni.departments.all()
            ]
        })

    context = {
        'interests' : interests,
        'universities' : universities,
        'universities_json': universities_data,  # 템플릿에서 JSON으로 사용
    }
    return render(request, 'interests/interest.html', context)