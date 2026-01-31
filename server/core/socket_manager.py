import json
import asyncio
from datetime import datetime
from aiohttp import web
from typing import Dict, Optional  # 타입 안정성을 위한 라이브러리
from services.ai_service import AIService
from dto.schemas import MessageEnvelope


class WebSocketManager:

    def __init__(self):
        # 세션 관리 (타입을 명시하여 Pyright 에러 방지)
        self.sessions: Dict[str, Optional[web.WebSocketResponse]] = {
            "chrome": None,
            "local": None
        }
        self.ai_service = AIService()
        self.last_local_status = "unknown"

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def websocket_handler(self, request: web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        curr_t = self.get_time()

        # 연결 즉시 응답 (Welcome ACK)
        await ws.send_json({
            "source": "replit",
            "type": "connection_ack",
            "data": {
                "message": "Central Hub Connected",
                "at": curr_t
            }
        })
        print(f"[{curr_t}] 🔌 New client connected")

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self._handle_message(ws, msg.data)

        # 연결 종료 시 세션 정리
        for key, session in self.sessions.items():
            if session == ws:
                self.sessions[key] = None
                print(f"[{self.get_time()}] ❌ {key} disconnected")

        return ws

    async def _handle_message(self, ws: web.WebSocketResponse, data: str):
        try:
            envelope = MessageEnvelope.model_validate_json(data)
            source = envelope.source
            msg_type = envelope.type

            # 세션 등록
            if source in self.sessions:
                self.sessions[source] = ws

            # 로컬 클라이언트 데이터 처리
            if source == "local":
                if msg_type == "frame":
                    # 이미지 분석 태스크 비동기 실행
                    image_b64 = envelope.data.get("image")
                    if image_b64:
                        asyncio.create_task(
                            self._process_ai_decision(image_b64))

                elif msg_type == "status":
                    self.last_local_status = envelope.data.get(
                        "status", "unknown")

        except Exception as e:
            print(f"[{self.get_time()}] ❌ Message Error: {str(e)}")

    async def _process_ai_decision(self, image_b64: str):
        """
        NVIDIA NIM 분석 후 명령어를 하달하는 핵심 파이프라인
        """
        # 1. AI Decision Making (NVIDIA NIM 호출)
        decision = await self.ai_service.analyze_and_decide(
            image_b64, self.last_local_status)

        curr_t = self.get_time()

        # 2. 로컬 세션에 명령어 전송 (Type Check로 Never 에러 방지)
        local_ws = self.sessions.get("local")
        if local_ws is not None and not local_ws.closed:
            command_payload = {
                "source": "replit",
                "type": "editor_command",
                "data": {
                    "type": decision.get("type"),
                    "payload": decision.get("payload"),
                    "guidance": decision.get("guidance"),
                    "should_pause": decision.get("should_pause", False)
                }
            }
            # await를 통해 비동기 전송 보장
            await local_ws.send_json(command_payload)
            print(
                f"[{curr_t}] 📡 [DECISION] {decision.get('type')} sent to Local"
            )

        # 3. 크롬 세션에 상태 공유 (UI 업데이트)
        chrome_ws = self.sessions.get("chrome")
        if chrome_ws is not None and not chrome_ws.closed:
            await chrome_ws.send_json({
                "source": "replit",
                "type": "ai_status",
                "data": {
                    "guidance": decision.get("guidance")
                }
            })
