#!/usr/bin/env python
"""
성격 키워드와 관심사 키워드를 Interest 모델에 추가하는 스크립트
Django 쉘에서 실행: python manage.py shell < setup_keywords.py
"""

from apps.interests.models import Interest

# 성격 키워드
personality_keywords = [
    "차분함", "논리적", "센스있는", "분석적", "꼼꼼함", "창의적",
    "사교적", "열정적", "배려심있는", "리더십있는", "유머러스", "진중함",
    "적극적", "신중함", "낙관적", "현실적", "독립적", "협력적"
]

# 관심사 키워드
interest_keywords = [
    "창업", "개발", "취업", "진로", "AI", "UX/UI", "마케팅", "투자", "데이터분석", "디자인",
    "외국어", "스터디", "프로젝트관리", "경제", "금융", "컨설팅", "기획", "영업", "교환학생",
    "인턴십", "블록체인", "게임개발", "모바일앱", "웹개발", "머신러닝"
]

# 모든 키워드를 Interest 모델에 추가
all_keywords = personality_keywords + interest_keywords

print("키워드 추가를 시작합니다...")

created_count = 0
existing_count = 0

for keyword in all_keywords:
    interest, created = Interest.objects.get_or_create(name=keyword)
    if created:
        created_count += 1
        print(f"✓ 새로 추가: {keyword}")
    else:
        existing_count += 1
        print(f"- 이미 존재: {keyword}")

print(f"\n완료! 새로 추가된 키워드: {created_count}개, 기존 키워드: {existing_count}개")
print(f"전체 키워드 수: {Interest.objects.count()}개")