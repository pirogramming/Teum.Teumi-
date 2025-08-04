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


class ReviewListView(APIView):
    def get(self, request):
        user = request.user
        reviews = Review.objects.filter(target=user).select_related("user")
        data = []
        for review in reviews:
            data.append({
                "review_id": review.id,
                "match_id": review.match.id,
                "reviewer_nickname": review.user.nickname if hasattr(review.user, "nickname") else "",
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
            })
        return Response(data, status=status.HTTP_200_OK)
