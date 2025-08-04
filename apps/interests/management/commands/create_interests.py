# apps/interests/management/commands/create_interests.py

from django.core.management.base import BaseCommand
from apps.interests.models import Interest


class Command(BaseCommand):
    help = "관심사 데이터를 생성합니다."

    def handle(self, *args, **options):
        interests = [
            '창업', '개발', '취업', '진로', 'AI', 'UX/UI', '마케팅', '투자',
            '데이터분석', '디자인', '외국어', '스터디', '프로젝트관리', '경제',
            '금융', '컨설팅', '기획', '영업', '교환학생', '인턴십', '블록체인',
            '게임개발', '모바일앱', '웹개발', '머신러닝', '정보보안', '대학원',
            '공모전', '부트캠프', '동아리'
        ]

        created_count = 0
        for interest_name in interests:
            interest, created = Interest.objects.get_or_create(name=interest_name)
            if created:
                created_count += 1
                self.stdout.write(f"✅ '{interest_name}' 관심사 생성됨")
            else:
                self.stdout.write(f"ℹ️  '{interest_name}' 관심사는 이미 존재함")

        self.stdout.write(
            self.style.SUCCESS(f"🎉 관심사 생성 완료! 새로 생성된 관심사: {created_count}개")
        ) 