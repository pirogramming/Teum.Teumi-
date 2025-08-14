from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.reviews.serializers import ReviewCreateSerializer
from apps.reviews.models import Review


class ReviewCreateView(APIView):
    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            return Response(
                {
                    "message": "후기 작성이 완료되었습니다.",
                    "review_id": review.id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
