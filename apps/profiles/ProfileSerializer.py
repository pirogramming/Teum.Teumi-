# profiles/ProfileSerializer.py
# 프로필 5단계의 요청 데이터를 검증할 시리얼라이저
from rest_framework import serializers
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .models import School, Department, Profile, Personality, AdditionalInfo, ProfileInterest
from apps.interests.models import Interest
from apps.schedules.models import FreeTime, DayOfWeek
from datetime import time


# 프로필 간단 시리얼라이저
class ProfileSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'nickname', 'mbti']

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
        if age < 20 or age > 29:
            raise serializers.ValidationError({'age': '유효한 나이 범위는 20세 이상 29세 이하입니다.'})

        valid_grades = ['1 학년', '2 학년', '3 학년', '4 학년', '대학원생']
        if data.get('grade') not in valid_grades:
            raise serializers.ValidationError({'grade': '유효한 학년이 아닙니다.'})

        return data

    def create(self, validated_data):
        school_name = validated_data.get('school_name')
        department_name = validated_data.get('department')
        grade = validated_data.get('grade')
        age = validated_data.get('age')

        school = School.objects.get(school_name=school_name)
        department = Department.objects.get(school=school, department_name=department_name)

        user = self.context['request'].user

        # 기존 프로필이 있는지 확인
        try:
            profile = Profile.objects.get(user=user)
            # 기존 프로필 업데이트
            profile.school = school
            profile.department = department
            profile.grade = grade
            profile.age = age
            profile.current_step = 'step2'  # 다음 단계로 진행
            profile.save()
            return profile
        except Profile.DoesNotExist:
            # 새 프로필 생성
            return Profile.objects.create(
                user=user,
                school=school,
                department=department,
                grade=grade,
                age=age,
                current_step='step2'  # 다음 단계로 진행
            )

# 프로필 2단계 시리얼라이저
class InterestSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(
        child=serializers.IntegerField(),
        validators=[MinLengthValidator(4), MaxLengthValidator(4)],
        help_text="관심사 ID 리스트 (정확히 4개)"
    )

    def validate_interest_ids(self, ids):
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("중복된 관심사 태그입니다.")
        existing_ids = set(Interest.objects.filter(id__in=ids).values_list('id', flat=True))
        invalid_ids = set(ids) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"다음 ID는 존재하지 않습니다: {invalid_ids}")
        return list(existing_ids)

    def create(self, validated_data):
        user = self.context['request'].user
        interest_ids = validated_data['interest_ids']

        # 🔥 핵심 수정
        profile = Profile.objects.get(user=user)
        ProfileInterest.objects.filter(profile=profile).delete()

        for interest_id in interest_ids:
            ProfileInterest.objects.create(profile=profile, interest_id=interest_id)

        # 다음 단계로 진행 상태 업데이트
        profile.current_step = 'step3'
        profile.save()

        return {"message": "관심사가 성공적으로 저장되었습니다."}
    
# 프로필 3단계 시리얼라이저
# 공강시간 개별의 요청 데이터를 검증할 시리얼라이저
class FreeTimeSerializer(serializers.Serializer):
    day_of_week = serializers.CharField()  # ChoiceField에서 CharField로 변경
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])

    def validate_day_of_week(self, value):
        # 요일 축약형을 전체 이름으로 변환
        day_mapping = {
            'MON': 'Monday',
            'TUE': 'Tuesday', 
            'WED': 'Wednesday',
            'THU': 'Thursday',
            'FRI': 'Friday',
            'SAT': 'Saturday',
            'SUN': 'Sunday'
        }
        
        if value in day_mapping:
            return day_mapping[value]
        elif value in [choice[0] for choice in DayOfWeek.choices]:
            return value
        else:
            raise serializers.ValidationError(f"'{value}'은 유효하지 않은 요일입니다.")

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

        # 다음 단계로 진행 상태 업데이트
        profile = Profile.objects.get(user=user)
        profile.current_step = 'step4'
        profile.save()

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
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 다음 단계로 진행 상태 업데이트
        profile = Profile.objects.get(user=instance.user)
        profile.current_step = 'step5'
        profile.save()

        return instance

# 프로필 5단계 시리얼라이저
class AddtionalInfoSerializer(serializers.ModelSerializer):
    personality_keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="성격 키워드 리스트 (정확히 3개)"
    )

    class Meta:
        model = AdditionalInfo
        exclude = ['profile']
        extra_kwargs = {
            'experience': {'required': False, 'allow_null': True},
            'conversation_style': {'required': False, 'allow_null': True},
            'activity_location': {'required': False, 'allow_null': True},
            'goal_or_concern': {'required': False, 'allow_null': True},
        }

    def validate_personality_keywords(self, value):
        if value and len(value) != 3:
            raise serializers.ValidationError("성격 키워드는 반드시 3개를 선택해야 합니다.")
        
        # 키워드가 실제로 존재하는지 확인
        if value:
            existing_keywords = set(Personality.objects.filter(keyword__in=value).values_list('keyword', flat=True))
            invalid_keywords = set(value) - existing_keywords
            if invalid_keywords:
                raise serializers.ValidationError(f"존재하지 않는 키워드입니다: {invalid_keywords}")
        
        return value
    
    def create(self, validated_data):
        personality_keywords = validated_data.pop('personality_keywords', [])
        profile = validated_data.pop('profile')
        additional_info = AdditionalInfo.objects.create(profile=profile, **validated_data)
        
        if personality_keywords:
            personality_objects = Personality.objects.filter(keyword__in=personality_keywords)
            additional_info.personality_keyword.set(personality_objects)
        
        return additional_info
    
    def update(self, instance, validated_data):
        personality_keywords = validated_data.pop('personality_keywords', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if personality_keywords is not None:
            personality_objects = Personality.objects.filter(keyword__in=personality_keywords)
            instance.personality_keyword.set(personality_objects)

        # 프로필 완료 상태로 업데이트
        profile = Profile.objects.get(user=instance.profile.user)
        profile.current_step = 'completed'
        profile.save()

        return instance