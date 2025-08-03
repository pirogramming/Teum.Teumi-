from rest_framework import serializers
from apps.users.models import UserInterest
from apps.interests.models import Interest
from rest_framework.exceptions import ValidationError

class UserInterestCreateSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    def create(self, validated_data):
        user = self.context['request'].user
        interest_ids = validated_data['interest_ids']
        created_interests = []
        already_exist = []

        for interest_id in interest_ids:
            try:
                interest = Interest.objects.get(id=interest_id)
                user_interest, created = UserInterest.objects.get_or_create(user=user, interest=interest)
                if created:
                    created_interests.append(user_interest)
                else:
                    already_exist.append(interest.name)
            except Interest.DoesNotExist:
                continue  
        if already_exist:
            raise ValidationError(
                {"error": f"이미 등록된 관심사입니다: {', '.join(already_exist)}"}
            )
        return created_interests
