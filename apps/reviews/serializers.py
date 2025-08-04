from rest_framework import serializers
from .models import Review
from apps.matches.models import Matching

class ReviewCreateSerializer(serializers.Serializer):
    match_id = serializers.IntegerField()
    rating = serializers.DecimalField(max_digits=2, decimal_places=1)
    comment = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data):
        user = self.context["request"].user
        match_id = validated_data.get("match_id")
        rating = validated_data.get("rating")
        comment = validated_data.get("comment", "")

        match = Matching.objects.get(id=match_id)

        if match.sender == user:
            target = match.receiver
        elif match.receiver == user:
            target = match.sender
        else:
            raise serializers.ValidationError("해당 매칭에 속한 유저가 아닙니다.")

        review = Review.objects.create(
            user=user,
            target=target,
            match=match,
            rating=rating,
            comment=comment
        )
        return review