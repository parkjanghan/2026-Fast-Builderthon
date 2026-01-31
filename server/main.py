# ⚠️ .env를 가장 먼저 로드 (다른 모듈에서 API 키를 사용하기 전에)
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import os  # noqa: E402
from aiohttp import web  # noqa: E402
from core.socket_manager import WebSocketManager  # noqa: E402

print(f"🔑 NVIDIA_API_KEY: {'✅' if os.getenv('NVIDIA_API_KEY') else '❌'}")
print(f"🔑 ELEVENLABS_API_KEY: {'✅' if os.getenv('ELEVENLABS_API_KEY') else '❌'}")

# 오디오 캐시 디렉토리 — voice_service와 동일 경로 보장
# voice_service: Path(voice_service.py).resolve().parent.parent / ".audio_cache"
# = server/.audio_cache (resolve로 symlink 해소)
# main.py도 동일하게 resolve
AUDIO_DIR = Path(__file__).resolve().parent / ".audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)
print(f"📁 오디오 서빙 경로: {AUDIO_DIR}")


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
