# profiles/serializers.py
# 요청 데이터를 검증할 시리얼라이저
from rest_framework import serializers

class SchoolProfileSerializer(serializers.Serializer):
    school_name = serializers.CharField()
    department = serializers.CharField()
    grade = serializers.IntegerField()
