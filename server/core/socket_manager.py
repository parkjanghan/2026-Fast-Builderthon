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
            "source": "server",
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
            raw_data = json.loads(data)
            source = raw_data.get("source", "unknown")
            inner_data = raw_data.get("data", {})
            msg_type = inner_data.get("type", "unknown")

            # 세션 등록
            if source in self.sessions:
                self.sessions[source] = ws

            # 크롬 확장프로그램에서 frame 수신
            if source == "chrome":
                if msg_type == "frame":
                    # 이미지 분석 태스크 비동기 실행
                    image_b64 = inner_data.get("image")
                    if image_b64:
                        asyncio.create_task(
                            self._process_ai_decision(image_b64))

            # 로컬 에이전트에서 상태 수신
            elif source == "local":
                if msg_type == "local_status":
                    self.last_local_status = inner_data.get(
                        "active_window", "unknown")

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
            # action/params 형식으로 전송 (로컬 호환)
            action_type = decision.get("type", "").upper()
            command_payload = {
                "source": "server",
                "data": {
                    "action": action_type,
                    "params": decision.get("payload", {}),
                    "audio_url": decision.get("audio_url")
                }
            }
            await local_ws.send_json(command_payload)
            print(
                f"[{curr_t}] 📡 [DECISION] {action_type} sent to Local"
            )

        chrome_ws = self.sessions.get("chrome")
        if chrome_ws is not None and not chrome_ws.closed:
            await chrome_ws.send_json({
                "source": "server",
                "data": {
                    "type": "ai_status",
                    "guidance": decision.get("guidance")
                }
            })
