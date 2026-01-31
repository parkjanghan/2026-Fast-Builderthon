from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import os
from core.socket_manager import WebSocketManager

# server/.env 로드
load_dotenv(Path(__file__).parent / ".env")

async def init_app():
    app = web.Application(client_max_size=1024**2 * 20)
    manager = WebSocketManager()

    async def index_handler(request):
        return web.Response(text="Central Hub Running")

    # 라우팅 설정
    app.add_routes(
        [web.get("/ws", manager.websocket_handler), web.get("/", index_handler)]
    )
    return app


if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="0.0.0.0", port=5000)
