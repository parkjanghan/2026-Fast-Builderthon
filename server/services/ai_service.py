import os
import asyncio
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage, SystemMessage


class AIService:

    def __init__(self):
        # NVIDIA NIM 연결 설정
        self.llm = ChatNVIDIA(model="meta/llama-3.2-11b-vision-instruct",
                              nvidia_api_key=os.getenv("NVIDIA_API_KEY"))
        self.system_prompt = "너는 질문에 친절하게 대답하는 AI 도우미야."

    # 테스트를 위해 추가한 텍스트 전용 메서드
    async def test_ask(self, question: str):
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=question)
            ])
            return response.content
        except Exception as e:
            return f"❌ 테스트 실패: {str(e)}"

    # 본 프로젝트에서 사용할 이미지 분석 메서드
    async def analyze_frame(self, image_b64: str, local_status: str):
        content = [{
            "type": "text",
            "text": f"현재 로컬 상태: {local_status}"
        }, {
            "type": "image_url",
            "image_url": {
                "url": image_b64
            }
        }]
        response = await self.llm.ainvoke([
            SystemMessage(content="너는 화면 분석 에이전트야. 위험하면 PAUSE라고 답해."),
            HumanMessage(content=content)
        ])
        return response.content


# --- 단독 실행 테스트 블록 ---
if __name__ == "__main__":

    async def run_test():
        print("🔍 [NVIDIA NIM & LangChain] 단독 연결 테스트 시작...")
        service = AIService()

        question = "최고의 포켓몬은?"
        print(f"❓ 질문: {question}")
        print("⌛ NVIDIA NIM 응답 대기 중...")

        # 이제 클래스 내부에 test_ask가 있으므로 에러가 나지 않습니다
        result = await service.test_ask(question)

        print("\n" + "=" * 40)
        print(f"🤖 AI 답변:\n{result}")
        print("=" * 40)

    asyncio.run(run_test())
