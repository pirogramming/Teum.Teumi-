from rest_framework import serializers
from apps.users.models import UserInterest
from apps.interests.models import Interest

class UserInterestCreateSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    def create(self, validated_data):
        user = self.context['request'].user
        interest_ids = validated_data['interest_ids']
        created_interests = []

        for interest_id in interest_ids:
            try:
                interest = Interest.objects.get(id=interest_id)
                user_interest, created = UserInterest.objects.get_or_create(user=user, interest=interest)
                if created:
                    created_interests.append(user_interest)
            except Interest.DoesNotExist:
                continue  

        return created_interests
