# ============================================================================
# 📁 main.py - Part 3 로컬 에이전트 컨트롤 타워 🎛️
# ============================================================================
#
# 🎯 역할:
#   1. Part 2 서버와 WebSocket으로 통신 (순수 WebSocket)
#   2. Downlink: 서버 명령 수신 → 오디오 재생 + 멘토님 로직 실행
#   3. Uplink: 1초마다 로컬 상태(활성 창 등)를 서버에 보고
#
# 📝 멘토님께:
#   이 파일의 "멘토님 전용 구역"에 pywinauto 로직을 추가해 주세요!
#   execute_mentor_logic() 함수가 호출될 때 JSON 데이터와 함께 전달됩니다.
#
# 📦 모듈 구조:
#   main.py           - 컨트롤 타워 (이 파일)
#   ├── audio_handler.py    - 입 (ElevenLabs 음성 재생)
#   └── status_monitor.py   - 눈 (로컬 상태 감시)
#
# 🚀 실행 방법:
#   python -m uv run python main.py
#
# ============================================================================

import asyncio
import time
import json
from datetime import datetime
from typing import Any, Dict, Optional

import websockets

# 로컬 모듈 임포트
from config import (
    SERVER_URL,
    CONNECTION_TIMEOUT,
    RECONNECT_ENABLED,
    RECONNECT_DELAY,
    RECONNECT_MAX_ATTEMPTS,
    STATUS_REPORT_INTERVAL
)
from audio_handler import AudioHandler
from status_monitor import StatusMonitor


# ============================================================================
# 📡 프로토콜 정의 (재준 님과 협의 완료!)
# ============================================================================
#
# 📥 수신 (Downlink) JSON 형식 (서버 → 로컬):
#   {
#       "source": "server",
#       "data": {
#           "action": "GOTO_LINE",           # 수행할 동작
#           "params": {"line": 10},          # 동작 파라미터
#           "audio_url": "https://...",      # ElevenLabs 음성 URL (선택)
#           "timestamp": "2026-01-31 09:12:45"
#       }
#   }
#
# 📤 송신 (Uplink) JSON 형식 (로컬 → 서버):
#   {
#       "source": "local",
#       "data": {
#           "type": "local_status",
#           "active_window": "Visual Studio Code",
#           "urgent": false,
#           "timestamp": "2026-01-31 09:12:45"
#       }
#   }
#
# 🛑 주요 액션 타입 (data.action):
#   - GOTO_LINE: 특정 줄로 이동 (params: { line: 숫자 })
#   - TYPE_CODE: 코드 입력 (params: { text: "..." })
#
# ============================================================================


# ============================================================================
# 🌐 전역 변수
# ============================================================================

# 모듈 인스턴스
audio_handler: Optional[AudioHandler] = None
status_monitor: Optional[StatusMonitor] = None

# WebSocket 연결 객체
ws_connection = None

# 상태 플래그
is_connected = False


# ============================================================================
# 🔧 유틸리티 함수
# ============================================================================

def get_timestamp() -> str:
    """현재 시간을 문자열로 반환 (재준 님 형식)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# 🔧 멘토님 전용 구역 (pywinauto 로직이 들어갈 곳)
# ============================================================================
#
# 📌 이 구역에 Windows 자동화 로직을 추가해 주세요!
#
# 📥 받을 수 있는 데이터 (command_data 딕셔너리):
#   - command_data.get("action"): 수행할 동작 
#       예: "GOTO_LINE", "TYPE_CODE", "CLICK", "SCROLL"
#   - command_data.get("params"): 동작 파라미터 (딕셔너리)
#       예: {"line": 10}, {"text": "print('hello')"}, {"x": 100, "y": 200}
#   - command_data.get("audio_url"): 재생할 음성 URL (이미 처리됨)
#
# 📤 반환값:
#   - True: 작업 성공
#   - False: 작업 실패
#   - 딕셔너리: 상세 결과 (서버에 전송됨)
#
# 💡 구현 예시:
#   from pywinauto import Application
#   
#   def execute_mentor_logic(command_data):
#       action = command_data.get("action")
#       params = command_data.get("params", {})
#       
#       app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
#       window = app.window(title_re=".*Visual Studio Code.*")
#       
#       if action == "GOTO_LINE":
#           line = params.get("line", 1)
#           window.type_keys("^g")  # Ctrl+G
#           window.type_keys(str(line) + "{ENTER}")
#           return True
#           
#       elif action == "TYPE_CODE":
#           text = params.get("text", "")
#           window.type_keys(text, with_spaces=True)
#           return True
#           
#       return False
#
# ============================================================================

def execute_mentor_logic(command_data: Dict[str, Any]) -> Any:
    """
    🎯 멘토님 전용 함수 - pywinauto 로직이 들어갈 곳
    
    이 함수는 오디오 재생이 완료된 후에 호출됩니다.
    Windows 자동화 로직을 여기에 구현해 주세요.
    
    Args:
        command_data (Dict[str, Any]): 서버에서 받은 명령 데이터 (data 필드 내용)
            - action (str): 수행할 동작 종류
            - params (dict): 동작 파라미터
            - 기타 서버에서 정의한 필드들...
    
    Returns:
        bool 또는 dict: 작업 결과
            - True: 성공
            - False: 실패
            - dict: 상세 결과 {"success": True, "message": "..."}
    
    Example:
        Input:
        {
            "action": "GOTO_LINE",
            "params": {"line": 15}
        }
        
        Output:
        True  # 또는 {"success": True, "line": 15}
    """
    print("")
    print("=" * 60)
    print("🎯 [멘토님 전용] execute_mentor_logic() 호출됨!")
    print("=" * 60)
    
    action = command_data.get("action", "UNKNOWN")
    params = command_data.get("params", {})
    
    print(f"   📋 액션: {action}")
    print(f"   📦 파라미터: {json.dumps(params, ensure_ascii=False)}")
    print("")
    print("   ⚠️  여기에 pywinauto 로직을 구현해 주세요!")
    print("   💡 pywinauto 설치: python -m uv add pywinauto")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님 코드 시작점
    # -------------------------------------------------------------------------
    # 
    # 아래 pass를 삭제하고 pywinauto 코드를 작성해 주세요!
    # 
    # from pywinauto import Application
    # 
    # try:
    #     app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
    #     window = app.window(title_re=".*Visual Studio Code.*")
    #     
    #     if action == "GOTO_LINE":
    #         line = params.get("line", 1)
    #         window.type_keys("^g")
    #         time.sleep(0.2)
    #         window.type_keys(str(line) + "{ENTER}")
    #         return True
    #         
    #     elif action == "TYPE_CODE":
    #         text = params.get("text", "")
    #         window.type_keys(text, with_spaces=True, pause=0.02)
    #         return True
    #     
    # except Exception as e:
    #     print(f"❌ pywinauto 오류: {e}")
    #     return False
    # 
    # -------------------------------------------------------------------------
    
    return True  # ← 임시 반환값. 실제 구현 시 삭제


# ============================================================================
# 📨 Downlink Handler (서버 → 로컬)
# ============================================================================

async def handle_downlink_message(message: str):
    """
    📨 서버에서 받은 메시지를 처리합니다.
    
    재준 님 형식:
    {
        "source": "server",
        "data": { ... 실제 데이터 ... }
    }
    
    메시지 처리 순서:
    1. JSON 파싱 → data 필드 추출
    2. audio_url이 있으면 오디오 재생 (동기)
    3. action이 있으면 멘토님 로직 실행
    4. 결과를 서버에 보고
    """
    print("")
    print("=" * 60)
    print("📨 [Downlink] 메시지 수신!")
    print("=" * 60)
    
    # ---------------------------------------------------------------------
    # 1단계: JSON 파싱 및 data 추출
    # ---------------------------------------------------------------------
    try:
        raw_message = json.loads(message)
    except json.JSONDecodeError:
        print(f"📝 텍스트 메시지: {message}")
        return
    
    print(f"📦 원본 수신 데이터:")
    print(json.dumps(raw_message, indent=2, ensure_ascii=False))
    
    # source 확인 (디버그용)
    source = raw_message.get("source", "unknown")
    print(f"📍 발신자: {source}")
    
    # data 필드 추출 (재준 님 형식)
    # 만약 data 필드가 없으면 raw_message 자체를 사용 (하위 호환)
    data = raw_message.get("data", raw_message)
    
    action = data.get("action", "").upper() if isinstance(data.get("action"), str) else ""
    
    # ---------------------------------------------------------------------
    # 2단계: 오디오 재생 (있는 경우)
    # ---------------------------------------------------------------------
    audio_url = data.get("audio_url")
    
    if audio_url and audio_handler:
        print("\n🔊 [Audio] ElevenLabs 음성 재생 시작...")
        audio_handler.play_from_url_sync(audio_url)  # 동기식: 재생 완료까지 대기
        print("✅ [Audio] 음성 재생 완료!")
    
    # ---------------------------------------------------------------------
    # 3단계: 멘토님 로직 실행 (action이 있는 경우)
    # ---------------------------------------------------------------------
    if action:
        print(f"\n🎯 [Action] 멘토님 로직 실행: {action}")
        
        result = execute_mentor_logic(data)
        
        # 결과 서버에 보고
        await send_uplink_message({
            "type": "action_complete",
            "action": action,
            "success": bool(result),
            "result": result if isinstance(result, dict) else None,
            "command_id": data.get("id", "unknown"),
            "timestamp": get_timestamp()
        })
        print("📤 [Uplink] 작업 완료 보고 전송")


# ============================================================================
# 📤 Uplink Handler (로컬 → 서버)
# ============================================================================

async def send_uplink_message(data: Dict[str, Any]):
    """
    📤 서버에 메시지를 전송합니다.
    
    재준 님 형식으로 래핑:
    {
        "source": "local",
        "data": { ... 실제 데이터 ... }
    }
    """
    global ws_connection
    
    if ws_connection:
        try:
            # 재준 님 형식으로 래핑
            wrapped_message = {
                "source": "local",
                "data": data
            }
            
            await ws_connection.send(json.dumps(wrapped_message))
        except Exception as e:
            print(f"⚠️ [Uplink] 전송 실패: {e}")


async def status_report_loop():
    """
    📊 주기적으로 서버에 로컬 상태를 보고합니다.
    
    재준 님 형식:
    {
        "source": "local",
        "data": {
            "type": "local_status",
            "active_window": "...",
            "urgent": false,
            "timestamp": "2026-01-31 09:12:45"
        }
    }
    """
    global is_connected
    
    print(f"📊 [Uplink] 상태 보고 시작 (간격: {STATUS_REPORT_INTERVAL}초)")
    
    while is_connected:
        try:
            if status_monitor:
                # 로컬 상태 수집
                raw_status = status_monitor.get_current_status()
                
                # 재준 님 형식에 맞게 변환
                status_data = {
                    "type": "local_status",
                    "active_window": raw_status.get("active_window", "Unknown"),
                    "is_vscode": raw_status.get("is_vscode", False),
                    "urgent": False,  # 긴급 상황 시 True로 변경
                    "timestamp": get_timestamp()
                }
                
                await send_uplink_message(status_data)
                
        except Exception as e:
            print(f"⚠️ [Uplink] 상태 보고 실패: {e}")
        
        await asyncio.sleep(STATUS_REPORT_INTERVAL)


# ============================================================================
# 🔌 WebSocket 연결 관리
# ============================================================================

async def connect_to_server():
    """
    🔌 서버에 연결하고 메시지를 송수신합니다.
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
            print(f"🔌 서버 연결 시도 중...")
            
            async with websockets.connect(SERVER_URL) as ws:
                ws_connection = ws
                is_connected = True
                reconnect_count = 0
                
                print("")
                print("=" * 60)
                print("✅ 서버 연결 성공!")
                print(f"   서버: {SERVER_URL}")
                print(f"   시간: {get_timestamp()}")
                print("=" * 60)
                print("")
                print("💡 Ctrl+C로 종료")
                print("💡 서버에서 명령을 기다리는 중...")
                print("")
                
                # 연결 알림 전송 (재준 님 형식)
                await send_uplink_message({
                    "type": "hello",
                    "message": "Part 3 로컬 에이전트 연결됨!",
                    "urgent": False,
                    "timestamp": get_timestamp()
                })
                
                # 상태 보고 태스크 시작
                status_task = asyncio.create_task(status_report_loop())
                
                try:
                    # 메시지 수신 루프 (Downlink)
                    async for message in ws:
                        await handle_downlink_message(message)
                        
                except websockets.ConnectionClosed as e:
                    print(f"\n❌ 서버 연결 끊김! (코드: {e.code})")
                    
                finally:
                    is_connected = False
                    status_task.cancel()
                    
        except Exception as e:
            print(f"\n❌ 연결 실패: {e}")
        
        # 재연결 로직
        if not RECONNECT_ENABLED:
            break
        
        reconnect_count += 1
        if RECONNECT_MAX_ATTEMPTS > 0 and reconnect_count >= RECONNECT_MAX_ATTEMPTS:
            print(f"❌ 최대 재연결 시도 횟수({RECONNECT_MAX_ATTEMPTS})에 도달")
            break
        
        print(f"🔄 {RECONNECT_DELAY}초 후 재연결... ({reconnect_count}/{RECONNECT_MAX_ATTEMPTS or '∞'})")
        await asyncio.sleep(RECONNECT_DELAY)


# ============================================================================
# 🚀 메인 실행부
# ============================================================================

def main():
    """🚀 프로그램 시작점"""
    global audio_handler, status_monitor
    
    # 모듈 초기화
    print("")
    print("🔧 모듈 초기화 중...")
    audio_handler = AudioHandler()
    status_monitor = StatusMonitor(sender_id="LOCAL_AGENT_KUNHO")
    
    try:
        asyncio.run(connect_to_server())
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자 종료 (Ctrl+C)")
        
    finally:
        print("\n🧹 정리 작업...")
        
        if audio_handler:
            audio_handler.cleanup()
        
        print("\n👋 Part 3 로컬 에이전트 종료!")


if __name__ == "__main__":
    main()
