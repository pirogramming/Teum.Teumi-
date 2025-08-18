"""
AI 기반 자기소개 자동 생성 서비스
프로필 단계별 정보를 바탕으로 개인화된 자기소개를 생성합니다.
"""

from typing import Dict, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from AI_API.LLM.open_ai import OpenAIAPIClient
from AI_API.LLM.prompt_templates import (
    PROFILE_INTRODUCTION_PROMPT, 
    ENHANCED_INTRODUCTION_PROMPT,
    CONVERSATION_STARTER_PROMPT
)
from apps.profiles.models import Profile


def generate_step_introduction(profile_data: Dict[str, Any]) -> str:
    """
    프로필 단계에서의 AI 기반 자기소개 생성
    이전 단계들의 정보만을 바탕으로 생성 (50자 이상, 1-2문장)
    
    Args:
        profile_data: 프로필 단계별 데이터
        
    Returns:
        str: 생성된 자기소개
    """
    try:
        # 프로필 단계별 정보 수집
        context = _collect_step_context(profile_data)
        
        # 프롬프트 생성
        prompt = PROFILE_INTRODUCTION_PROMPT.format(**context)
        
        # GPT 호출
        client = OpenAIAPIClient()
        response = client.get_gpt_response(
            prompt, 
            max_tokens=150, 
            temperature=0.7
        )
        
        if response:
            # 응답 정리 및 길이 검증
            cleaned_response = _clean_and_validate_introduction(response)
            return cleaned_response
        else:
            return _generate_fallback_introduction(profile_data)
            
    except Exception as e:
        print(f"단계별 자기소개 생성 오류: {e}")
        return _generate_fallback_introduction(profile_data)


def generate_enhanced_introduction(profile: Any, existing_introduction: str = "") -> str:
    """
    마이페이지에서의 향상된 AI 기반 자기소개 생성
    DB에 저장된 모든 정보를 바탕으로 더 디테일한 자기소개 생성 (50자 이상, 1-2문장)
    
    Args:
        profile: 사용자 프로필 객체
        existing_introduction: 기존 자기소개 (있는 경우)
        
    Returns:
        str: 생성된 향상된 자기소개
    """
    try:
        # 프로필의 모든 정보 수집
        context = _collect_full_profile_context(profile, existing_introduction)
        
        # 향상된 프롬프트 생성
        prompt = ENHANCED_INTRODUCTION_PROMPT.format(**context)
        
        # GPT 호출
        client = OpenAIAPIClient()
        response = client.get_gpt_response(
            prompt, 
            max_tokens=200, 
            temperature=0.8
        )
        
        if response:
            # 응답 정리 및 길이 검증
            cleaned_response = _clean_and_validate_introduction(response)
            return cleaned_response
        else:
            return _generate_fallback_introduction_from_profile(profile)
            
    except Exception as e:
        print(f"향상된 자기소개 생성 오류: {e}")
        return _generate_fallback_introduction_from_profile(profile)


def generate_conversation_topics(user_a_profile, user_b_profile):
    """
    두 사용자 간의 대화주제 3가지를 AI로 추천
    성능 개선: 캐싱 적용
    
    Args:
        user_a_profile: 사용자 A의 프로필
        user_b_profile: 사용자 B의 프로필
    
    Returns:
        dict: 대화주제 목록과 메타데이터
    """
    # 캐시 키 생성 (두 사용자 조합별로 고유)
    cache_key = f"conversation_topics_{user_a_profile.profile_id}_{user_b_profile.profile_id}"
    
    # 캐시에서 결과 확인 (10분 캐시)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"캐시된 대화주제 결과 사용")
        return cached_result
    
    try:
        # 두 사용자의 프로필 요약 생성 (동기 처리로 변경)
        try:
            user_a_summary = _create_profile_summary_for_conversation(user_a_profile)
        except Exception as e:
            print(f"사용자 A 프로필 요약 생성 실패: {e}")
            user_a_summary = "프로필 정보를 불러올 수 없습니다."
        
        try:
            user_b_summary = _create_profile_summary_for_conversation(user_b_profile)
        except Exception as e:
            print(f"사용자 B 프로필 요약 생성 실패: {e}")
            user_b_summary = "프로필 정보를 불러올 수 없습니다."
        
        # OpenAI API 클라이언트 초기화
        client = OpenAIAPIClient()
        
        # 프롬프트에 사용자 정보 삽입
        prompt = CONVERSATION_STARTER_PROMPT.format(
            user_a_summary=user_a_summary,
            user_b_summary=user_b_summary
        )
        
        # AI 응답 생성
        response = client.get_gpt_response(
            prompt=prompt,
            max_tokens=300,
            temperature=0.7
        )
        
        if response and response.strip():
            # 응답에서 대화주제 추출
            topics_with_messages = _parse_conversation_topics(response)
            
            result = {
                'success': True,
                'topics': [t['topic'] for t in topics_with_messages],
                'messages': [t['message'] for t in topics_with_messages],
                'raw_response': response,
                'user_a_summary': user_a_summary,
                'user_b_summary': user_b_summary
            }
        else:
            result = {
                'success': False,
                'error': 'AI 응답이 비어있습니다.',
                'topics': _generate_fallback_conversation_topics_with_messages(user_a_profile, user_b_profile)
            }
        
        # 결과 캐싱 (10분)
        cache.set(cache_key, result, 600)
        return result
            
    except Exception as e:
        print(f"대화주제 생성 오류: {e}")
        result = {
            'success': False,
            'error': str(e),
            'topics': _generate_fallback_conversation_topics_with_messages(user_a_profile, user_b_profile)
        }
        cache.set(cache_key, result, 600)  # 10분 캐시
        return result


def _collect_step_context(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """프로필 단계별 컨텍스트 정보 수집"""
    context = {
        'school_name': '없음',
        'department_name': '없음',
        'grade': '없음',
        'age': '없음',
        'interests': '없음',
        'mbti': '없음',
        'gender': '없음',
        'conversation_style': '없음',
        'personality_keywords': '없음',
        'experience': '없음',
        'goal_or_concern': '없음'
    }
    
    # 학교/학과 정보
    if profile_data.get('school'):
        context['school_name'] = profile_data['school']
    if profile_data.get('department'):
        context['department_name'] = profile_data['department']
    
    # 기본 정보
    if profile_data.get('grade'):
        context['grade'] = profile_data['grade']
    if profile_data.get('age'):
        context['age'] = profile_data['age']
    if profile_data.get('mbti'):
        context['mbti'] = profile_data['mbti']
    if profile_data.get('gender'):
        context['gender'] = profile_data['gender']
    
    # 관심사
    if profile_data.get('interests'):
        interests = profile_data['interests']
        if isinstance(interests, list):
            context['interests'] = ', '.join(interests[:3])  # 최대 3개
        else:
            context['interests'] = str(interests)
    
    # 추가 정보
    if profile_data.get('conversation_style'):
        context['conversation_style'] = profile_data['conversation_style']
    if profile_data.get('personality_keywords'):
        keywords = profile_data['personality_keywords']
        if isinstance(keywords, list):
            context['personality_keywords'] = ', '.join(keywords[:3])
        else:
            context['personality_keywords'] = str(keywords)
    if profile_data.get('experience'):
        context['experience'] = profile_data['experience']
    if profile_data.get('goal_or_concern'):
        context['goal_or_concern'] = profile_data['goal_or_concern']
    
    return context


def _collect_full_profile_context(profile: Any, existing_introduction: str) -> Dict[str, Any]:
    """프로필의 모든 정보를 수집하여 컨텍스트 생성"""
    try:
        # 기본 정보
        context = {
            'nickname': profile.nickname or '없음',
            'age': profile.age or '없음',
            'gender': profile.get_gender_display() if profile.gender else '없음',
            'grade': profile.grade or '없음',
            'mbti': profile.mbti or '없음',
            'school_name': profile.school.school_name if profile.school else '없음',
            'department_name': profile.department.department_name if profile.department else '없음',
            'existing_introduction': existing_introduction or '없음'
        }
        
        # 관심사 정보
        try:
            interests = profile.interests.all()
            context['interests'] = ', '.join([i.interest.name for i in interests[:4]])
        except:
            context['interests'] = '없음'
        
        # 추가 정보
        try:
            additional_info = profile.additional_info
            if additional_info:
                context['conversation_style'] = additional_info.conversation_style or '없음'
                context['experience'] = additional_info.experience or '없음'
                context['activity_location'] = additional_info.activity_location or '없음'
                context['goal_or_concern'] = additional_info.goal_or_concern or '없음'
                
                # 성격 키워드
                personality_keywords = additional_info.personality_keyword.all()
                if personality_keywords:
                    context['personality_keywords'] = ', '.join([k.keyword for k in personality_keywords[:3]])
                else:
                    context['personality_keywords'] = '없음'
            else:
                context.update({
                    'conversation_style': '없음',
                    'experience': '없음',
                    'activity_location': '없음',
                    'goal_or_concern': '없음',
                    'personality_keywords': '없음'
                })
        except:
            context.update({
                'conversation_style': '없음',
                'experience': '없음',
                'activity_location': '없음',
                'goal_or_concern': '없음',
                'personality_keywords': '없음'
            })
        
        return context
        
    except Exception as e:
        print(f"프로필 컨텍스트 수집 오류: {e}")
        return {
            'nickname': '사용자',
            'age': '없음',
            'gender': '없음',
            'grade': '없음',
            'mbti': '없음',
            'school_name': '없음',
            'department_name': '없음',
            'interests': '없음',
            'conversation_style': '없음',
            'experience': '없음',
            'activity_location': '없음',
            'goal_or_concern': '없음',
            'personality_keywords': '없음',
            'existing_introduction': existing_introduction or '없음'
        }


def _create_profile_summary_for_conversation(profile):
    """
    대화주제 추천을 위한 프로필 요약 생성
    """
    try:
        summary_parts = []
        
        # 기본 정보
        if profile.nickname:
            summary_parts.append(f"닉네임: {profile.nickname}")
        if profile.age:
            summary_parts.append(f"나이: {profile.age}세")
        if profile.grade:
            summary_parts.append(f"학년: {profile.grade}")
        if profile.gender:
            summary_parts.append(f"성별: {profile.gender}")
        
        # 학교/학과 정보
        if profile.school:
            summary_parts.append(f"학교: {profile.school.school_name}")
        if profile.department:
            summary_parts.append(f"학과: {profile.department.department_name}")
        
        # 관심사
        try:
            interests = profile.interests.values_list('interest__name', flat=True)
            if interests:
                summary_parts.append(f"관심사: {', '.join(interests)}")
        except:
            pass
        
        # 성격 키워드
        try:
            additional_info = getattr(profile, 'additional_info', None)
            if additional_info and additional_info.personality_keyword.exists():
                keywords = additional_info.personality_keyword.values_list('keyword', flat=True)
                summary_parts.append(f"성격: {', '.join(keywords)}")
        except:
            pass
        
        # 대화 스타일
        try:
            additional_info = getattr(profile, 'additional_info', None)
            if additional_info and additional_info.conversation_style:
                summary_parts.append(f"대화 스타일: {additional_info.conversation_style}")
        except:
            pass
        
        # 자기소개
        if profile.introduction:
            summary_parts.append(f"자기소개: {profile.introduction}")
        
        return '\n'.join(summary_parts) if summary_parts else "프로필 정보 부족"
        
    except Exception as e:
        print(f"프로필 요약 생성 오류: {e}")
        return "프로필 정보를 불러올 수 없습니다."


def _parse_conversation_topics(response):
    """
    AI 응답에서 대화주제 3개와 메시지 예시를 추출
    """
    try:
        lines = response.strip().split('\n')
        topics_with_messages = []
        current_topic = None
        current_message = None
        
        for line in lines:
            line = line.strip()
            
            # 주제 줄 확인 (1., 2., 3.으로 시작)
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                # 이전 주제와 메시지가 있으면 저장
                if current_topic and current_message:
                    topics_with_messages.append({
                        'topic': current_topic,
                        'message': current_message
                    })
                
                # 새 주제 추출
                current_topic = line.split('.', 1)[1].strip() if '.' in line else line
                current_message = None
                
            # 예시 메시지 줄 확인
            elif line and '예시 메시지:' in line:
                current_message = line.split('예시 메시지:', 1)[1].strip()
                if current_message.startswith('"') and current_message.endswith('"'):
                    current_message = current_message[1:-1]  # 따옴표 제거
        
        # 마지막 주제와 메시지 저장
        if current_topic and current_message:
            topics_with_messages.append({
                'topic': current_topic,
                'message': current_message
            })
        
        # 3개가 안 되면 기본 주제로 보완
        while len(topics_with_messages) < 3:
            fallback_topics = _generate_fallback_conversation_topics_with_messages(None, None)
            topics_with_messages.append({
                'topic': fallback_topics[len(topics_with_messages)],
                'message': f"안녕하세요! {fallback_topics[len(topics_with_messages)]}에 대해 이야기해보고 싶어요."
            })
        
        return topics_with_messages[:3]  # 최대 3개만 반환
        
    except Exception as e:
        print(f"대화주제 파싱 오류: {e}")
        return _generate_fallback_conversation_topics_with_messages(None, None)


def _generate_fallback_conversation_topics_with_messages(user_a_profile, user_b_profile):
    """
    AI 생성 실패 시 기본 대화주제와 메시지 예시 제공
    """
    basic_topics_with_messages = [
        {
            'topic': '대학 생활과 전공에 대한 이야기',
            'message': '안녕하세요! 전공 공부는 어떻게 되고 계신가요? 대학 생활하면서 재미있는 경험이 있으셨나요?'
        },
        {
            'topic': '취미와 관심사 공유하기',
            'message': '평소에 어떤 취미나 관심사가 있으신지 궁금해요! 저도 비슷한 관심사가 있을 것 같은데요.'
        },
        {
            'topic': '미래 계획과 꿈에 대해 이야기하기',
            'message': '앞으로 어떤 꿈을 가지고 계신지, 어떤 방향으로 나아가고 싶으신지 이야기해보고 싶어요!'
        }
    ]
    
    # 프로필 정보가 있으면 조금 더 구체적으로
    if user_a_profile and user_b_profile:
        try:
            # 학교가 같으면 학교 관련 주제 추가
            if (user_a_profile.school and user_b_profile.school and 
                user_a_profile.school.school_id == user_b_profile.school.school_id):
                basic_topics_with_messages[0] = {
                    'topic': f"{user_a_profile.school.school_name} 캠퍼스 생활 이야기",
                    'message': f'안녕하세요! {user_a_profile.school.school_name}에서 어떤 과목을 수강하고 계신가요? 캠퍼스에서 재미있는 일이 있었나요?'
                }
            
            # 관심사가 있으면 관련 주제 추가
            try:
                a_interests = set(user_a_profile.interests.values_list('interest__name', flat=True))
                b_interests = set(user_b_profile.interests.values_list('interest__name', flat=True))
                common_interests = a_interests & b_interests
                if common_interests:
                    interest_list = list(common_interests)[:2]
                    basic_topics_with_messages[1] = {
                        'topic': f"{', '.join(interest_list)}에 대한 이야기",
                        'message': f'저도 {", ".join(interest_list)}에 관심이 많아요! 어떤 부분이 가장 재미있으신가요?'
                    }
            except:
                pass
                
        except Exception as e:
            print(f"기본 주제 생성 오류: {e}")
    
    return basic_topics_with_messages


def _clean_and_validate_introduction(text: str) -> str:
    """자기소개 텍스트 정리 및 길이 검증"""
    if not text:
        return "열정적이고 적극적인 대학생입니다."
    
    # 불필요한 문자 제거
    cleaned = text.strip()
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
    cleaned = ' '.join(cleaned.split())  # 연속된 공백 제거
    
    # 길이 검증 (50자 이상)
    if len(cleaned) < 50:
        cleaned = cleaned + " 다양한 경험을 통해 성장하고 싶습니다."
    
    # 문장 수 제한 (1-2문장)
    sentences = cleaned.split('.')
    if len(sentences) > 2:
        cleaned = '. '.join(sentences[:2]) + '.'
    
    return cleaned


def _generate_fallback_introduction(profile_data: Dict[str, Any]) -> str:
    """기본 자기소개 생성 (AI 실패 시)"""
    parts = []
    
    if profile_data.get('school'):
        parts.append(f"{profile_data['school']}에 재학 중인")
    
    if profile_data.get('grade'):
        parts.append(f"{profile_data['grade']}학년")
    
    if profile_data.get('age'):
        parts.append(f"{profile_data['age']}세")
    
    if profile_data.get('mbti'):
        parts.append(f"{profile_data['mbti']} 성향의")
    
    if profile_data.get('interests'):
        interests = profile_data['interests']
        if isinstance(interests, list) and interests:
            parts.append(f"{interests[0]}에 관심이 많은")
    
    if not parts:
        parts.append("열정적인")
    
    parts.append("대학생입니다. 새로운 경험과 도전을 통해 성장하고 싶습니다.")
    
    return ' '.join(parts)


def _generate_fallback_introduction_from_profile(profile: Any) -> str:
    """프로필 객체로부터 기본 자기소개 생성 (AI 실패 시)"""
    try:
        parts = []
        
        if profile.school:
            parts.append(f"{profile.school.school_name}에 재학 중인")
        
        if profile.grade:
            parts.append(f"{profile.grade}학년")
        
        if profile.age:
            parts.append(f"{profile.age}세")
        
        if profile.mbti:
            parts.append(f"{profile.mbti} 성향의")
        
        if profile.nickname:
            parts.append(f"{profile.nickname}입니다")
        else:
            parts.append("대학생입니다")
        
        if not parts:
            parts.append("열정적인 대학생입니다")
        
        parts.append("새로운 경험과 도전을 통해 성장하고 싶습니다.")
        
        return ' '.join(parts)
        
    except Exception as e:
        print(f"기본 자기소개 생성 오류: {e}")
        return "열정적이고 적극적인 대학생입니다. 다양한 경험을 통해 성장하고 싶습니다."


def analyze_introduction_quality(introduction: str) -> Dict[str, Any]:
    """
    자기소개 품질 분석
    
    Returns:
        Dict: 품질 점수 및 피드백
    """
    try:
        quality_score = 0
        feedback = []
        
        # 길이 점수 (50자 이상: 30점, 100자 이상: 40점)
        if len(introduction) >= 100:
            quality_score += 40
        elif len(introduction) >= 50:
            quality_score += 30
        else:
            feedback.append("자기소개가 너무 짧습니다. 50자 이상 작성해주세요.")
        
        # 문장 수 점수 (1-2문장: 30점, 3문장: 20점)
        sentences = [s.strip() for s in introduction.split('.') if s.strip()]
        if 1 <= len(sentences) <= 2:
            quality_score += 30
        elif len(sentences) == 3:
            quality_score += 20
        else:
            feedback.append("자기소개는 1-2문장으로 작성하는 것이 좋습니다.")
        
        # 개인정보 포함 점수 (20점)
        personal_keywords = ['재학', '학년', '나이', '성향', '관심', '목표', '경험']
        if any(keyword in introduction for keyword in personal_keywords):
            quality_score += 20
        else:
            feedback.append("개인적인 정보를 포함하면 더 좋은 자기소개가 됩니다.")
        
        # 전반적인 품질 평가
        if quality_score >= 80:
            overall_quality = "매우 좋음"
        elif quality_score >= 60:
            overall_quality = "좋음"
        elif quality_score >= 40:
            overall_quality = "보통"
        else:
            overall_quality = "개선 필요"
        
        return {
            'score': quality_score,
            'overall_quality': overall_quality,
            'feedback': feedback,
            'length': len(introduction),
            'sentence_count': len(sentences)
        }
        
    except Exception as e:
        print(f"자기소개 품질 분석 오류: {e}")
        return {
            'score': 0,
            'overall_quality': '분석 실패',
            'feedback': ['품질 분석 중 오류가 발생했습니다.'],
            'length': len(introduction) if introduction else 0,
            'sentence_count': 0
        }
