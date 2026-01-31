from pathlib import Path
from dotenv import load_dotenv

# ⚠️ 반드시 다른 모듈 import 전에 .env 로드!
# socket_manager → ai_service → ChatNVIDIA() 초기화 시 API 키가 필요함
import core

SERVER_DIR = Path(core.__file__).resolve().parent.parent
load_dotenv(SERVER_DIR / ".env")
print(f"📁 [Main] server/ 디렉토리: {SERVER_DIR}")
print(
    f"🔑 [Main] NVIDIA_API_KEY: {'✅ 설정됨' if __import__('os').getenv('NVIDIA_API_KEY') else '❌ 없음'}"
)
print(
    f"🔑 [Main] ELEVENLABS_API_KEY: {'✅ 설정됨' if __import__('os').getenv('ELEVENLABS_API_KEY') else '❌ 없음'}"
)

# 이제 나머지 모듈 import (API 키가 이미 환경변수에 로드된 상태)
from aiohttp import web  # noqa: E402
from core.socket_manager import WebSocketManager  # noqa: E402

# 오디오 캐시 디렉토리
AUDIO_DIR = SERVER_DIR / ".audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)
print(f"📁 [Main] 오디오 서빙 경로: {AUDIO_DIR}")


async def init_app():
    app = web.Application(client_max_size=1024**2 * 20)
    manager = WebSocketManager()

    async def index_handler(request):
        return web.Response(text="Central Hub Running")

    async def audio_handler(request):
        """오디오 파일 서빙 (/audio/{filename})"""
        filename = request.match_info["filename"]
        file_path = AUDIO_DIR / filename
        if not file_path.exists():
            print(f"❌ [Audio] 파일 없음: {file_path}")
            existing = list(AUDIO_DIR.glob("*.mp3"))
            print(f"   존재하는 파일: {[f.name for f in existing[:5]]}")
            return web.Response(status=404, text=f"Audio not found: {filename}")
        return web.FileResponse(file_path, headers={"Content-Type": "audio/mpeg"})

    # 라우팅 설정
    app.add_routes(
        [
            web.get("/ws", manager.websocket_handler),
            web.get("/", index_handler),
            web.get("/audio/{filename}", audio_handler),
        ]
    )
    return app


if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="0.0.0.0", port=5000)
