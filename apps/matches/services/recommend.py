from django.contrib.auth import get_user_model
from django.db.models import Q
from matches.models import Match
from profiles.models import Profile
from schedules.models import FreeTime
from reviews.models import Review   

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
    matched_users = Match.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values_list('sender_id', 'receiver_id')

    matched_user_ids = set()
    for s_id, r_id in matched_users:
        matched_user_ids.update([s_id, r_id])
    matched_user_ids.discard(user.id)

    # 공강시간 교집합이 있는 사람만 남기기
    user_times = FreeTime.objects.filter(profile=user.profile)
    overlap_profiles = Profile.objects.filter(
        freetime__in=user_times
    ).exclude(user__id__in=matched_user_ids).exclude(user=user).distinct()

    return overlap_profiles

def calculate_match_score(my_profile, other_profile):
    """
    2단계: 점수 계산
    - 관심사, 성격, 대화 목적 등 조건별 가중치 적용
    """
    score = 0

    # 성격 키워드 교집합
    my_keywords = set(my_profile.personality_keywords.values_list('id', flat=True))
    other_keywords = set(other_profile.personality_keywords.values_list('id', flat=True))
    if my_keywords & other_keywords:
        score += 15

    # 관심사 태그 교집합
    my_tags = set(my_profile.interest_tags.values_list('id', flat=True))
    other_tags = set(other_profile.interest_tags.values_list('id', flat=True))
    common_tags = my_tags & other_tags
    score += len(common_tags) * 5  # 태그 하나당 5점

    # 대화 목적
    if my_profile.conversation_purpose == other_profile.conversation_purpose:
        score += 10

    # 대화 스타일
    if my_profile.conversation_style == other_profile.conversation_style:
        score += 7

    # 고민 주제 교집합
    my_worries = set(my_profile.worry_topics.values_list('id', flat=True))
    other_worries = set(other_profile.worry_topics.values_list('id', flat=True))
    if my_worries & other_worries:
        score += 6

    # 진로 희망과 관련 직업 일치
    if my_profile.desired_career and other_profile.related_career:
        if my_profile.desired_career in other_profile.related_career:
            score += 7

    # 주요 커리큘럼 키워드 유사도
    if my_profile.desired_career and other_profile.main_subject:
        if my_profile.desired_career.lower() in other_profile.main_subject.lower():
            score += 5

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
