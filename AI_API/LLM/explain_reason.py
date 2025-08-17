from AI_API.LLM.open_ai import OpenAIAPIClient
from AI_API.LLM.prompt_templates import EXPLANATION_PROMPT
import re

def explain_recommendation_reasons(user, recommended_profiles, n=3):
    """
    AI가 추천한 사용자들을 추천한 이유를 설명하는 함수
    
    Args:
        user: 추천을 받는 사용자
        recommended_profiles: 추천된 프로필 리스트
        n: 추천된 프로필 수 (기본값: 3)
    
    Returns:
        dict: 각 추천 사용자별 추천 이유
    """
    try:
        if not recommended_profiles:
            return {"error": "추천된 프로필이 없습니다."}
        
        # 사용자 프로필 정보 수집
        user_profile = user.profile
        user_summary = _create_user_summary(user_profile)
        
        # 추천된 프로필들의 정보 수집
        candidate_summaries = []
        for i, profile in enumerate(recommended_profiles[:n], 1):
            try:
                summary = _create_candidate_summary(profile, i)
                candidate_summaries.append(summary)
            except Exception as e:
                print(f"후보 {i} 요약 생성 실패: {e}")
                continue
        
        if not candidate_summaries:
            return {"error": "후보 프로필 요약 생성 실패"}
        
        # GPT에게 추천 이유 설명 요청
        prompt = EXPLANATION_PROMPT.format(
            user_summary=user_summary,
            candidates="\n".join(candidate_summaries),
            n=len(candidate_summaries)
        )
        
        client = OpenAIAPIClient()
        gpt_response = client.get_gpt_response(
            prompt, 
            max_tokens=500, 
            temperature=0.7
        )
        
        if not gpt_response:
            return {"error": "GPT 응답 실패"}
        
        # 응답 파싱 및 구조화
        explanations = _parse_explanation_response(gpt_response, recommended_profiles[:n])
        
        return {
            "success": True,
            "explanations": explanations,
            "raw_response": gpt_response
        }
        
    except Exception as e:
        print(f"추천 이유 설명 생성 오류: {e}")
        return {"error": f"추천 이유 설명 생성 오류: {str(e)}"}

def _create_user_summary(profile):
    """사용자 프로필 요약 생성"""
    try:
        additional_info = getattr(profile, 'additional_info', None)
        
        summary = (
            f"사용자 프로필: "
            f"나이: {profile.age or '없음'}, "
            f"성별: {profile.get_gender_display() if profile.gender else '없음'}, "
            f"MBTI: {profile.mbti or '없음'}, "
            f"자기소개: {profile.introduction or '없음'}"
        )
        
        if additional_info:
            personality_keywords = [k.keyword for k in additional_info.personality_keyword.all()]
            if personality_keywords:
                summary += f", 성격키워드: {', '.join(personality_keywords)}"
            
            if additional_info.conversation_style:
                summary += f", 선호대화스타일: {additional_info.conversation_style}"
            
            if additional_info.goal_or_concern:
                summary += f", 목표/걱정: {additional_info.goal_or_concern}"
        
        return summary
        
    except Exception as e:
        print(f"사용자 요약 생성 오류: {e}")
        return "사용자 프로필 정보 오류"

def _create_candidate_summary(profile, index):
    """추천 후보 프로필 요약 생성"""
    try:
        additional_info = getattr(profile, 'additional_info', None)
        
        summary = (
            f"{index}. 후보 프로필: "
            f"닉네임: {profile.nickname or '없음'}, "
            f"나이: {profile.age or '없음'}, "
            f"성별: {profile.get_gender_display() if profile.gender else '없음'}, "
            f"MBTI: {profile.mbti or '없음'}, "
            f"자기소개: {profile.introduction or '없음'}"
        )
        
        if additional_info:
            personality_keywords = [k.keyword for k in additional_info.personality_keyword.all()]
            if personality_keywords:
                summary += f", 성격키워드: {', '.join(personality_keywords)}"
            
            if additional_info.conversation_style:
                summary += f", 대화스타일: {additional_info.conversation_style}"
            
            if additional_info.experience:
                summary += f", 경험: {additional_info.experience}"
        
        return summary
        
    except Exception as e:
        print(f"후보 요약 생성 오류: {e}")
        return f"{index}. 후보 프로필 정보 오류"

def _parse_explanation_response(response, profiles):
    """GPT 응답을 파싱하여 구조화된 추천 이유 반환"""
    try:
        explanations = []
        
        # 각 후보별로 응답에서 해당 부분 추출
        for i, profile in enumerate(profiles, 1):
            # 응답에서 해당 번호의 설명 부분 찾기
            pattern = rf"{i}\.?\s*([^0-9]+?)(?=\d+\.|$)"
            match = re.search(pattern, response, re.DOTALL)
            
            if match:
                reason = match.group(1).strip()
            else:
                reason = "추천 이유를 파싱할 수 없습니다."
            
            explanations.append({
                "profile_id": profile.profile_id,
                "nickname": profile.nickname or "익명",
                "reason": reason
            })
        
        return explanations
        
    except Exception as e:
        print(f"응답 파싱 오류: {e}")
        return [{"error": f"파싱 오류: {str(e)}"}]

def explain_single_recommendation(user, target_profile):
    """
    단일 추천에 대한 이유를 설명하는 함수
    
    Args:
        user: 추천을 받는 사용자
        target_profile: 추천 대상 프로필
    
    Returns:
        str: 추천 이유 설명
    """
    try:
        user_summary = _create_user_summary(user.profile)
        target_summary = _create_candidate_summary(target_profile, 1)
        
        prompt = f"""
사용자 프로필: {user_summary}

추천 대상: {target_summary}

위 사용자에게 이 추천 대상을 추천하는 구체적인 이유를 2-3문장으로 설명해주세요.
성격, 관심사, 대화스타일 등의 호환성을 중심으로 설명하세요.
"""
        
        client = OpenAIAPIClient()
        response = client.get_gpt_response(prompt, max_tokens=200, temperature=0.7)
        
        return response or "추천 이유를 생성할 수 없습니다."
        
    except Exception as e:
        print(f"단일 추천 이유 설명 오류: {e}")
        return f"추천 이유 설명 오류: {str(e)}"
