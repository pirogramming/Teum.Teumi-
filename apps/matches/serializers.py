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
    request_message = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Matching
        fields = ['request_message']

    def validate(self, attrs):
        request = self.context['request']
        raw_profile_id = request.data.get('to_profile_id') or request.data.get('profile_id')
        if not raw_profile_id:
            raise serializers.ValidationError({"receiver": ["profile_id가 필요합니다."]})

        from apps.profiles.models import Profile
        try:
            profile = Profile.objects.select_related('user').get(pk=int(raw_profile_id))
        except (ValueError, Profile.DoesNotExist):
            raise serializers.ValidationError({"receiver": ["대상 프로필을 찾을 수 없습니다."]})

        attrs['receiver'] = profile.user
        return attrs

class MatchDetailSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    receiver = UserSimpleSerializer(read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Matching
        fields = ['id', 'sender', 'receiver', 'status', 'status_label', 'matched_at', 'request_message', 'refusal_message', 'created_at']   