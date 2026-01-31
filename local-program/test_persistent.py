# ============================================================================
# 🔗 test_persistent.py - 연결 유지 테스트
# ============================================================================
# 
# 재준님 서버와 연결을 유지하면서 메시지를 주고받는 테스트
# Ctrl+C로 종료
#
# 실행 방법:
#   cd c:\Users\mnb09\Desktop\2026-Fast-Builderthon\local-program
#   uv run python test_persistent.py
#
# ============================================================================

import asyncio
import json

import websockets

# 재준님 서버 주소
SERVER_URL = "wss://5920da4b-c27b-4df6-9297-f7d4ec4f329f-00-st4gdos7kox3.riker.replit.dev/ws"

async def main():
    print("=" * 60)
    print("🔗 WebSocket 연결 유지 테스트")
    print("=" * 60)
    print(f"서버: {SERVER_URL}")
    print("Ctrl+C로 종료")
    print("=" * 60)
    print("")
    
    try:
        async with websockets.connect(SERVER_URL) as ws:
            print("✅ 연결 성공! 서버에서 메시지를 기다리는 중...")
            print("")
            
            # 연결됨을 알리는 메시지 전송
            hello = {"message": "Part 3 로컬 에이전트 연결됨!", "type": "hello"}
            await ws.send(json.dumps(hello))
            print(f"📤 전송: {hello}")
            print("")
            
            # 계속 메시지 수신 대기
            while True:
                try:
                    message = await ws.recv()
                    print(f"📥 수신: {message}")
                    
                    # JSON 파싱 시도
                    try:
                        data = json.loads(message)
                        print(f"   → 파싱됨: {data}")
                    except:
                        pass
                    
                    print("")
                    
                except websockets.ConnectionClosed:
                    print("❌ 서버가 연결을 끊었습니다.")
                    break
                    
    except Exception as e:
        print(f"❌ 연결 실패: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 종료했습니다. (Ctrl+C)")
