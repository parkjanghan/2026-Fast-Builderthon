import json
from datetime import datetime
from aiohttp import web
from services.ai_service import AIService
from dto.schemas import MessageEnvelope


class WebSocketManager:

    def __init__(self):
        self.sessions = {"chrome": None, "local": None}
        self.ai_service = AIService()
        self.last_local_status = "unknown"

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # 초기 연결 시 환영 메시지
        await ws.send_json({
            "type": "connected",
            "message": "Central Hub connected",
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        print(f"[{self.get_time()}] ✅ [Hub] 신규 클라이언트 접속")

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self._handle_message(ws, msg.data)

        return ws

    async def _handle_message(self, ws, raw_data):
        curr_t = self.get_time()
        try:
            # 1. 봉투(Envelope) 역직렬화
            payload = MessageEnvelope.model_validate_json(raw_data)
            source = payload.source
            msg_type = payload.type

            # 2. 세션 최신화 (Spring의 Session Manager 역할)
            if source in self.sessions:
                self.sessions[source] = ws

            # 3. 비즈니스 로직 분기
            if source == "chrome" and msg_type == "frame":
                image_b64 = payload.data.get("image", "")
                print(f"[{curr_t}] 🖼️  Chrome 프레임 수신 (Len: {len(image_b64)})")

                # [AI Orchestration] NVIDIA NIM 분석
                ai_decision = await self.ai_service.analyze_frame(
                    image_b64, self.last_local_status)
                print(f"[{curr_t}] 🤖 AI Decision: {ai_decision}")

                # [Decision Making] 로컬로 명령 하달
                if self.sessions["local"]:
                    await self.sessions["local"].send_json({
                        "source": "replit",
                        "type": "command",
                        "data": {
                            "decision": ai_decision
                        }
                    })

            elif source == "local" and msg_type == "status":
                self.last_local_status = payload.data.get("status", "unknown")
                print(f"[{curr_t}] 💻 Local 상태 업데이트: {self.last_local_status}")

        except Exception as e:
            print(f"[{curr_t}] ❌ 처리 에러: {str(e)}")
