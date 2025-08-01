# profiles/serializers.py
# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from rest_framework import serializers
from .models import School, Department, Profile
from apps.schedules.models import FreeTime, DayOfWeek
from datetime import time

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
# 프로필 2단계 시리얼라이저
class InterestSerializer(serializers.Serializer):
    pass
# 프로필 3단계 시리얼라이저
# 공강시간 개별의 요청 데이터를 검증할 시리얼라이저
class FreeTimeSerializer(serializers.Serializer):
    day_of_week = serializers.ChoiceField(choices=DayOfWeek.choices)
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])

    def validate(self, data):
        start = data.get('start_time')
        end = data.get('end_time')

        if start >= end:
            raise serializers.ValidationError({"error": "종료 시간은 시작 시간보다 이후여야 합니다."})
        
        # 시간은 24시간 단위로 입력되며, 30분 단위로 입력되어야 합니다.
        if start.minute not in (0, 30) or end.minute not in (0, 30):
            raise serializers.ValidationError({
                "error": "시작 시간과 종료 시간은 30분 단위로 입력되어야 합니다. (예: 09:00, 09:30)"
            })

        return data
    
# 공강시간 전체 등록 요청 데이터를 검증할 시리얼라이저
class FreeTimeListSerializer(serializers.Serializer):
    free_times = FreeTimeSerializer(many=True)

    def create(self, validated_data):
        user = self.context['request'].user
        free_time_data = validated_data['free_times']

        # 기존 공강 시간 삭제 후 새로 등록
        FreeTime.objects.filter(user=user).delete()

        for entry in free_time_data:
            FreeTime.objects.create(user=user, **entry)

        return {"message": "공강 시간이 성공적으로 등록되었습니다."}
    
# 프로필 4단계 시리얼라이저
class BasicInfoSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50)
    mbti = serializers.ChoiceField(choices=Profile.MBTI_CHOICES)
    gender = serializers.ChoiceField(choices=Profile.GENDER_CHOICES)
    introduction = serializers.CharField(min_length=50)

    def validate(self, data):
        user = self.context['request'].user

        # 닉네임 중복 검사
        nickname = data.get('nickname')
        if Profile.objects.exclude(user=user).filter(nickname=nickname).exists():
            raise serializers.ValidationError({"nickname": "이미 사용 중인 닉네임입니다."})

        # MBTI 검사
        valid_mbti = [choice[0] for choice in Profile.MBTI_CHOICES]
        if data.get('mbti') not in valid_mbti:
            raise serializers.ValidationError({"mbti": "유효한 MBTI 값이 아닙니다."})

        # 성별 검사
        valid_gender = [choice[0] for choice in Profile.GENDER_CHOICES]
        if data.get('gender') not in valid_gender:
            raise serializers.ValidationError({"gender": "유효한 성별 값이 아닙니다."})

        # 자기소개 글자 수 검사
        if len(data.get('introduction', '').strip()) < 50:
            raise serializers.ValidationError({"introduction": "자기소개는 최소 50자 이상 작성해야 합니다."})

        return data

    def update(self, instance, validated_data):
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.mbti = validated_data.get('mbti', instance.mbti)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.introduction = validated_data.get('introduction', instance.introduction)
        instance.save()
        return instance

# 프로필 5단계 시리얼라이저
class AddtionalInfoSerializer(serializers.Serializer):
    pass