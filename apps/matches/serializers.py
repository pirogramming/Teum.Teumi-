from rest_framework import serializers
from .models import Matching, MatchingStatus
from django.contrib.auth import get_user_model

User = get_user_model()

# 유저앱에 시리얼라이저가 없어서 간단하게 만들어둠
class UserSimpleSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='profile.nickname', read_only=True)
    mbti = serializers.CharField(source='profile.mbti', read_only=True)
    username = serializers.CharField(read_only=True)
    department_name = serializers.CharField(source='profile.department.department_name', read_only=True, allow_null=True)
    grade = serializers.CharField(source='profile.grade', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'mbti', 'department_name', 'grade']


class MatchCreateSerializer(serializers.ModelSerializer):
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    request_message = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Matching
        fields = ['receiver', 'request_message']

class MatchDetailSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    receiver = UserSimpleSerializer(read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Matching
        fields = ['id', 'sender', 'receiver', 'status', 'status_label', 'matched_at', 'request_message', 'refusal_message', 'created_at']   