from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.interests.models import Interest 
from .serializers import InterestSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def interest_list(request):
    interests = Interest.objects.all()
    serializer = InterestSerializer(interests, many=True)
    return Response(serializer.data)

def interest_list_page(request):
    interests = Interest.objects.all()
    context = {
        'interests' : interests,
    }
    return render(request, 'interests/interest.html', context)