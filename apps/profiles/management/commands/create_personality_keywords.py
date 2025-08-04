# apps/profiles/management/commands/create_personality_keywords.py

from django.core.management.base import BaseCommand
from apps.profiles.models import Personality


class Command(BaseCommand):
    help = "성격 키워드를 데이터베이스에 추가합니다."

    def handle(self, *args, **options):
        personality_keywords = [
            '논리적', '차분함', '분석적', '센스있는', '리더십있는', '적극적',
            '창의적', '책임감', '열정적', '친근함', '신중함', '도전적',
            '협력적', '독립적', '긍정적', '체계적', '유머러스', '배려심',
            '성실함', '호기심', '인내심', '낙관적', '현실적', '이상주의적'
        ]

        created_count = 0
        for keyword in personality_keywords:
            personality, created = Personality.objects.get_or_create(keyword=keyword)
            if created:
                created_count += 1
                self.stdout.write(f"✅ '{keyword}' 키워드 생성됨")
            else:
                self.stdout.write(f"ℹ️  '{keyword}' 키워드는 이미 존재함")

        self.stdout.write(
            self.style.SUCCESS(f"🎉 성격 키워드 추가 완료! 새로 생성된 키워드: {created_count}개")
        ) 