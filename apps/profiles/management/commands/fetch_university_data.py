# apps/profiles/management/commands/fetch_university_data.py

import requests
import os
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from apps.profiles.models import School, Department


class Command(BaseCommand):
    help = "외부 API로부터 학교 및 학과 정보를 수집해 DB에 저장합니다."

    def handle(self, *args, **options):
        load_dotenv()
        api_key = os.getenv('PUBLIC_DATA_API_KEY')
        # 우선은 경기도 지역의 기존 학사 과정 데이터를 수집
        base_url = (
            "http://api.data.go.kr/openapi/tn_pubr_public_univ_major_api"
            f"?serviceKey={api_key}"
            "&numOfRows=100"
            "&type=JSON"
            "&SCSBJT_STTS_NM=기존"
            "&CTPV_NM=서울특별시"
            "&DEG_CRSE_CRS_NM=학사"
            "&SCHL_SE_NM=대학교"
        )

        # 첫번째 페이지 요청으로 전체 데이터 수를 확인합니다.
        response = requests.get(f"{base_url}&pageNo=1")
        if response.status_code != 200:
            self.stderr.write("❌ API 요청 실패")
            return

        json_data = response.json()
        body = json_data.get('response', {}).get('body', {})
        items = body.get('items', [])
        total_count = int(body.get('totalCount', 0))
        num_of_rows = int(body.get('numOfRows', 100))
        last_page = (total_count - 1) // num_of_rows + 1

        total_saved = 0
        
        # 전체 데이터수를 토대로 각 페이지를 순회하며 데이터를 수집합니다.
        for page in range(1, last_page + 1):
            page_url = f"{base_url}&pageNo={page}"
            response = requests.get(page_url)
            if response.status_code != 200:
                self.stderr.write(f"❌ API 요청 실패 (page {page})")
                continue

            data = response.json().get('response', {}).get('body', {}).get('items', [])
            if not data:
                break

            for item in data:
                school, _ = School.objects.get_or_create(
                    school_name=item['schlNm'],
                    defaults={
                        'school_code': item['insttCode'],
                        'location': item['ctpvNm'],
                        'school_type': item['schlSeNm'],
                    }
                )

                Department.objects.update_or_create(
                    school=school,
                    department_name=item['scsbjtNm'],
                    defaults={
                        'major_code': item.get('scsbjtCdNm'),
                        'degree_type': item.get('degCrseCrsNm'),
                        'category': item.get('univOneslfAfilNm'),
                        'college_name': item.get('collegeNm'),
                        'main_subject': item.get('mainSubjNm', ''),
                        'related_career': item.get('relatCrNm', ''),
                    }
                )
                total_saved += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {page}페이지 처리 완료, 누적 {total_saved}개 저장됨"))

        self.stdout.write(self.style.SUCCESS("🎉 전체 데이터 수집 및 저장 완료"))