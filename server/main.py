from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import os
from core.socket_manager import WebSocketManager

# server/ 디렉토리 = core/ 패키지의 부모 (symlink에 영향받지 않음)
import core

SERVER_DIR = Path(core.__file__).resolve().parent.parent
print(f"📁 [Main] server/ 디렉토리: {SERVER_DIR}")

# .env 로드 (server/.env)
load_dotenv(SERVER_DIR / ".env")

# 오디오 캐시 디렉토리 — voice_service.py와 동일 경로
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
            # 디렉토리 내 파일 목록 출력 (디버깅용)
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
