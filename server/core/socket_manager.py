import json
import asyncio
import time
from datetime import datetime
from aiohttp import web
from typing import Dict, Optional

from services.ai_service import AIService
from dto.schemas import (
    MessageEnvelope,
    FrameData,
    TranscriptData,
    ConnectedMessage,
    ErrorMessage,
)


class WebSocketManager:
    """
    🌐 WebSocket 허브 — Extension(chrome)과 Local Agent 양쪽을 관리

    프로토콜 (protocol.md 기준):
      - Extension → Server: {source:"chrome", data:{type:"frame"|"transcript", ...}}
      - Local    → Server:  {source:"local",  data:{type:"local_status"|"hello"|..., ...}}
      - Server   → Extension: raw JSON {type:"connected"|"transcript"|"command"|"error"}
      - Server   → Local:     envelope {source:"replit", type:"editor_command", data:{...}}
    """

    def __init__(self):
        self.sessions: Dict[str, Optional[web.WebSocketResponse]] = {
            "chrome": None,
            "local": None,
        }
        self.ai_service = AIService()
        self.last_local_status = "unknown"
        # 자막 문맥 누적 (최근 N개)
        self.transcript_context: list[str] = []

    # ------------------------------------------------------------------
    # 유틸
    # ------------------------------------------------------------------
    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # WebSocket 핸들러 (aiohttp)
    # ------------------------------------------------------------------
    async def websocket_handler(self, request: web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        t = self._now_str()

        # 연결 즉시 응답 (Welcome ACK)
        await ws.send_json(
            {
                "source": "server",
                "type": "connection_ack",
                "data": {"message": "Central Hub Connected", "at": t},
            }
        )
        print(f"[{t}] 🔌 New client connected")

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self._route_message(ws, msg.data)

        # 연결 종료 시 세션 정리
        for key, session in self.sessions.items():
            if session is ws:
                self.sessions[key] = None
                print(f"[{self._now_str()}] ❌ {key} disconnected")

        return ws

    # ------------------------------------------------------------------
    # 메시지 라우팅 — 공통 envelope {source, data} 파싱
    # ------------------------------------------------------------------
    async def _route_message(self, ws: web.WebSocketResponse, raw: str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            await ws.send_json(ErrorMessage(code="PARSE_ERROR", message=str(e)).model_dump())
            return

        # envelope 검증
        try:
            source = parsed.get("source", "unknown")
            inner_data = parsed.get("data", {})
            msg_type = inner_data.get("type", "unknown")

            # 세션 등록
            self.sessions[source] = ws

            # 크롬 확장프로그램에서 frame 수신
            if source == "chrome":
                if msg_type == "frame":
                    # 이미지 분석 태스크 비동기 실행
                    image_b64 = inner_data.get("image")
                    if image_b64:
                        asyncio.create_task(self._process_ai_decision(image_b64))

            # 로컬 에이전트에서 상태 수신
            elif source == "local":
                if msg_type == "local_status":
                    self.last_local_status = inner_data.get("active_window", "unknown")

        except Exception as e:
            print(f"[{self._now_str()}] ❌ Message Error: {str(e)}")

    async def _process_ai_decision(self, image_b64: str):
        """
        NVIDIA NIM 분석 후 Local Agent에 명령 전송 + Extension에 상태 공유
        """
        decision = await self.ai_service.analyze_and_decide(
            image_b64, self.last_local_status, self.transcript_context
        )
        t = self._now_str()

        # 1. Local Agent에 editor_command 전송
        local_ws = self.sessions.get("local")
        if local_ws is not None and not local_ws.closed:
            # action/params 형식으로 전송 (로컬 호환)
            action_type = decision.get("type", "").upper()
            params = decision.get("payload", {})
            # target_file이 있으면 params에 포함 (로컬이 올바른 파일에서 작업하도록)
            target_file = decision.get("target_file")
            if target_file:
                params["target_file"] = target_file
            expected_content = decision.get("expected_content")
            if expected_content:
                params["expected_content"] = expected_content
            command_payload = {
                "source": "server",
                "data": {
                    "action": action_type,
                    "params": params,
                    "audio_url": decision.get("audio_url"),
                },
            }
            await local_ws.send_json(command_payload)
            print(f"[{t}] 📡 [DECISION] {action_type} sent to Local")

        chrome_ws = self.sessions.get("chrome")
        if chrome_ws is not None and not chrome_ws.closed:
            await chrome_ws.send_json(
                {
                    "source": "server",
                    "data": {"type": "ai_status", "guidance": decision.get("guidance")},
                }
            )
