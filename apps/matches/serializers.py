from rest_framework import serializers
from .models import Matching
from django.contrib.auth import get_user_model

User = get_user_model()

# 유저앱에 시리얼라이저가 없어서 간단하게 만들어둠
class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nickname', 'mbti']


class MatchCreateSerializer(serializers.ModelSerializer):
    receiver = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Matching._meta.get_field('receiver').remote_field.model.objects.all())
    request_message = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Matching
        fields = ['receiver', 'request_message']

class MatchDetailSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    receiver = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Matching
        fields = ['id', 'sender', 'receiver', 'status', 'matched_at', 'request_message', 'refusal_message', 'created_at']