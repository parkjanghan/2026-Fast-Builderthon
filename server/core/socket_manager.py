import json
from datetime import datetime
from aiohttp import web


class WebSocketManager:

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Connected Message
        await ws.send_json({
            "type": "connected",
            "message": "Connection established",
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        print(f"[{self.get_time()}] ✅ [Hub] 클라이언트 연결됨")

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self._handle_message(ws, msg.data)

        print(f"[{self.get_time()}] ❌ [Hub] 클라이언트 연결 종료")
        return ws

    async def _handle_message(self, ws, data):
        curr_t = self.get_time()
        try:
            payload = json.loads(data)
            msg_type = payload.get("type")

            if msg_type == "frame":
                # 여기에 AI Service 호출 로직 연동
                print(
                    f"[{curr_t}] 🖼️  Frame 수신 (Length: {len(payload.get('image', ''))})"
                )

            elif msg_type == "audio":
                # 여기에 STT 및 Decision Making 로직 연동
                print(
                    f"[{curr_t}] 🎵 Audio 수신 (Length: {len(payload.get('data', ''))})"
                )

        except Exception as e:
            print(f"[{curr_t}] ❌ 처리 에러: {str(e)}")
