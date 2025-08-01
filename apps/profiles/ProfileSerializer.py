# profiles/serializers.py
# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from rest_framework import serializers
from .models import School, Department, Profile

# 프로필 1단계 시리얼라이저
class SchoolProfileSerializer(serializers.Serializer):
    school_name = serializers.CharField()
    department = serializers.CharField()
    grade = serializers.CharField()
    age = serializers.IntegerField()

    def validate(self, data):
        school_name = data.get('school_name')
        department_name = data.get('department')

        try:
            school = School.objects.get(school_name=school_name)
        except School.DoesNotExist:
            raise serializers.ValidationError({'school_name': '존재하지 않는 학교입니다.'})

        if not Department.objects.filter(school=school, department_name=department_name).exists():
            raise serializers.ValidationError({'department': '해당 학교에 존재하지 않는 학과입니다.'})
        
        age = data.get('age')
        if age < 20 or age > 40:
            raise serializers.ValidationError({'age': '유효한 나이 범위는 20세 이상 40세 이하입니다.'})

        valid_grades = ['1 학년 (새내기)', '2 학년', '3 학년', '4 학년', '대학원생']
        if data.get('grade') not in valid_grades:
            raise serializers.ValidationError({'grade': '유효한 학년이 아닙니다.'})

        return data

    def create(self, validated_data):
        school_name = validated_data.pop('school_name')
        department_name = validated_data.pop('department')
        grade = validated_data.get('grade')
        age = validated_data.get('age')

        school = School.objects.get(school_name=school_name)
        department = Department.objects.get(school=school, department_name=department_name)

        user = self.context['request'].user

        return Profile.objects.create(
            user=user,
            school=school,
            department=department,
            grade=grade,
            age=age
        )
