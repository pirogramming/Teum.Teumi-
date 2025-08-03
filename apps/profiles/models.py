# apps/profiles/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.core.models import BaseEntity

# 학교 테이블
class School(models.Model):
    # 학교 기본키
    school_id = models.BigAutoField(primary_key=True)

    school_name = models.CharField(max_length=50) #학교이름
    school_code = models.CharField(max_length=50)  # 공공데이터 기준 학교 코드
    location = models.CharField(max_length=50, null=True, blank=True) #지역명
    school_type = models.CharField(max_length=50, null=True, blank=True)  # 예: 진문대, 4년제대학 등

    def __str__(self):
        return self.school_name

# 학과 테이블
class Department(models.Model):
    # 학과 기본키
    department_id = models.BigAutoField(primary_key=True)

    # 외래키
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments') # 학교와의 관계를 명시

    department_name = models.CharField(max_length=50) #학과이름
    major_code = models.CharField(max_length=50, null=True, blank=True) # 공공데이터 기준 학과 코드
    degree_type = models.CharField(max_length=50, null=True, blank=True)  # 학사, 석사 등
    category = models.CharField(max_length=50, null=True, blank=True)     # 공학, 인문, 예체능 등
    college_name = models.CharField(max_length=100, null=True, blank=True)  # 소속 단과대학
    main_subject = models.TextField(null=True, blank=True)  # 주요 커리큘럼
    related_career = models.TextField(null=True, blank=True)  # 관련 직업

    def __str__(self):
        return f"{self.school.school_name} - {self.department_name}"

# 프로필 테이블
class Profile(BaseEntity):
    # 성별과 MBTI 선택지
    GENDER_CHOICES = [
        ('M', '남자'),
        ('F', '여자'),
    ]

    MBTI_CHOICES = [
        ('INTJ', 'INTJ'), ('INTP', 'INTP'), ('ENTJ', 'ENTJ'), ('ENTP', 'ENTP'),
        ('INFJ', 'INFJ'), ('INFP', 'INFP'), ('ENFJ', 'ENFJ'), ('ENFP', 'ENFP'),
        ('ISTJ', 'ISTJ'), ('ISFJ', 'ISFJ'), ('ESTJ', 'ESTJ'), ('ESFJ', 'ESFJ'),
        ('ISTP', 'ISTP'), ('ISFP', 'ISFP'), ('ESTP', 'ESTP'), ('ESFP', 'ESFP'),
    ]
    
    # 프로필 기본키
    profile_id = models.BigAutoField(primary_key=True)

    # 외래키
    school = models.ForeignKey(School, null=True, blank=True, on_delete=models.SET_NULL, related_name='profiles') # 학교와의 관계
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name='profiles') # 학과와의 관계
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profile') # 사용자와의 관계

    nickname = models.CharField(max_length=50, null=True, blank=True) # 닉네임
    age = models.BigIntegerField(null=True, blank=True) # 나이
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True) # 성별
    grade = models.CharField(max_length=50, null=True, blank=True) # 학년
    mbti = models.CharField(max_length=4, choices=MBTI_CHOICES, null=True, blank=True) # MBTI
    introduction = models.TextField(null=True, blank=True) # 자기소개

    is_active = models.BooleanField(default=True) # 프로필 활성화 여부
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}의 프로필"


# --- 프로필 5단계 추가정보 테이블 ---
# 성격키워드를 저장하는 클래스
class Personality(models.Model):
    keyword = models.CharField(max_length=50, unique=True, null=False)
    def __str__(self):
        return self.keyword

# 선호하는 대화 스타일을 저장하는 클래스
class ConversationStyle(models.TextChoices):
    CASUAL = "casual", "수다형"
    DEEP = "deep", "깊은대화형"
    HUMOR = "humor", "유머형"
    DEBATE = "debate", "토론형"

    def __str__(self):
        return self.label

class AdditionalInfo(BaseEntity):
    # 추가 정보 기본키
    additional_info_id = models.BigAutoField(primary_key=True)

    # 외래키
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='additional_info')

    experience = models.TextField(null=True, blank=True)
    conversation_style = models.CharField(max_length=100,choices=ConversationStyle.choices,null=True,blank=True)
    activity_location = models.CharField(max_length=100, null=True, blank=True)
    personality_keyword = models.ManyToManyField(Personality, blank=True)
    goal_or_concern = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile.nickname or self.profile.user.username}의 추가 정보"
