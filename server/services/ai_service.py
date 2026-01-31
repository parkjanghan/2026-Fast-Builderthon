import os
import json
import asyncio
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage, SystemMessage


class AIService:

    def __init__(self):
        # NVIDIA NIM 연결 설정 (Secrets에 등록된 API Key 사용)
        self.llm = ChatNVIDIA(model="meta/llama-3.2-11b-vision-instruct",
                              nvidia_api_key=os.getenv("NVIDIA_API_KEY"))

        # 시각장애인 수강생을 위한 전용 페르소나 및 출력 규격 정의
        self.system_prompt = """
        너는 시각장애인 수강생을 위해 강의 영상 속 강사의 동작을 분석하고 에디터를 제어하는 AI 에이전트야.
        강의 화면(이미지)을 분석하여 수강생이 따라해야 할 동작을 판단하고, 반드시 아래 JSON 형식으로만 응답해.

        [명령어 타입 가이드]
        - focus_window: 창 전환이 필요할 때 (예: 브라우저에서 VS Code로)
        - hotkey: 단축키 실행 (예: ['ctrl', 's'], ['ctrl', 'g'])
        - type_text: 코드나 텍스트 입력
        - goto_line: 특정 라인으로 이동
        - save_file: 파일 저장

        [응답 형식]
        {
          "type": "명령어타입",
          "payload": { "해당 스키마의 필드" },
          "guidance": "스크린리더가 읽어줄 친절한 설명",
          "should_pause": true/false
        }
        """

    async def analyze_and_decide(self, image_b64: str, local_status: str):
        """
        NVIDIA NIM을 통해 화면을 분석하고 구조화된 의사결정 데이터를 반환합니다.
        """
        content = [{
            "type": "text",
            "text": f"현재 로컬 상태: {local_status}. 화면 분석 후 필요한 명령을 내려줘."
        }, {
            "type": "image_url",
            "image_url": {
                "url": image_b64
            }
        }]

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=content)
            ])

            # AI 응답에서 JSON 추출 및 파싱
            result = json.loads(response.content)
            return result
        except Exception as e:
            print(f"❌ AI 분석 실패: {str(e)}")
            return {
                "type": "type_text",
                "payload": {},
                "guidance": "화면을 분석하는 중 오류가 발생했습니다.",
                "should_pause": True
            }

    async def test_ask(self, question: str):
        """연결 확인용 테스트 메서드"""
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="너는 친절한 도우미야."),
                HumanMessage(content=question)
            ])
            return response.content
        except Exception as e:
            return f"❌ 테스트 실패: {str(e)}"


if __name__ == "__main__":

    async def run_test():
        service = AIService()
        print("🔍 NVIDIA NIM 연결 테스트 시작...")
        res = await service.test_ask("Hello, NIM!")
        print(f"🤖 응답: {res}")

    asyncio.run(run_test())
