from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.reviews.serializers import ReviewCreateSerializer
from apps.reviews.models import Review
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from apps.users.models import User  # 경로는 실제 프로젝트 구조에 맞게 수정 필요


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


# 특정유저에 대한 리뷰의 평균 평점과 재만남 점수를 계산 후 반환
class ReviewSummaryView(APIView):
    def get(self, request, user_id):
        """
        특정 유저가 받은 리뷰의 평균 평점과 재만남 점수를 계산하여 반환하는 GET API
        """
        user = get_object_or_404(User, id=user_id)

        average_rating = Review.objects.filter(target=user).aggregate(avg=Avg("rating"))["avg"] or 0

        meeting_counts = (
            Review.objects.filter(target=user)
            .values("meeting")
            .annotate(count=Count("meeting"))
        )
        count_map = {item["meeting"]: item["count"] for item in meeting_counts}
        yes = count_map.get(1, 0)
        no = count_map.get(2, 0)

        total = yes + no
        meeting_score = 0
        if total > 0:
            meeting_score = int((yes / total) * 100)

        return Response({
            "user_id": user.id,
            "average_rating": round(average_rating, 2),
            "meeting_yes_count": yes,
            "meeting_no_count": no,
            "meeting_score": meeting_score,
        }, status=status.HTTP_200_OK)

