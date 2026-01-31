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

        # 연결 즉시 protocol.md 형식의 connected 메시지 전송
        await ws.send_json(ConnectedMessage(timestamp=self._now_ms()).model_dump())
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
            await ws.send_json(
                ErrorMessage(code="PARSE_ERROR", message=str(e)).model_dump()
            )
            return

        # envelope 검증
        try:
            envelope = MessageEnvelope.model_validate(parsed)
        except Exception:
            # envelope 형식이 아닌 경우 (fallback)
            print(f"[{self._now_str()}] ⚠️ Non-envelope message: {list(parsed.keys())}")
            return

        source = envelope.source
        data = envelope.data

        # 세션 등록
        self.sessions[source] = ws

        if source == "chrome":
            await self._handle_chrome_message(ws, data)
        elif source == "local":
            await self._handle_local_message(data)

    # ------------------------------------------------------------------
    # Extension(chrome) 메시지 처리
    # ------------------------------------------------------------------
    async def _handle_chrome_message(self, ws: web.WebSocketResponse, data: dict):
        msg_type = data.get("type", "")
        t = self._now_str()

        if msg_type == "frame":
            try:
                frame = FrameData.model_validate(data)
            except Exception as e:
                await ws.send_json(
                    ErrorMessage(code="INVALID_FORMAT", message=str(e)).model_dump()
                )
                return

            print(f"[{t}] 📸 Frame received (videoTime={frame.videoTime}s)")

            # AI 분석 파이프라인 비동기 실행
            asyncio.create_task(self._process_ai_decision(frame.image))

        elif msg_type == "transcript":
            try:
                transcript = TranscriptData.model_validate(data)
            except Exception as e:
                await ws.send_json(
                    ErrorMessage(code="INVALID_FORMAT", message=str(e)).model_dump()
                )
                return

            print(
                f"[{t}] 📝 Transcript received "
                f"({transcript.videoTimeStart}s – {transcript.videoTimeEnd}s): "
                f"{transcript.text[:50]}..."
            )

            # 문맥 누적 (최근 10개)
            self.transcript_context.append(transcript.text)
            if len(self.transcript_context) > 10:
                self.transcript_context.pop(0)

        else:
            print(f"[{t}] ⚠️ Unknown chrome message type: {msg_type}")

    # ------------------------------------------------------------------
    # Local Agent 메시지 처리
    # ------------------------------------------------------------------
    async def _handle_local_message(self, data: dict):
        msg_type = data.get("type", "")
        t = self._now_str()

        if msg_type == "local_status":
            self.last_local_status = data.get("active_window", "unknown")

        elif msg_type == "hello":
            print(f"[{t}] 👋 Local Agent connected: {data.get('message', '')}")

        elif msg_type == "action_complete":
            action = data.get("action", "?")
            success = data.get("success", False)
            icon = "✅" if success else "❌"
            print(f"[{t}] {icon} Local completed: {action}")

        else:
            print(f"[{t}] 📩 Local message: {msg_type}")

    # ------------------------------------------------------------------
    # AI Decision 파이프라인 (NVIDIA NIM → Local Agent 명령)
    # ------------------------------------------------------------------
    async def _process_ai_decision(self, image_b64: str):
        """
        NVIDIA NIM 분석 후 Local Agent에 명령 전송 + Extension에 상태 공유
        """
        decision = await self.ai_service.analyze_and_decide(
            image_b64, self.last_local_status
        )
        t = self._now_str()

        # 1. Local Agent에 editor_command 전송
        local_ws = self.sessions.get("local")
        if local_ws is not None and not local_ws.closed:
            command_payload = {
                "source": "replit",
                "type": "editor_command",
                "data": {
                    "type": decision.get("type"),
                    "payload": decision.get("payload"),
                    "guidance": decision.get("guidance"),
                    "should_pause": decision.get("should_pause", False),
                },
            }
            await local_ws.send_json(command_payload)
            print(f"[{t}] 📡 [DECISION] {decision.get('type')} → Local")

        # 2. Extension에 pause 명령 (should_pause인 경우)
        chrome_ws = self.sessions.get("chrome")
        if chrome_ws is not None and not chrome_ws.closed:
            if decision.get("should_pause"):
                await chrome_ws.send_json(
                    {
                        "type": "command",
                        "action": "pause",
                        "value": None,
                    }
                )

            # AI 상태 공유 (guidance)
            guidance = decision.get("guidance")
            if guidance:
                await chrome_ws.send_json(
                    {
                        "type": "ai_status",
                        "guidance": guidance,
                    }
                )
