from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_auth_test(request):
    user = request.user
    return Response({
        "message": f"인증된 유저입니다: {user.email}",
        "user_id": user.id,
    })