import os
import re
import json
import asyncio
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage, SystemMessage


# ============================================================================
# 📦 AI 응답 검증용 Pydantic 모델 (local-program EditorCommand와 1:1 대응)
# ============================================================================

VALID_TYPES = Literal[
    "focus_window",
    "hotkey",
    "type_text",
    "command_palette",
    "open_file",
    "goto_line",
    "open_folder",
    "save_file",
]


class AIDecision(BaseModel):
    """AI가 반환해야 하는 구조화된 의사결정"""

    type: VALID_TYPES
    payload: dict
    guidance: str = ""
    should_pause: bool = False
    target_file: Optional[str] = None  # 편집 대상 파일명 (로컬이 올바른 파일에서 작업하도록)
    expected_content: Optional[str] = None  # 화면에 보이는 현재 파일 내용 (로컬 파일 검증용)


# ============================================================================
# 🧠 AI Service
# ============================================================================


class AIService:
    MAX_RETRIES = 1  # 검증 실패 시 재시도 횟수

    def __init__(self):
        # ----------------------------------------------------------------
        # 🤖 모델 선택 (OCR 벤치마크 기준 순위)
        # ----------------------------------------------------------------
        # 1순위: Llama 4 Maverick — OCR 82.3%, DocVQA 94.4%, 1M 컨텍스트
        model_id = "meta/llama-4-maverick-17b-128e-instruct"
        # 2순위: Nemotron Nano VL — OCRBench v2 1위(92.3%), 128K 컨텍스트
        # model_id = "nvidia/nemotron-nano-12b-v2-vl"
        # 3순위: Llama 4 Scout — OCR 74.3%, 10M 컨텍스트, 더 빠름
        # model_id = "meta/llama-4-scout-17b-16e-instruct"
        # ----------------------------------------------------------------
        self.llm = ChatNVIDIA(
            model=model_id,
            nvidia_api_key=os.getenv("NVIDIA_API_KEY"),
            temperature=0.15,
        )

        # local-program/models/commands.py EditorCommand 스키마와 정확히 일치하는 프롬프트
        self.system_prompt = """너는 시각장애인 수강생을 위해 강의 영상 속 강사의 동작을 분석하고 에디터를 제어하는 AI 에이전트야.
강의 화면(이미지)과 자막(transcript)을 분석하여 수강생이 따라해야 할 동작을 판단하고, 반드시 아래 JSON 형식으로만 응답해.
JSON 외의 텍스트(설명, 마크다운 등)는 절대 포함하지 마.

[명령어 타입 + payload 스키마]

1. focus_window — 창 전환
   payload: { "window_title": "Visual Studio Code" }

2. hotkey — 단축키 실행
   payload: { "keys": ["ctrl", "s"] }

3. type_text — 코드/텍스트 입력
   payload: { "content": "print('hello')" }

4. command_palette — VS Code 명령 팔레트
   payload: { "command": "Go to Line" }

5. open_file — 파일 열기
   payload: { "file_path": "C:/project/main.py" }

6. goto_line — 특정 라인으로 이동
   payload: { "line_number": 42 }
   (선택) payload: { "line_number": 42, "column": 10 }

7. open_folder — 폴더 열기
   payload: { "folder_path": "C:/project", "new_window": false }

8. save_file — 파일 저장
   payload: { "file_name": null, "folder_path": null }

[응답 형식 — 반드시 이 JSON만 출력]
{
  "type": "명령어타입",
  "payload": { ... 위 스키마에 맞는 필드 ... },
  "guidance": "스크린리더가 읽어줄 친절한 한국어 설명",
  "should_pause": true 또는 false,
  "target_file": "편집할 파일명 (예: main.py)",
  "expected_content": "화면에 보이는 해당 파일의 현재 전체 코드 내용 (있는 그대로)"
}

[규칙]
- type은 위 8가지 중 하나여야 함
- payload는 해당 타입의 스키마를 정확히 따라야 함
- guidance는 시각장애인이 이해할 수 있도록 친절하게 작성
- should_pause: 강의를 일시정지해야 하면 true, 아니면 false
- target_file: 편집 명령(type_text, goto_line, hotkey, save_file)일 때 반드시 대상 파일명을 포함해야 함 (예: "main.py", "app.js"). 로컬 에이전트가 올바른 파일을 열고 편집하기 위해 필수임. 화면에서 강사가 작업 중인 파일명을 읽어서 넣어줘.
- expected_content: 편집 명령일 때 화면에 보이는 해당 파일의 현재 전체 코드 내용을 있는 그대로 넣어줘. 로컬 에이전트가 같은 이름의 다른 파일에 잘못 편집하는 것을 방지하기 위한 검증용임. 화면에 보이는 코드를 최대한 정확하게 읽어서 넣어줘. 화면에 일부만 보이면 보이는 부분만 넣어도 됨.
- 화면에 변화가 없거나 명령이 불필요하면 type을 "type_text", payload를 {"content": ""}, should_pause를 false로
"""

    # ------------------------------------------------------------------
    # 핵심 메서드
    # ------------------------------------------------------------------
    async def analyze_and_decide(
        self,
        image_b64: str,
        local_status: str,
        transcript_context: list[str] | None = None,
    ) -> dict:
        """
        NVIDIA NIM VLM으로 화면 분석 → Pydantic 검증 → 실패 시 재시도.

        Returns:
            AIDecision과 동일한 구조의 dict (type, payload, guidance, should_pause)
        """
        messages = self._build_messages(image_b64, local_status, transcript_context)

        for attempt in range(1 + self.MAX_RETRIES):
            try:
                response = await self.llm.ainvoke(messages)
                raw_text = response.content
                print(f"🤖 [AI 원문] {raw_text[:300]}")

                raw_json = self._extract_json(raw_text)
                decision = AIDecision.model_validate(raw_json)

                print(
                    f"✅ [AI 결정] type={decision.type} "
                    f"payload={json.dumps(decision.payload, ensure_ascii=False)[:100]} "
                    f"pause={decision.should_pause}"
                )
                return decision.model_dump()

            except ValidationError as e:
                if attempt < self.MAX_RETRIES:
                    # 재시도: 검증 에러를 피드백으로 제공
                    error_msg = str(e)
                    print(f"⚠️ AI 응답 검증 실패 (재시도 {attempt + 1}): {error_msg[:100]}")
                    messages.append(
                        HumanMessage(
                            content=(
                                f"응답이 스키마 검증에 실패했어. 에러: {error_msg}\n"
                                "위 스키마를 정확히 따라서 JSON만 다시 출력해줘."
                            )
                        )
                    )
                else:
                    print(f"❌ AI 응답 검증 최종 실패: {e}")
                    return self._fallback_decision("응답이 올바른 형식이 아닙니다.")

            except (ValueError, json.JSONDecodeError) as e:
                if attempt < self.MAX_RETRIES:
                    print(f"⚠️ JSON 추출 실패 (재시도 {attempt + 1}): {e}")
                    messages.append(
                        HumanMessage(
                            content=(
                                "JSON 파싱에 실패했어. 반드시 순수 JSON만 출력해. "
                                "마크다운이나 설명 텍스트 없이 { ... } 만 응답해줘."
                            )
                        )
                    )
                else:
                    print(f"❌ JSON 추출 최종 실패: {e}")
                    return self._fallback_decision("JSON을 추출할 수 없습니다.")

            except Exception as e:
                print(f"❌ AI 분석 실패: {e}")
                return self._fallback_decision("화면을 분석하는 중 오류가 발생했습니다.")

        return self._fallback_decision("알 수 없는 오류")

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------
    def _build_messages(
        self,
        image_b64: str,
        local_status: str,
        transcript_context: list[str] | None,
    ) -> list:
        """LLM 호출용 메시지 리스트 구성"""
        text_parts = [f"현재 로컬 상태: {local_status}."]

        if transcript_context:
            recent = "\n".join(transcript_context[-5:])
            text_parts.append(f"최근 강의 자막:\n{recent}")

        text_parts.append("화면을 분석하고 수강생이 따라해야 할 명령을 JSON으로 내려줘.")

        content = [
            {"type": "text", "text": "\n\n".join(text_parts)},
            {"type": "image_url", "image_url": {"url": image_b64}},
        ]

        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=content),
        ]

    @staticmethod
    def _fallback_decision(reason: str) -> dict:
        """검증/파싱 실패 시 안전한 기본 응답"""
        return AIDecision(
            type="type_text",
            payload={"content": ""},
            guidance=reason,
            should_pause=True,
        ).model_dump()

    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        AI 응답에서 첫 번째 JSON 객체를 추출합니다.

        AI가 여러 JSON을 연속 출력하는 경우({ ... } { ... })
        첫 번째 완전한 객체만 추출합니다.
        """
        text = text.strip()

        # 1차: 전체가 단일 JSON이면 바로 파싱
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2차: 마크다운 코드블록 추출
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 3차: balanced brace 매칭 — 첫 번째 { ... } 객체만 추출
        result = AIService._extract_first_json_object(text)
        if result is not None:
            return result

        raise ValueError(f"AI 응답에서 JSON을 추출할 수 없습니다: {text[:200]}")

    @staticmethod
    def _extract_first_json_object(text: str) -> dict | None:
        """
        문자열에서 brace depth를 추적하여 첫 번째 완전한 JSON 객체를 추출합니다.
        '{ ... } { ... }' 형태에서 첫 번째만 가져옴.
        """
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):
            ch = text[i]

            if escape:
                escape = False
                continue

            if ch == "\\":
                if in_string:
                    escape = True
                continue

            if ch == '"' and not escape:
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None

        return None

    # ------------------------------------------------------------------
    # 테스트
    # ------------------------------------------------------------------
    async def test_ask(self, question: str):
        """연결 확인용 테스트 메서드"""
        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="너는 친절한 도우미야."),
                    HumanMessage(content=question),
                ]
            )
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
