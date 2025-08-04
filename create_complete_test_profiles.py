#!/usr/bin/env python
"""
완전한 프로필 데이터 생성 스크립트
프로필 1~5단계를 모두 완성한 사용자들을 생성합니다.
"""

import os
import sys
import django
from django.conf import settings

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from datetime import time
from apps.profiles.models import Profile, School, Department, AdditionalInfo, Personality
from apps.interests.models import Interest
from apps.profiles.models import ProfileInterest
from apps.schedules.models import FreeTime, DayOfWeek

User = get_user_model()

def create_test_data():
    print("🎯 완전한 테스트 프로필 데이터 생성을 시작합니다...")
    
    # 1. 학교 데이터 생성
    schools_data = [
        {'name': '동국대학교', 'code': 'DGU', 'location': '서울', 'type': '4년제대학'},
        {'name': '연세대학교', 'code': 'YU', 'location': '서울', 'type': '4년제대학'},
        {'name': '고려대학교', 'code': 'KU', 'location': '서울', 'type': '4년제대학'},
        {'name': '서울대학교', 'code': 'SNU', 'location': '서울', 'type': '4년제대학'},
        {'name': '성균관대학교', 'code': 'SKKU', 'location': '서울', 'type': '4년제대학'},
    ]
    
    schools = {}
    for school_data in schools_data:
        school, created = School.objects.get_or_create(
            school_name=school_data['name'],
            defaults={
                'school_code': school_data['code'],
                'location': school_data['location'],
                'school_type': school_data['type']
            }
        )
        schools[school_data['name']] = school
        if created:
            print(f"📚 학교 생성: {school.school_name}")
    
    # 2. 학과 데이터 생성
    departments_data = [
        {'school': '동국대학교', 'name': '컴퓨터공학과', 'category': '공학'},
        {'school': '동국대학교', 'name': '경영학과', 'category': '상경'},
        {'school': '동국대학교', 'name': '영어영문학과', 'category': '인문'},
        {'school': '연세대학교', 'name': '심리학과', 'category': '사회과학'},
        {'school': '연세대학교', 'name': '디자인학과', 'category': '예체능'},
        {'school': '고려대학교', 'name': '경제학과', 'category': '상경'},
        {'school': '고려대학교', 'name': '국어국문학과', 'category': '인문'},
        {'school': '서울대학교', 'name': '전자공학과', 'category': '공학'},
        {'school': '성균관대학교', 'name': '화학과', 'category': '자연과학'},
    ]
    
    departments = {}
    for dept_data in departments_data:
        dept, created = Department.objects.get_or_create(
            school=schools[dept_data['school']],
            department_name=dept_data['name'],
            defaults={'category': dept_data['category']}
        )
        departments[f"{dept_data['school']}-{dept_data['name']}"] = dept
        if created:
            print(f"🏫 학과 생성: {dept.school.school_name} {dept.department_name}")
    
    # 3. 관심사 데이터 생성
    interests_data = [
        '창업', '개발', '취업', '진로', 'AI', 'UX/UI', '마케팅', '투자', 
        '데이터분석', '디자인', '외국어', '스터디', '프로젝트관리', '경제', 
        '금융', '컨설팅', '기획', '영업', '교환학생', '인턴십',
        '블록체인', '게임개발', '모바일앱', '웹개발', '머신러닝'
    ]
    
    interests = {}
    for interest_name in interests_data:
        interest, created = Interest.objects.get_or_create(
            name=interest_name
        )
        interests[interest_name] = interest
        if created:
            print(f"🌱 관심사 생성: {interest.name}")
    
    # 4. 성격 키워드 데이터 생성
    personality_data = [
        '차분함', '논리적', '센스있는', '분석적', '꼼꼼함', '창의적', 
        '사교적', '열정적', '배려심있는', '리더십있는', '유머러스', '진중함',
        '적극적', '신중함', '낙관적', '현실적', '독립적', '협력적'
    ]
    
    personalities = {}
    for personality_name in personality_data:
        personality, created = Personality.objects.get_or_create(
            keyword=personality_name
        )
        personalities[personality_name] = personality
        if created:
            print(f"🎭 성격 키워드 생성: {personality.keyword}")
    
    # 5. 완전한 프로필을 가진 사용자들 생성
    complete_users_data = [
        {
            'username': 'kim_haneul',
            'email': 'kim.haneul@email.com',
            'nickname': '하늘빛코딩',
            'age': 22,
            'gender': 'F',
            'grade': '3학년',
            'mbti': 'ENFP',
            'school': '동국대학교',
            'department': '컴퓨터공학과',
            'introduction': '안녕하세요! 개발과 디자인에 관심이 많은 3학년 김하늘입니다. UX/UI에 특히 관심이 많고, 사용자 중심의 서비스를 만드는 것이 꿈이에요. 스타트업 창업을 목표로 하고 있어서 같은 꿈을 가진 분들과 네트워킹하고 싶습니다.',
            'interests': ['창업', 'UX/UI', '개발', '디자인'],
            'experience': 'UX/UI 해커톤 2회 참가, 스타트업 인턴 경험 있어요',
            'conversation_style': 'deep',
            'activity_location': '혜화 캠퍼스 위주로 활동해요',
            'personalities': ['창의적', '열정적', '적극적'],
            'goal': '내년에 스타트업 창업을 목표로 하고 있어요',
            'schedule': {
                'Monday': [('14:00', '16:00'), ('18:00', '21:00')],
                'Tuesday': [('10:00', '12:00'), ('15:30', '18:00')],
                'Wednesday': [('13:00', '15:00'), ('19:00', '21:00')],
                'Thursday': [('11:00', '13:30'), ('16:00', '17:30')],
                'Friday': [('14:30', '17:00')],
                'Saturday': [('10:00', '18:00')],  # 주말은 비교적 자유
                'Sunday': [('11:00', '17:00')]
            }
        },
        {
            'username': 'lee_dohyun',
            'email': 'lee.dohyun@email.com',
            'nickname': '데이터마니아',
            'age': 24,
            'gender': 'M',
            'grade': '4학년',
            'mbti': 'INTJ',
            'school': '연세대학교',
            'department': '심리학과',
            'introduction': '심리학을 전공하면서 데이터 분석에 관심을 갖게 된 4학년 이도현입니다. 사람의 행동을 데이터로 분석하고 인사이트를 찾는 일에 흥미를 느껴요. 현재 데이터 사이언티스트로의 전환을 준비하고 있습니다.',
            'interests': ['데이터분석', '머신러닝', '진로', '스터디'],
            'experience': '데이터 분석 관련 인턴십 2회, 심리학 연구 프로젝트 다수 참여',
            'conversation_style': 'casual',
            'activity_location': '신촌 캠퍼스 주변에서 주로 활동해요',
            'personalities': ['논리적', '분석적', '신중함'],
            'goal': '데이터 사이언티스트로 취업하는 것이 목표예요',
            'schedule': {
                'Monday': [('10:30', '12:00'), ('15:00', '17:30')],
                'Tuesday': [('13:00', '16:00'), ('18:30', '21:00')],
                'Wednesday': [('09:30', '11:00'), ('14:00', '16:30')],
                'Thursday': [('11:30', '14:00'), ('17:00', '19:00')],
                'Friday': [('10:00', '13:00'), ('16:00', '18:00')],
                'Saturday': [('12:00', '20:00')],
                'Sunday': [('10:00', '16:00')]
            }
        },
        {
            'username': 'park_seojin',
            'email': 'park.seojin@email.com',
            'nickname': '금융퀸',
            'age': 21,
            'gender': 'F',
            'grade': '2학년',
            'mbti': 'ESFJ',
            'school': '고려대학교',
            'department': '경제학과',
            'introduction': '경제학과 2학년 박서진입니다! 금융과 투자에 관심이 많고, 특히 ESG 투자와 지속가능한 경영에 대해 공부하고 있어요. 동아리 활동도 활발히 하고 있고, 다양한 사람들과 만나 이야기하는 것을 좋아합니다.',
            'interests': ['금융', '투자', '경제', '컨설팅'],
            'experience': '투자 동아리 운영진, 경제 관련 공모전 입상 경험',
            'conversation_style': 'humor',
            'activity_location': '안암 캠퍼스와 강남 지역에서 활동해요',
            'personalities': ['사교적', '배려심있는', '낙관적'],
            'goal': '금융권 취업과 CFA 자격증 취득을 목표로 하고 있어요',
            'schedule': {
                'Monday': [('11:00', '13:00'), ('16:30', '19:00')],
                'Tuesday': [('09:00', '11:30'), ('14:30', '17:00')],
                'Wednesday': [('12:00', '15:00'), ('18:00', '20:30')],
                'Thursday': [('10:00', '12:30'), ('15:30', '18:30')],
                'Friday': [('13:30', '16:00'), ('19:00', '21:00')],
                'Saturday': [('11:00', '19:00')],
                'Sunday': [('13:00', '18:00')]
            }
        },
        {
            'username': 'choi_minwoo',
            'email': 'choi.minwoo@email.com',
            'nickname': 'AI연구생',
            'age': 23,
            'gender': 'M',
            'grade': '4학년',
            'mbti': 'ISTP',
            'school': '서울대학교',
            'department': '전자공학과',
            'introduction': '전자공학과 4학년 최민우입니다. AI와 머신러닝 분야에 깊은 관심을 가지고 있으며, 특히 컴퓨터 비전과 자연어 처리 기술을 연구하고 있어요. 대학원 진학을 고려하고 있고, 연구 지향적인 개발자가 되고 싶습니다.',
            'interests': ['AI', '머신러닝', '개발', '웹개발'],
            'experience': '연구실 인턴 1년, AI 논문 2편 게재, 오픈소스 프로젝트 기여',
            'conversation_style': 'debate',
            'activity_location': '관악 캠퍼스 연구실에서 주로 시간을 보내요',
            'personalities': ['논리적', '꼼꼼함', '독립적'],
            'goal': '대학원 진학 후 AI 연구자가 되는 것이 목표입니다',
            'schedule': {
                'Monday': [('13:00', '15:30'), ('17:00', '19:30')],
                'Tuesday': [('10:00', '12:00'), ('16:00', '18:00')],
                'Wednesday': [('14:00', '17:00'), ('19:00', '21:00')],
                'Thursday': [('11:00', '14:00'), ('15:30', '17:30')],
                'Friday': [('12:30', '15:00'), ('18:00', '20:00')],
                'Saturday': [('10:30', '17:00')],  # 연구실 시간
                'Sunday': [('14:00', '19:00')]
            }
        },
        {
            'username': 'jung_yuna',
            'email': 'jung.yuna@email.com',
            'nickname': '디자인러버',
            'age': 20,
            'gender': 'F',
            'grade': '1학년',
            'mbti': 'ENFJ',
            'school': '연세대학교',
            'department': '디자인학과',
            'introduction': '디자인학과 1학년 정유나예요! 브랜드 디자인과 마케팅에 관심이 많아서 관련 분야로 진로를 설정하고 있어요. 창의적인 아이디어를 현실로 만드는 과정을 좋아하고, 다양한 사람들과 협업하며 성장하고 싶습니다.',
            'interests': ['디자인', '마케팅', '기획', '창업'],
            'experience': '디자인 공모전 참가, 브랜딩 프로젝트 2회 진행',
            'conversation_style': 'casual',
            'activity_location': '신촌과 홍대 지역에서 주로 활동해요',
            'personalities': ['창의적', '사교적', '리더십있는'],
            'goal': '브랜드 디자이너가 되어 의미있는 브랜드를 만들고 싶어요',
            'schedule': {
                'Monday': [('10:00', '12:30'), ('15:00', '18:00')],
                'Tuesday': [('11:30', '14:00'), ('16:30', '20:00')],
                'Wednesday': [('09:30', '12:00'), ('14:30', '17:30')],
                'Thursday': [('13:00', '16:30'), ('18:30', '21:00')],
                'Friday': [('11:00', '14:30'), ('17:00', '19:30')],
                'Saturday': [('12:00', '18:30')],
                'Sunday': [('10:30', '17:00')]
            }
        },
        {
            'username': 'kang_jiseok',
            'email': 'kang.jiseok@email.com',
            'nickname': '바이오스타터',
            'age': 25,
            'gender': 'M',
            'grade': '4학년',
            'mbti': 'ENTP',
            'school': '성균관대학교',
            'department': '화학과',
            'introduction': '화학과 4학년 강지석입니다. 전공을 살려 화학 연구원의 길도 고민했지만, 요즘은 바이오테크 스타트업에 관심이 생겨서 새로운 도전을 준비하고 있어요. 과학적 사고와 비즈니스를 결합한 일을 해보고 싶습니다.',
            'interests': ['창업', '진로', '투자', '프로젝트관리'],
            'experience': '화학 연구 프로젝트 다수, 바이오테크 스타트업 인턴십',
            'conversation_style': 'deep',
            'activity_location': '성균관대 자연과학캠퍼스와 강남에서 활동해요',
            'personalities': ['분석적', '열정적', '협력적'],
            'goal': '바이오테크 분야에서 창업하거나 관련 기업에 취업하고 싶어요',
            'schedule': {
                'Monday': [('14:30', '17:00'), ('19:00', '21:00')],
                'Tuesday': [('10:30', '13:00'), ('15:00', '18:30')],
                'Wednesday': [('11:00', '14:30'), ('16:00', '19:30')],
                'Thursday': [('09:00', '12:00'), ('17:30', '20:00')],
                'Friday': [('13:00', '16:30'), ('18:00', '20:30')],
                'Saturday': [('11:30', '18:00')],
                'Sunday': [('12:30', '19:00')]
            }
        }
    ]
    
    print("\n👥 완전한 프로필을 가진 사용자 생성 중...")
    
    for user_data in complete_users_data:
        # 사용자 생성 또는 업데이트
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['nickname'],
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ 사용자 생성: {user.username}")
        else:
            # 기존 사용자 정보 업데이트
            user.email = user_data['email']
            user.first_name = user_data['nickname']
            user.save()
            print(f"🔄 사용자 업데이트: {user.username}")
        
        # 프로필 생성 또는 업데이트 (1, 4단계 정보)
        school = schools[user_data['school']]
        department = departments[f"{user_data['school']}-{user_data['department']}"]
        
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'nickname': user_data['nickname'],
                'age': user_data['age'],
                'gender': user_data['gender'],
                'grade': user_data['grade'],
                'mbti': user_data['mbti'],
                'school': school,
                'department': department,
                'introduction': user_data['introduction'],
                'current_step': 'completed',
                'is_active': True
            }
        )
        
        if not created:
            # 기존 프로필 업데이트
            profile.nickname = user_data['nickname']
            profile.age = user_data['age']
            profile.gender = user_data['gender']
            profile.grade = user_data['grade']
            profile.mbti = user_data['mbti']
            profile.school = school
            profile.department = department
            profile.introduction = user_data['introduction']
            profile.current_step = 'completed'
            profile.is_active = True
            profile.save()
            print(f"🔄 프로필 업데이트: {profile.nickname}")
        else:
            print(f"✅ 프로필 생성: {profile.nickname}")
        
        # 관심사 추가 (2단계)
        ProfileInterest.objects.filter(profile=profile).delete()  # 기존 관심사 삭제
        for interest_name in user_data['interests']:
            interest = interests[interest_name]
            ProfileInterest.objects.get_or_create(
                profile=profile,
                interest=interest
            )
        print(f"   🌱 관심사 추가: {', '.join(user_data['interests'])}")
        
        # 추가 정보 생성 또는 업데이트 (5단계)
        additional_info, created = AdditionalInfo.objects.get_or_create(
            profile=profile,
            defaults={
                'experience': user_data['experience'],
                'conversation_style': user_data['conversation_style'],
                'activity_location': user_data['activity_location'],
                'goal_or_concern': user_data['goal']
            }
        )
        
        if not created:
            # 기존 추가 정보 업데이트
            additional_info.experience = user_data['experience']
            additional_info.conversation_style = user_data['conversation_style']
            additional_info.activity_location = user_data['activity_location']
            additional_info.goal_or_concern = user_data['goal']
            additional_info.save()
            print(f"   🔄 추가 정보 업데이트: {additional_info}")
        else:
            print(f"   📝 추가 정보 생성: {additional_info}")
        
        # 성격 키워드 추가
        additional_info.personality_keyword.clear()  # 기존 키워드 삭제
        for personality_name in user_data['personalities']:
            personality = personalities[personality_name]
            additional_info.personality_keyword.add(personality)
        print(f"   🎭 성격 키워드 추가: {', '.join(user_data['personalities'])}")
        
        # 스케줄 정보 생성 (3단계)
        FreeTime.objects.filter(user=user).delete()  # 기존 스케줄 삭제
        for day_name, time_slots in user_data['schedule'].items():
            day_of_week = getattr(DayOfWeek, day_name.upper())
            for start_time_str, end_time_str in time_slots:
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                
                FreeTime.objects.create(
                    user=user,
                    day_of_week=day_of_week,
                    start_time=time(start_hour, start_minute),
                    end_time=time(end_hour, end_minute)
                )
        print(f"   ⏰ 스케줄 추가: 주간 {len(user_data['schedule'])}일 공강시간 설정")
    
    print(f"\n🎉 완료! {len(complete_users_data)}명의 완전한 프로필이 생성되었습니다.")
    print("\n📊 데이터 요약:")
    print(f"   - 학교: {School.objects.count()}개")
    print(f"   - 학과: {Department.objects.count()}개") 
    print(f"   - 관심사: {Interest.objects.count()}개")
    print(f"   - 성격 키워드: {Personality.objects.count()}개")
    print(f"   - 사용자: {User.objects.count()}명")
    print(f"   - 프로필: {Profile.objects.count()}개")
    print(f"   - 추가 정보: {AdditionalInfo.objects.count()}개")
    print(f"   - 공강 시간: {FreeTime.objects.count()}개")

if __name__ == '__main__':
    create_test_data()