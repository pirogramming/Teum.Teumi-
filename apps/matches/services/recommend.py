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
    - 공강시간이 겹치는 유저만 남김
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

    # 공강시간 교집합이 있는 사람만 남기기 (모든 완료된 프로필 반환으로 단순화)
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
    score = 0

    # 성격 키워드 교집합
    try:
        my_additional = getattr(my_profile, 'additional_info', None)
        other_additional = getattr(other_profile, 'additional_info', None)
        if my_additional and other_additional:
            my_keywords = set(my_additional.personality_keyword.values_list('id', flat=True))
            other_keywords = set(other_additional.personality_keyword.values_list('id', flat=True))
            if my_keywords & other_keywords:
                score += 15
    except:
        pass

    # 관심사 태그 교집합
    try:
        my_interests = set(my_profile.interests.values_list('interest_id', flat=True))
        other_interests = set(other_profile.interests.values_list('interest_id', flat=True))
        common_interests = my_interests & other_interests
        score += len(common_interests) * 5  # 관심사 하나당 5점
    except:
        pass

    # 대화 스타일 일치
    try:
        my_additional = getattr(my_profile, 'additional_info', None)
        other_additional = getattr(other_profile, 'additional_info', None)
        if (my_additional and other_additional and 
            my_additional.conversation_style and other_additional.conversation_style and
            my_additional.conversation_style == other_additional.conversation_style):
            score += 10
    except:
        pass

    # 같은 학교 보너스
    if my_profile.school and other_profile.school:
        if my_profile.school == other_profile.school:
            score += 10

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
            score += 10
        elif age_diff <= 3:
            score += 7
        elif age_diff <= 5:
            score += 3

    # 리뷰 평점
    review_scores = Review.objects.filter(target=other_profile.user).values_list('rating', flat=True)
    if review_scores:
        avg_rating = sum(review_scores) / len(review_scores)
        if avg_rating >= 4.0:
            score += 5

    return score

def recommend_top_n(user, n=3):
    """
    3단계: 추천 후보 정렬 및 상위 n명 반환
    """
    candidates = filter_candidates(user)
    scored = []
    for candidate in candidates:
        score = calculate_match_score(user.profile, candidate)
        scored.append((candidate.user, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [user for user, _ in scored[:n]]
