import json
from datetime import datetime
from aiohttp import web
from services.ai_service import AIService
from dto.schemas import MessageEnvelope


class WebSocketManager:

    def __init__(self):
        # 세션 관리 딕셔너리 (Spring의 Session Map 역할)
        self.sessions = {"chrome": None, "local": None}
        self.ai_service = AIService()
        self.last_local_status = "unknown"

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        curr_t = self.get_time()

        # 1. [연결 즉시 응답] 클라이언트가 접속하자마자 서버가 먼저 인사를 건넵니다.
        welcome_msg = {
            "source": "replit",
            "type": "connection_ack",
            "data": {
                "message": "Central Hub에 연결되었습니다.",
                "connected_at": curr_t
            }
        }
        await ws.send_json(welcome_msg)
        print(
            f"[{curr_t}] 🔌 [CONNECTION] New client connected & Welcome ACK sent"
        )

        # 2. 메시지 수신 루프
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self._handle_message(ws, msg.data)

        # 연결 종료 시 세션 정리
        for key, session in self.sessions.items():
            if session == ws:
                self.sessions[key] = None
                print(f"[{self.get_time()}] ❌ {key} 클라이언트 연결 종료")

        return ws

    async def _handle_message(self, ws, data):
        curr_t = self.get_time()
        try:
            # Pydantic을 이용한 규격 검증 (Jackson ObjectMapper 역할)
            envelope = MessageEnvelope.model_validate_json(data)
            source = envelope.source
            msg_type = envelope.type

            # 세션 등록
            if source in self.sessions:
                self.sessions[source] = ws

            # 3. [데이터 수신 즉시 응답] Local로부터 데이터가 오면 즉시 로그를 찍고 응답을 보냅니다.
            if source == "local":
                # 수신 로그
                print(
                    f"[{curr_t}] 📥 [RECEIVE] Local -> Server (Type: {msg_type}, Status: {envelope.data.get('status')})"
                )

                # 응답(ACK) 페이로드 준비
                ack_payload = {
                    "source": "replit",
                    "type": "ack",
                    "data": {
                        "message": "서버가 데이터를 정상적으로 수신했습니다.",
                        "received_at": curr_t
                    }
                }

                # 발신 로그 및 실제 전송
                print(f"[{curr_t}] 📤 [SEND] Server -> Local (Payload: ack)")
                await ws.send_json(ack_payload)

                # 상태 업데이트 로직 (필요시)
                if msg_type == "status":
                    self.last_local_status = envelope.data.get(
                        "status", "unknown")

        except Exception as e:
            print(f"[{curr_t}] ❌ [ERROR] 데이터 처리 중 오류 발생: {str(e)}")
