from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import os
from core.socket_manager import WebSocketManager

# server/.env 로드
load_dotenv(Path(__file__).parent / ".env")

# 오디오 캐시 디렉토리 (voice_service.py와 동일 경로여야 함)
# Replit에서 main.py 위치가 다를 수 있으므로 server/ 기준 절대경로 사용
_SERVER_DIR = Path(__file__).parent
# core/ 폴더가 있으면 여기가 server/ 디렉토리
if (_SERVER_DIR / "core").exists():
    AUDIO_DIR = _SERVER_DIR / ".audio_cache"
else:
    # main.py가 workspace 루트에 있는 경우 (Replit)
    # voice_service가 저장하는 경로를 직접 찾기
    for candidate in [
        _SERVER_DIR / "2026-Fast-Builderthon" / "server" / ".audio_cache",
        _SERVER_DIR / "server" / ".audio_cache",
        _SERVER_DIR / ".audio_cache",
    ]:
        if candidate.parent.exists():
            AUDIO_DIR = candidate
            break
    else:
        AUDIO_DIR = _SERVER_DIR / ".audio_cache"

AUDIO_DIR.mkdir(exist_ok=True)
print(f"📁 [Main] 오디오 서빙 경로: {AUDIO_DIR.resolve()}")


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
            return web.Response(status=404, text="Audio not found")
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
