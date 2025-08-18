from django.contrib.auth import get_user_model
from django.db.models import Q
from apps.matches.models import Matching
from apps.profiles.models import Profile
from apps.schedules.models import FreeTime
from apps.reviews.models import Review 

User = get_user_model()

def filter_candidates(user):
    """
    1단계: 추천 대상 필터링
    - 자기 자신 제외
    - 이미 매칭한 유저 제외
    - 완료된 프로필만 대상으로 선정
    """
    # 본인 제외
    all_profiles = Profile.objects.exclude(user=user)

    # 이미 매칭된 사람 제외
    matched_users = Matching.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values_list('sender_id', 'receiver_id')

    matched_user_ids = set()
    for s_id, r_id in matched_users:
        matched_user_ids.update([s_id, r_id])
    matched_user_ids.discard(user.id)

    # 완료된 프로필만 대상으로 선정
    overlap_profiles = Profile.objects.filter(
        current_step='completed',
        is_active=True
    ).exclude(user__id__in=matched_user_ids).exclude(user=user).distinct()

    return overlap_profiles

def calculate_match_score(my_profile, other_profile):
    """
    2단계: 점수 계산
    - 관심사, 성격, 대화 목적 등 조건별 가중치 적용
    """
    score = 0  # 기본 점수를 0점으로 설정 (백분율 계산을 위해)

    # 성격 키워드 교집합
    try:
        my_additional = getattr(my_profile, 'additional_info', None)
        other_additional = getattr(other_profile, 'additional_info', None)
        if my_additional and other_additional:
            my_keywords = set(my_additional.personality_keyword.values_list('keyword', flat=True))
            other_keywords = set(other_additional.personality_keyword.values_list('keyword', flat=True))
            common_keywords = my_keywords & other_keywords
            score += len(common_keywords) * 5  # 교집합 1개당 5점, 최대 20점
    except Exception as e:
        print(f"성격 키워드 계산 오류: {e}")
        pass

    # 관심사 태그 교집합
    try:
        my_interests = set(my_profile.interests.values_list('interest__name', flat=True))
        other_interests = set(other_profile.interests.values_list('interest__name', flat=True))
        common_interests = my_interests & other_interests
        score += len(common_interests) * 5  # 관심사 하나당 5점, 최대 20점
    except Exception as e:
        print(f"관심사 계산 오류: {e}")
        pass

    # 대화 스타일 일치
    try:
        my_additional = getattr(my_profile, 'additional_info', None)
        other_additional = getattr(other_profile, 'additional_info', None)
        if (my_additional and other_additional and 
            my_additional.conversation_style and other_additional.conversation_style and
            my_additional.conversation_style == other_additional.conversation_style):
            score += 10 
    except Exception as e:
        print(f"대화 스타일 계산 오류: {e}")
        pass

    # 같은 학교 보너스
    if my_profile.school and other_profile.school:
        if my_profile.school.school_id == other_profile.school.school_id:
            score += 15

    # 학년 차이 (1-2학년 차이는 보너스)
    if my_profile.grade and other_profile.grade:
        try:
            my_grade_num = int(my_profile.grade[0])
            other_grade_num = int(other_profile.grade[0])
            grade_diff = abs(my_grade_num - other_grade_num)
            if grade_diff <= 1:
                score += 7
            elif grade_diff <= 2:
                score += 3
        except:
            pass

    # 나이 차이 (3세 이내 보너스)
    if my_profile.age and other_profile.age:
        age_diff = abs(my_profile.age - other_profile.age)
        if age_diff <= 2:
            score += 15
        elif age_diff <= 3:
            score += 10
        elif age_diff <= 5:
            score += 5

    # ============================================================================
    # 학과 관련 점수 계산
    # ============================================================================
    
    # 학과 카테고리 점수 (같은 계열 학과 보너스)
    try:
        if (my_profile.department and other_profile.department and 
            my_profile.department.category and other_profile.department.category):
            
            # 같은 카테고리 (공학, 인문, 예체능 등)
            if my_profile.department.category == other_profile.department.category:
                score += 8
            # 유사한 카테고리 (공학-자연과학, 인문-사회 등)
            elif _is_similar_category(my_profile.department.category, other_profile.department.category):
                score += 4
    except Exception as e:
        print(f"학과 카테고리 점수 계산 오류: {e}")
        pass

    # 학과 위치 점수 (같은 단과대학 보너스)
    try:
        if (my_profile.department and other_profile.department and 
            my_profile.department.college_name and other_profile.department.college_name):
            
            if my_profile.department.college_name == other_profile.department.college_name:
                score += 6
    except Exception as e:
        print(f"학과 위치 점수 계산 오류: {e}")
        pass

    # 학과 학위 유형 점수 (같은 학위 유형 보너스)
    try:
        if (my_profile.department and other_profile.department and 
            my_profile.department.degree_type and other_profile.department.degree_type):
            
            if my_profile.department.degree_type == other_profile.department.degree_type:
                score += 5
    except Exception as e:
        print(f"학과 학위 유형 점수 계산 오류: {e}")
        pass

    # ============================================================================
    # 리뷰 세부 점수 계산
    # ============================================================================
    
    # 리뷰 평점 (기존 로직 개선)
    try:
        review_scores = Review.objects.filter(target=other_profile.user).values_list('rating', flat=True)
        if review_scores:
            avg_rating = sum(review_scores) / len(review_scores)
            # 평점에 따른 세분화된 점수
            if avg_rating >= 4.5:
                score += 8
            elif avg_rating >= 4.0:
                score += 6
            elif avg_rating >= 3.5:
                score += 4
            elif avg_rating >= 3.0:
                score += 2
    except Exception as e:
        print(f"리뷰 평점 계산 오류: {e}")
        pass

    # 리뷰에서 대화태도 점수
    try:
        score += _calculate_conversation_attitude_score(other_profile.user)
    except Exception as e:
        print(f"대화태도 점수 계산 오류: {e}")
        pass

    # 리뷰에서 대화가치 점수
    try:
        score += _calculate_conversation_value_score(other_profile.user)
    except Exception as e:
        print(f"대화가치 점수 계산 오류: {e}")
        pass

    # 재만남 점수
    try:
        re_meeting_score = _calculate_re_meeting_score(other_profile.user)
        score += re_meeting_score
    except Exception as e:
        print(f"재만남 점수 계산 오류: {e}")
        pass

    # 최대 점수 계산 (모든 조건이 만족될 때의 점수)
    max_score = 0
    
    # 성격 키워드 최대 점수 (3개 키워드 × 5점 = 15점)
    max_score += 15
    
    # 관심사 최대 점수 (4개 관심사 × 5점 = 20점)
    max_score += 20
    
    # 대화 스타일 최대 점수
    max_score += 10
    
    # 같은 학교 최대 점수
    max_score += 15
    
    # 학년 차이 최대 점수
    max_score += 7
    
    # 나이 차이 최대 점수
    max_score += 15
    
    # 학과 카테고리 최대 점수
    max_score += 8
    
    # 학과 위치 최대 점수
    max_score += 6
    
    # 학과 학위 유형 최대 점수
    max_score += 5
    
    # 리뷰 평점 최대 점수
    max_score += 8
    
    # 대화태도 최대 점수 (추정)
    max_score += 10
    
    # 대화가치 최대 점수 (추정)
    max_score += 10
    
    # 재만남 최대 점수 (추정)
    max_score += 10
    
    # 최대 점수는 149점
    
    # 백분율 계산: (실제 점수 / 최대 점수) × 100
    if max_score > 0:
        percentage = (score / max_score) * 100
        # 60점 기본점수 + 백분율 점수 (최대 40점)
        final_score = 60 + (percentage * 0.4)  # 0.4는 40점을 100%로 나눈 값
        return min(final_score, 100)
    else:
        return 60  # 최대 점수가 0이면 기본점수만 반환


def _is_similar_category(category1, category2):
    """
    학과 카테고리가 유사한지 판단
    """
    similar_categories = {
        '공학': ['자연과학', 'IT'],
        '자연과학': ['공학', 'IT'],
        'IT': ['공학', '자연과학'],
        '인문': ['사회', '예체능'],
        '사회': ['인문', '예체능'],
        '예체능': ['인문', '사회'],
        '의학': ['자연과학', '공학'],
        '경영': ['사회', '인문']
    }
    
    if category1 in similar_categories:
        return category2 in similar_categories[category1]
    return False


def _calculate_conversation_attitude_score(user):
    """
    대화태도 점수 계산 (리뷰 데이터 기반)
    """
    try:
        from apps.reviews.models import ReviewAttitude, ConversationAttitude
        
        # 해당 사용자에 대한 모든 리뷰 가져오기
        total_reviews = Review.objects.filter(target=user).count()
        if total_reviews == 0:
            return 0
            
        # 대화태도 관련 리뷰 데이터 계산
        # 긍정적인 대화태도 (적극적 참여, 경청, 질문 등)
        positive_attitudes = [
            "적극적으로 참여해주셨어요",
            "경청을 잘해주셨어요", 
            "질문을 많이 해주셨어요",
            "편안한 분위기를 만들어주셨어요",
            "시간을 잘 지켜주셨어요"
        ]
        
        # 긍정적인 대화태도를 가진 리뷰 수 계산
        positive_attitude_reviews = ReviewAttitude.objects.filter(
            review__target=user,
            attitude__content__in=positive_attitudes
        ).count()
        
        if total_reviews > 0:
            # 긍정적인 대화태도 비율에 따른 점수 (0-5점)
            positive_ratio = positive_attitude_reviews / total_reviews
            score = int(positive_ratio * 5)
            return score
        
        return 0
    except Exception as e:
        print(f"대화태도 점수 계산 오류: {e}")
        return 0


def _calculate_conversation_value_score(user):
    """
    대화가치 점수 계산 (리뷰 데이터 기반)
    """
    try:
        from apps.reviews.models import ReviewValue, ConversationValue
        
        # 해당 사용자에 대한 모든 리뷰 가져오기
        total_reviews = Review.objects.filter(target=user).count()
        if total_reviews == 0:
            return 0
            
        # 대화가치 관련 리뷰 데이터 계산
        # 높은 가치를 가진 대화 (새로운 관점, 실용적 조언, 동기부여 등)
        high_value_conversations = [
            "새로운 관점을 얻었어요",
            "실용적인 조언을 받았어요",
            "동기부여가 되었어요",
            "전문적인 지식을 배웠어요"
        ]
        
        # 높은 가치를 가진 대화 리뷰 수 계산
        high_value_reviews = ReviewValue.objects.filter(
            review__target=user,
            value__content__in=high_value_conversations
        ).count()
        
        if total_reviews > 0:
            # 높은 가치 대화 비율에 따른 점수 (0-5점)
            high_value_ratio = high_value_reviews / total_reviews
            score = int(high_value_ratio * 5)
            return score
        
        return 0
    except Exception as e:
        print(f"대화가치 점수 계산 오류: {e}")
        return 0


def _calculate_re_meeting_score(user):
    """
    재만남 점수 계산 (리뷰 데이터 기반)
    """
    try:
        # 재만남 의사가 있는 리뷰의 비율로 점수 계산
        total_reviews = Review.objects.filter(target=user).count()
        if total_reviews == 0:
            return 0
            
        # 재만남 의사가 있는 리뷰 수 (meeting 필드가 1인 경우)
        re_meeting_reviews = Review.objects.filter(target=user, meeting=1).count()
        
        if total_reviews > 0:
            re_meeting_ratio = re_meeting_reviews / total_reviews
            # 재만남 비율에 따른 점수 (0-10점)
            score = int(re_meeting_ratio * 10)
            return score
        
        return 0
    except Exception as e:
        print(f"재만남 점수 계산 오류: {e}")
        return 0


def recommend_top_n(user, n=3):
    """
    3단계: 추천 후보 정렬 및 상위 n명 반환
    """
    try:
        candidates = filter_candidates(user)
        if not candidates.exists():
            print(f"사용자 {user.username}에 대한 추천 후보가 없습니다.")
            return []
            
        scored = []
        for candidate in candidates:
            try:
                score = calculate_match_score(user.profile, candidate)
                scored.append((candidate, score))
            except Exception as e:
                print(f"후보 {candidate.user.username} 점수 계산 오류: {e}")
                continue
                
        scored.sort(key=lambda x: x[1], reverse=True)
        return [candidate for candidate, _ in scored[:n]]
        
    except Exception as e:
        print(f"추천 로직 실행 오류: {e}")
        return []
