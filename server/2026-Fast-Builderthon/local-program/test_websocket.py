# ============================================================================
# 🧪 test_websocket.py - WebSocket 연결 테스트
# ============================================================================
# 
# 재준님 서버와 WebSocket 연결 테스트용 스크립트
# 
# ============================================================================

import asyncio
import json

try:
    import websockets
except ImportError:
    print("❌ websockets 라이브러리가 없습니다!")
    print("   설치: uv add websockets")
    exit(1)

# 재준님 서버 주소
SERVER_URL = "wss://5920da4b-c27b-4df6-9297-f7d4ec4f329f-00-st4gdos7kox3.riker.replit.dev/ws"

async def test_connection():
    print("=" * 60)
    print("🧪 WebSocket 연결 테스트")
    print("=" * 60)
    print(f"서버: {SERVER_URL}")
    print("")
    
    try:
        async with websockets.connect(SERVER_URL) as ws:
            print("✅ 연결 성공!")
            
            # 테스트 메시지 전송
            test_message = {"message": "hello world"}
            await ws.send(json.dumps(test_message))
            print(f"📤 전송: {test_message}")
            
            # 응답 대기 (5초)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"📥 수신: {response}")
            except asyncio.TimeoutError:
                print("⏱️ 5초 내 응답 없음 (정상일 수 있음)")
            
            print("")
            print("✅ 테스트 완료! WebSocket 연결이 정상입니다.")
            
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        print("")
        print("🔧 확인해 주세요:")
        print("   1. 서버가 실행 중인가요?")
        print("   2. URL이 올바른가요?")
        print("   3. 네트워크 연결이 정상인가요?")

if __name__ == "__main__":
    asyncio.run(test_connection())
