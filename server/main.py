from aiohttp import web
from core.socket_manager import WebSocketManager


async def init_app():
    app = web.Application(client_max_size=1024**2 * 20)
    manager = WebSocketManager()

    # 라우팅 설정
    app.add_routes([
        web.get('/ws', manager.websocket_handler),
        web.get('/', lambda r: web.Response(text="Central Hub Running"))
    ])
    return app


if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=8080)
