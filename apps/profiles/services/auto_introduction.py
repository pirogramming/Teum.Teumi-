"""
AI 기반 자기소개 자동 생성 서비스
프로필 단계별 정보를 바탕으로 개인화된 자기소개를 생성합니다.
"""

from typing import Dict, Any, Optional
from AI_API.LLM.open_ai import OpenAIAPIClient
from AI_API.LLM.prompt_templates import PROFILE_INTRODUCTION_PROMPT, ENHANCED_INTRODUCTION_PROMPT


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
