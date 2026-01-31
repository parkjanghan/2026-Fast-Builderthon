from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import os
from core.socket_manager import WebSocketManager

# server/.env 로드
load_dotenv(Path(__file__).parent / ".env")

# 오디오 캐시 디렉토리
AUDIO_DIR = Path(__file__).parent / ".audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)


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
