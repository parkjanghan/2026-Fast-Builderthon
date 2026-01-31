# ⚠️ .env를 가장 먼저 로드 (다른 모듈에서 API 키를 사용하기 전에)
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import os  # noqa: E402
from aiohttp import web  # noqa: E402
from core.socket_manager import WebSocketManager  # noqa: E402
from services.voice_service import get_voice_service  # noqa: E402

print(f"🔑 NVIDIA_API_KEY: {'✅' if os.getenv('NVIDIA_API_KEY') else '❌'}")
print(f"🔑 ELEVENLABS_API_KEY: {'✅' if os.getenv('ELEVENLABS_API_KEY') else '❌'}")


async def init_app():
    app = web.Application(client_max_size=1024**2 * 20)
    manager = WebSocketManager()

    async def index_handler(request):
        return web.Response(text="Central Hub Running")

    async def tts_handler(request):
        """동적 TTS 스트리밍 엔드포인트 - 파일 저장 없이 바로 음성 반환"""
        request_id = request.match_info.get("id")
        audio_data = await get_voice_service().stream_speech(request_id)
        
        if audio_data:
            return web.Response(
                body=audio_data,
                content_type="audio/mpeg"
            )
        else:
            return web.Response(status=404, text="Audio not found")

    # 라우팅 설정
    app.add_routes([
        web.get("/ws", manager.websocket_handler),
        web.get("/", index_handler),
        web.get("/tts/{id}", tts_handler),  # 동적 TTS 스트리밍
    ])
    return app


if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="0.0.0.0", port=5000)
