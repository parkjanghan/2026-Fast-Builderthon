# ============================================================================
# 📁 main.py - Part 3 로컬 에이전트 메인 엔트리포인트
# ============================================================================
#
# 🎯 역할:
#   1. Part 2 서버와 WebSocket으로 통신
#   2. 서버에서 명령을 받아 오디오 재생 + Windows 제어 실행
#   3. 1초마다 로컬 상태(활성 창 등)를 서버에 보고
#
# 📝 멘토님께:
#   이 파일의 "멘토님 전용 구역"에 pywinauto 로직을 추가해 주세요!
#   execute_mentor_logic() 함수가 호출될 때 JSON 데이터와 함께 전달됩니다.
#
# 🚀 실행 방법:
#   uv run python main.py
#
# ============================================================================

import asyncio
import time
import json
from typing import Any, Dict, Optional

import websockets

# 로컬 모듈 임포트
from config import (
    SERVER_URL,
    CONNECTION_TIMEOUT,
    RECONNECT_ENABLED,
    RECONNECT_DELAY,
    RECONNECT_MAX_ATTEMPTS,
    EVENT_EDITOR_SYNC,
    EVENT_LECTURE_PAUSE,
    EVENT_LECTURE_RESUME,
    EVENT_LOCAL_STATUS,
    EVENT_TASK_COMPLETE,
    STATUS_REPORT_INTERVAL
)
from audio_handler import AudioHandler


# ============================================================================
# 🌐 전역 변수
# ============================================================================

# 오디오 핸들러 전역 인스턴스
audio_handler: Optional[AudioHandler] = None

# WebSocket 연결 객체
ws_connection = None

# 강의 일시정지 상태
is_lecture_paused = False

# 연결 상태
is_connected = False


# ============================================================================
# 🔧 멘토님 전용 구역 (pywinauto 로직이 들어갈 곳)
# ============================================================================
#
# 📌 이 구역에 Windows 자동화 로직을 추가해 주세요!
#
# 사용 가능한 데이터 (command_data 딕셔너리):
#   - command_data.get("action"): 수행할 동작 (예: "type", "click", "scroll")
#   - command_data.get("target"): 대상 요소 (예: "line_15", "button_run")
#   - command_data.get("content"): 입력할 내용 (타이핑의 경우)
#   - command_data.get("audio_url"): 재생할 음성 URL
#   - 기타 Part 2에서 정의한 필드들...
#
# ============================================================================

def execute_mentor_logic(command_data: Dict[str, Any]):
    """
    🎯 멘토님 전용 함수 - pywinauto 로직이 들어갈 곳
    
    이 함수는 오디오 재생이 완료된 후에 호출됩니다.
    Windows 자동화 로직을 여기에 구현해 주세요.
    
    Args:
        command_data (Dict[str, Any]): 서버에서 받은 명령 데이터
    """
    print("=" * 60)
    print("🎯 [멘토님 전용] execute_mentor_logic() 호출됨!")
    print("=" * 60)
    print(f"📦 받은 데이터: {json.dumps(command_data, indent=2, ensure_ascii=False)}")
    print("")
    print("⚠️  여기에 pywinauto 로직을 구현해 주세요!")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님 코드 시작점 - 아래에 pywinauto 코드를 작성해 주세요!
    # -------------------------------------------------------------------------
    
    pass  # ← 이 줄을 삭제하고 실제 로직을 구현해 주세요


def get_local_status() -> Dict[str, Any]:
    """
    📊 현재 로컬 시스템 상태를 가져옵니다.
    """
    window_title = "Unknown (pygetwindow 미설치)"  # 임시값
    
    return {
        "type": EVENT_LOCAL_STATUS,
        "active_window": window_title,
        "timestamp": time.time(),
        "is_paused": is_lecture_paused,
        "status": "ready"
    }


# ============================================================================
# 📡 메시지 핸들러
# ============================================================================

async def handle_message(message: str):
    """
    📨 서버에서 받은 메시지를 처리합니다.
    """
    global is_lecture_paused
    
    print("")
    print("=" * 60)
    print(f"📨 메시지 수신!")
    print("=" * 60)
    
    # JSON 파싱
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print(f"📝 텍스트 메시지: {message}")
        return
    
    print(f"📦 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 이벤트 타입 확인
    event_type = data.get("type") or data.get("event") or "unknown"
    
    # ---------------------------------------------------------------------
    # 에디터 동기화 명령
    # ---------------------------------------------------------------------
    if event_type == EVENT_EDITOR_SYNC or data.get("action"):
        print(f"\n📝 [{EVENT_EDITOR_SYNC}] 에디터 명령!")
        
        # 1단계: 오디오 재생 (있는 경우)
        audio_url = data.get("audio_url")
        if audio_url and audio_handler:
            print("\n🔊 오디오 재생 시작...")
            audio_handler.play_from_url(audio_url)
            audio_handler.wait_until_done()
            print("✅ 오디오 재생 완료!")
        
        # 2단계: 멘토님 로직 실행
        print("\n🎯 멘토님 로직 실행...")
        execute_mentor_logic(data)
        
        # 3단계: 작업 완료 알림
        await send_message({
            "type": EVENT_TASK_COMPLETE,
            "status": "success",
            "command_id": data.get("id", "unknown"),
            "timestamp": time.time()
        })
        print("📤 작업 완료 알림 전송")
    
    # ---------------------------------------------------------------------
    # 강의 일시정지 (Pause-and-Explain)
    # ---------------------------------------------------------------------
    elif event_type == EVENT_LECTURE_PAUSE:
        print(f"\n⏸️ [{EVENT_LECTURE_PAUSE}] 강의 일시정지!")
        is_lecture_paused = True
        
        if audio_handler and audio_handler.is_playing:
            audio_handler.pause()
        
        reason = data.get("reason", "사용자 요청")
        print(f"   이유: {reason}")
        print("💡 서버에서 resume 신호를 보내면 재개됩니다.")
    
    # ---------------------------------------------------------------------
    # 강의 재개
    # ---------------------------------------------------------------------
    elif event_type == EVENT_LECTURE_RESUME:
        print(f"\n▶️ [{EVENT_LECTURE_RESUME}] 강의 재개!")
        is_lecture_paused = False
        
        if audio_handler and audio_handler.is_paused:
            audio_handler.resume()
        
        print("💡 강의가 재개되었습니다.")
    
    # ---------------------------------------------------------------------
    # 기타 메시지
    # ---------------------------------------------------------------------
    else:
        print(f"ℹ️ 기타 메시지 (type: {event_type})")


async def send_message(data: Dict[str, Any]):
    """
    📤 서버에 메시지를 전송합니다.
    """
    global ws_connection
    
    if ws_connection:
        try:
            await ws_connection.send(json.dumps(data))
        except Exception as e:
            print(f"⚠️ 메시지 전송 실패: {e}")


# ============================================================================
# 📊 상태 보고 기능
# ============================================================================

async def status_reporter():
    """
    📊 주기적으로 서버에 로컬 상태를 보고합니다.
    """
    global is_connected
    
    while is_connected:
        try:
            status = get_local_status()
            await send_message(status)
            # 디버그용 (너무 많이 출력되면 주석 처리)
            # print(f"📤 상태 보고: {status}")
        except Exception as e:
            print(f"⚠️ 상태 보고 실패: {e}")
        
        await asyncio.sleep(STATUS_REPORT_INTERVAL)


# ============================================================================
# 🔌 WebSocket 연결 관리
# ============================================================================

async def connect_to_server():
    """
    🔌 서버에 연결하고 메시지를 수신합니다.
    """
    global ws_connection, is_connected
    
    print("")
    print("=" * 60)
    print("🚀 Part 3: 로컬 에이전트 시작!")
    print("=" * 60)
    print(f"   서버 URL: {SERVER_URL}")
    print(f"   자동 재연결: {'✅ 활성화' if RECONNECT_ENABLED else '❌ 비활성화'}")
    print(f"   상태 보고 간격: {STATUS_REPORT_INTERVAL}초")
    print("=" * 60)
    print("")
    
    reconnect_count = 0
    
    while True:
        try:
            print(f"🔌 서버 연결 시도 중... ({SERVER_URL})")
            
            async with websockets.connect(SERVER_URL) as ws:
                ws_connection = ws
                is_connected = True
                reconnect_count = 0
                
                print("")
                print("=" * 60)
                print("✅ 서버 연결 성공!")
                print(f"   서버 주소: {SERVER_URL}")
                print(f"   연결 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                print("")
                print("💡 Ctrl+C로 종료할 수 있습니다.")
                print("💡 서버에서 메시지를 기다리는 중...")
                print("")
                
                # 연결 알림 메시지 전송
                await send_message({
                    "type": "hello",
                    "message": "Part 3 로컬 에이전트 연결됨!",
                    "timestamp": time.time()
                })
                
                # 상태 보고 태스크 시작
                status_task = asyncio.create_task(status_reporter())
                
                try:
                    # 메시지 수신 루프
                    async for message in ws:
                        await handle_message(message)
                        
                except websockets.ConnectionClosed as e:
                    print(f"\n❌ 서버 연결 끊김! (코드: {e.code})")
                    
                finally:
                    is_connected = False
                    status_task.cancel()
                    
        except Exception as e:
            print(f"\n❌ 연결 실패: {e}")
        
        # 재연결 로직
        if not RECONNECT_ENABLED:
            print("🔧 자동 재연결이 비활성화되어 있습니다.")
            break
        
        reconnect_count += 1
        if RECONNECT_MAX_ATTEMPTS > 0 and reconnect_count >= RECONNECT_MAX_ATTEMPTS:
            print(f"❌ 최대 재연결 시도 횟수({RECONNECT_MAX_ATTEMPTS})에 도달했습니다.")
            break
        
        print(f"🔄 {RECONNECT_DELAY}초 후 재연결 시도... ({reconnect_count}/{RECONNECT_MAX_ATTEMPTS or '∞'})")
        await asyncio.sleep(RECONNECT_DELAY)


# ============================================================================
# 🚀 메인 실행부
# ============================================================================

def main():
    """
    🚀 메인 함수 - 프로그램 시작점
    """
    global audio_handler
    
    # 오디오 핸들러 초기화
    audio_handler = AudioHandler()
    
    try:
        # 이벤트 루프 실행
        asyncio.run(connect_to_server())
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 종료됨 (Ctrl+C)")
        
    finally:
        # 정리 작업
        print("\n🧹 정리 작업 중...")
        
        if audio_handler:
            audio_handler.cleanup()
            print("   ✅ 오디오 핸들러 정리")
        
        print("\n👋 Part 3 로컬 에이전트 종료!")


# ============================================================================
# 🖥️ 직접 실행 시
# ============================================================================

if __name__ == "__main__":
    main()
