from rest_framework import serializers
from apps.users.models import UserInterest
from apps.interests.models import Interest

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']
