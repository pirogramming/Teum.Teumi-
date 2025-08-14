from rest_framework import serializers
from .models import Review, ReviewAttitude, ReviewValue, ConversationAttitude, ConversationValue
from apps.matches.models import Matching
from django.db import transaction

class ReviewCreateSerializer(serializers.Serializer):
    match_id = serializers.IntegerField(help_text="매칭 ID")
    rating = serializers.DecimalField(max_digits=2, decimal_places=1, help_text="매너온도 점수")
    comment = serializers.CharField(allow_blank=True, required=False, help_text="한 줄 후기 (선택)")
    attitude_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="대화태도 ID 리스트"
    )
    degree_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="대화가치 ID 리스트"
    )
    meeting = serializers.IntegerField(required=False, help_text="재만남 여부 (1: True, 2: False)")


    def validate_meeting(self, value):
        """
        meeting 값을 1은 True, 0은 False로 변환합니다.
        """
        if value == 1:
            return True
        elif value == 2:
            return False
        raise serializers.ValidationError("meeting 값은 1 또는 2이어야 합니다.")

    def validate(self, data):
        """
        attitude_ids와 degree_ids의 유효성을 검사합니다.
        """
        attitude_ids = data.get('attitude_ids', [])
        degree_ids = data.get('degree_ids', [])

        # attitude_ids 유효성 검사
        existing_attitude_ids = set(ConversationAttitude.objects.filter(id__in=attitude_ids).values_list('id', flat=True))
        invalid_attitude_ids = set(attitude_ids) - existing_attitude_ids
        if invalid_attitude_ids:
            raise serializers.ValidationError(f"다음 대화태도 ID는 존재하지 않습니다: {invalid_attitude_ids}")

        # degree_ids 유효성 검사
        existing_degree_ids = set(ConversationValue.objects.filter(id__in=degree_ids).values_list('id', flat=True))
        invalid_degree_ids = set(degree_ids) - existing_degree_ids
        if invalid_degree_ids:
            raise serializers.ValidationError(f"다음 대화가치 ID는 존재하지 않습니다: {invalid_degree_ids}")

        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        match_id = validated_data.pop("match_id")
        attitude_ids = validated_data.pop("attitude_ids", [])
        degree_ids = validated_data.pop("degree_ids", [])
        
        try:
            match = Matching.objects.get(id=match_id)
        except Matching.DoesNotExist:
            raise serializers.ValidationError("해당 매칭이 존재하지 않습니다.")

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
            **validated_data
        )
        # 대화태도와 대화가치 저장
        if attitude_ids:
            review_attitudes = [ReviewAttitude(review=review, attitude_id=attitude_id) for attitude_id in attitude_ids]
            ReviewAttitude.objects.bulk_create(review_attitudes)
        
        if degree_ids:
            review_values = [ReviewValue(review=review, value_id=degree_id) for degree_id in degree_ids]
            ReviewValue.objects.bulk_create(review_values)
        
        return review