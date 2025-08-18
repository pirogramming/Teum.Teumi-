import re
import requests
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from apps.matches.services.recommend import recommend_top_n
from AI_API.LLM.open_ai import OpenAIAPIClient
from AI_API.LLM.prompt_templates import RECOMMENDATION_PROMPT


def get_review_summary_from_api(user_id):
    """
    리뷰 API에서 사용자의 리뷰 요약 정보를 가져옵니다.
    """
    try:
        response = requests.get(f"http://localhost:8000/reviews/summary/{user_id}/")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"리뷰 정보 요청 실패: {e}")
    return {}

def get_user_profile_summary(user, profile):
    """
    사용자와 프로필 정보를 요약하여 반환합니다.
    """
    try:
        # 학교/학과 정보
        school_name = profile.school.school_name if profile.school else "없음"
        department_name = profile.department.department_name if profile.department else "없음"
        department_main_subject = profile.department.main_subject if profile.department else "없음"
        department_related_career = profile.department.related_career if profile.department else "없음"

        # 관심사 정보 - 수정된 부분
        interests = []
        try:
            # ProfileInterest 모델을 통해 관심사 가져오기
            from apps.profiles.models import ProfileInterest
            profile_interests = ProfileInterest.objects.filter(profile=profile).select_related('interest')
            interests = [pi.interest.name for pi in profile_interests]
        except Exception as e:
            print(f"관심사 정보 가져오기 오류: {e}")
            interests = ["없음"]

        # 프로필 5단계 정보
        additional_info = getattr(profile, 'additional_info', None)
        personality_keywords = []
        conversation_style = "없음"
        experience = "없음"
        goal_or_concern = "없음"
        
        if additional_info:
            personality_keywords = [k.keyword for k in additional_info.personality_keyword.all()]
            conversation_style = additional_info.conversation_style or "없음"
            experience = additional_info.experience or "없음"
            goal_or_concern = additional_info.goal_or_concern or "없음"

        # 리뷰 정보
        review= getattr(user, 'received_reviews', None)
        review_comments = review.values_list('comment', flat=True) if review else []
        review_summary = get_review_summary_from_api(user.id)
        avg_rating = review_summary.get('average_rating', '없음')
        meeting_score = review_summary.get('meeting_score', '없음')

        summary = (
            f"닉네임: {profile.nickname or '없음'}, "
            f"나이: {profile.age or '없음'}, "
            f"성별: {profile.get_gender_display() if profile.gender else '없음'}, "
            f"학년: {profile.grade or '없음'}, "
            f"MBTI: {profile.mbti or '없음'}, "
            f"자기소개: {profile.introduction or '없음'}, "
            f"학교: {school_name}, "
            f"학과: {department_name}, "
            f"주요과목: {department_main_subject}, "
            f"관련직업: {department_related_career}, "
            f"관심사: {', '.join(interests) if interests else '없음'}, "
            f"성격키워드: {', '.join(personality_keywords) if personality_keywords else '없음'}, "
            f"대화스타일: {conversation_style}, "
            f"경험: {experience}, "
            f"목표/걱정: {goal_or_concern}, "
            f"평균리뷰평점: {avg_rating}, "
            f"리뷰: {', '.join(review_comments) if review_comments else '없음'}, "
            f"재만남점수: {meeting_score}%"
        )
        
        return summary
        
    except Exception as e:
        print(f"프로필 요약 생성 오류: {e}")
        return f"프로필 정보 오류: {e}"

def recommend_top_n_with_ai(user, n=3):
    """
    룰 기반 점수로 상위 10명을 선별한 뒤,
    해당 후보군을 GPT에게 전달해 최종 추천 유저 n(기본값=3)명을 선택하는 함수.
    성능 개선: 캐싱 및 비동기 처리 적용
    """
    # 캐시 키 생성 (사용자별로 고유)
    cache_key = f"ai_recommendations_{user.id}_{n}"
    
    # 캐시에서 결과 확인 (5분 캐시)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"캐시된 AI 추천 결과 사용: {len(cached_result)}명")
        return cached_result
    
    try:
        # 1단계: 룰 기반으로 상위 10명 선별 (최소 3명 이상일 때만 AI 사용)
        initial_candidates = recommend_top_n(user, n=10)
        
        if not initial_candidates:
            print("초기 후보가 없습니다.")
            return []
        
        if len(initial_candidates) < 3:
            print(f"후보가 {len(initial_candidates)}명으로 부족합니다. 룰 기반 결과 반환")
            return initial_candidates[:n]

        print(f"초기 후보 {len(initial_candidates)}명 선별 완료")

        # 2단계: 각 후보의 프로필 요약 생성 (동기 처리로 변경)
        summaries = []
        
        for i, candidate in enumerate(initial_candidates, 1):
            try:
                summary = get_user_profile_summary(candidate.user, candidate)
                if summary:
                    summaries.append(f"{i}. {summary}")
            except Exception as e:
                print(f"후보 {candidate.profile_id} 요약 생성 실패: {e}")
                continue

        if not summaries:
            print("프로필 요약 생성 실패")
            result = initial_candidates[:n]
            cache.set(cache_key, result, 300)  # 5분 캐시
            return result

        # 3단계: GPT에게 추천 요청 (비동기)
        prompt = RECOMMENDATION_PROMPT.format(
            n=n, 
            summaries="\n".join(summaries)
        )

        client = OpenAIAPIClient()
        gpt_response = client.get_gpt_response(prompt, max_tokens=200, temperature=0.3)

        if not gpt_response:
            print("GPT 응답 실패, 룰 기반 결과 반환")
            result = initial_candidates[:n]
            cache.set(cache_key, result, 300)  # 5분 캐시
            return result

        # 4단계: GPT 응답에서 선택된 인덱스 추출
        numbers = re.findall(r'\d+', gpt_response)
        selected_indices = set()
        
        for num in numbers:
            try:
                idx = int(num)
                if 1 <= idx <= len(initial_candidates):
                    selected_indices.add(idx)
            except ValueError:
                continue

        # 5단계: 선택된 후보 반환
        if selected_indices:
            selected_candidates = [initial_candidates[i-1] for i in selected_indices if 1 <= i <= len(initial_candidates)]
            result = selected_candidates[:n]
        else:
            print("GPT 응답에서 유효한 인덱스를 찾을 수 없음, 룰 기반 결과 반환")
            result = initial_candidates[:n]
        
        # 결과 캐싱 (5분)
        cache.set(cache_key, result, 300)
        return result

    except Exception as e:
        print(f"AI 추천 로직 실행 오류: {e}")
        # 오류 발생 시 룰 기반 결과 반환
        try:
            result = recommend_top_n(user, n)
            cache.set(cache_key, result, 300)  # 5분 캐시
            return result
        except:
            return []

