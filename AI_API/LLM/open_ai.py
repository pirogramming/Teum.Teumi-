import os
import openai
from openai import OpenAI  # 👈 변경: OpenAI 클라이언트 임포트
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class OpenAIAPIClient:
    """
    OpenAI API를 호출하는 클라이언트 클래스 (버전 1.0.0 이상)
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")

        # 👈 변경: 클라이언트 객체 생성 시 API 키 전달
        self.client = OpenAI(api_key=self.api_key)

    def get_gpt_response(self, prompt, model="gpt-4o", max_tokens=150, temperature=0.7):
        """
        GPT 모델에 프롬프트를 보내고 응답을 받습니다.

        Args:
            prompt (str): GPT에게 전달할 입력 프롬프트.
            model (str): 사용할 OpenAI 모델.
            max_tokens (int): 응답으로 받을 최대 토큰 수.
            temperature (float): 텍스트의 무작위성(창의성)을 조절하는 값.

        Returns:
            str: GPT 모델의 응답 텍스트.
        """
        try:
            # 👈 변경: self.client 객체를 통해 API 호출
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            # 👈 변경: 응답 객체 접근 방식 변경
            return response.choices[0].message.content.strip()

        except openai.APIStatusError as e:
            print(f"OpenAI API 호출 중 오류 발생: {e.status_code}, {e.response}")
            return None
        except openai.APIConnectionError as e:
            print(f"OpenAI API 호출 중 오류 발생: API 서버 연결 실패 - {e}")
            return None
        except Exception as e:
            print(f"OpenAI API 호출 중 예기치 않은 오류가 발생했습니다: {e}")
            return None

if __name__ == "__main__":
    client = OpenAIAPIClient()

    def get_response_with_retry(prompt, retries=3, delay=3):
        for attempt in range(retries):
            response = client.get_gpt_response(prompt)
            if response:
                print("--- GPT 응답 ---")
                print(response)
                return
            else:
                print(f"[재시도] 시도 {attempt + 1}/{retries} 실패... {delay}초 후 재시도합니다.")
                time.sleep(delay)
        print("GPT 응답 실패. 나중에 다시 시도해보세요.")

    import time
    test_prompt = "GPT야, 자기소개 예시 문장을 하나 만들어줘"
    get_response_with_retry(test_prompt)