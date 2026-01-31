# ============================================================================
# 📁 main.py - Part 3 로컬 에이전트 메인 엔트리포인트
# ============================================================================
#
# 🎯 역할:
#   1. Part 2 서버와 웹소켓(Socket.IO)으로 통신
#   2. 서버에서 명령을 받아 오디오 재생 + Windows 제어 실행
#   3. 1초마다 로컬 상태(활성 창 등)를 서버에 보고
#
# 📝 멘토님께:
#   이 파일의 "멘토님 전용 구역"에 pywinauto 로직을 추가해 주세요!
#   execute_mentor_logic() 함수가 호출될 때 JSON 데이터와 함께 전달됩니다.
#
# 🚀 실행 방법:
#   python main.py
#
# ============================================================================

import time
import json
import threading
from typing import Any, Dict, Optional

import socketio

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
# 🌐 Socket.IO 클라이언트 설정
# ============================================================================

# Socket.IO 클라이언트 생성
# reconnection=True: 연결이 끊겨도 자동으로 재연결 시도
sio = socketio.Client(
    reconnection=RECONNECT_ENABLED,
    reconnection_delay=RECONNECT_DELAY,
    reconnection_attempts=RECONNECT_MAX_ATTEMPTS if RECONNECT_MAX_ATTEMPTS > 0 else 0,
    logger=False,  # 디버그 로그 비활성화 (필요시 True로)
    engineio_logger=False
)

# 오디오 핸들러 전역 인스턴스
audio_handler: Optional[AudioHandler] = None

# 상태 보고 스레드 실행 플래그
status_report_running = False

# 강의 일시정지 상태
is_lecture_paused = False


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
# 예시 구현:
#   from pywinauto import Application
#   
#   def execute_mentor_logic(command_data: Dict[str, Any]):
#       action = command_data.get("action")
#       if action == "type":
#           # VS Code에 타이핑
#           app = Application().connect(title_re=".*Visual Studio Code.*")
#           app.window().type_keys(command_data.get("content"))
#
# ============================================================================

def execute_mentor_logic(command_data: Dict[str, Any]):
    """
    🎯 멘토님 전용 함수 - pywinauto 로직이 들어갈 곳
    
    이 함수는 오디오 재생이 완료된 후에 호출됩니다.
    Windows 자동화 로직을 여기에 구현해 주세요.
    
    Args:
        command_data (Dict[str, Any]): 서버에서 받은 명령 데이터
            - action: 수행할 동작 종류
            - target: 대상 요소/위치
            - content: 입력할 내용 (있는 경우)
            - 기타 필드...
    
    Returns:
        None
    
    Example command_data:
        {
            "action": "type",
            "target": "editor",
            "content": "print('Hello, World!')",
            "line": 15
        }
    """
    print("=" * 60)
    print("🎯 [멘토님 전용] execute_mentor_logic() 호출됨!")
    print("=" * 60)
    print(f"📦 받은 데이터: {json.dumps(command_data, indent=2, ensure_ascii=False)}")
    print("")
    print("⚠️  여기에 pywinauto 로직을 구현해 주세요!")
    print("    예: VS Code 창 찾기 → 특정 라인으로 이동 → 코드 입력")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님 코드 시작점
    # -------------------------------------------------------------------------
    # 
    # 아래에 pywinauto 코드를 작성해 주세요!
    # 
    # 참고 코드:
    # 
    # from pywinauto import Application
    # from pywinauto.findwindows import ElementNotFoundError
    # 
    # try:
    #     # VS Code 연결
    #     app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
    #     main_window = app.window(title_re=".*Visual Studio Code.*")
    #     
    #     action = command_data.get("action")
    #     
    #     if action == "type":
    #         content = command_data.get("content", "")
    #         main_window.type_keys(content, with_spaces=True)
    #         
    #     elif action == "goto_line":
    #         line_number = command_data.get("line", 1)
    #         main_window.type_keys("^g")  # Ctrl+G (Go to Line)
    #         time.sleep(0.3)
    #         main_window.type_keys(str(line_number) + "{ENTER}")
    #         
    # except ElementNotFoundError:
    #     print("❌ VS Code 창을 찾을 수 없습니다!")
    # 
    # -------------------------------------------------------------------------
    
    pass  # ← 이 줄을 삭제하고 실제 로직을 구현해 주세요


def get_local_status() -> Dict[str, Any]:
    """
    📊 현재 로컬 시스템 상태를 가져옵니다.
    
    멘토님이 pywinauto/pygetwindow를 추가하시면 
    활성 창 정보 등을 반환하도록 확장할 수 있습니다.
    
    Returns:
        Dict[str, Any]: 로컬 상태 정보
            - active_window: 현재 활성 창 제목
            - timestamp: 현재 시간
            - is_paused: 강의 일시정지 상태
    """
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님: pygetwindow 설치 후 아래 주석 해제 가능
    # -------------------------------------------------------------------------
    # import pygetwindow as gw
    # 
    # try:
    #     active_window = gw.getActiveWindow()
    #     window_title = active_window.title if active_window else "Unknown"
    # except Exception:
    #     window_title = "Unknown"
    # -------------------------------------------------------------------------
    
    window_title = "Unknown (pygetwindow 미설치)"  # 임시값
    
    return {
        "active_window": window_title,
        "timestamp": time.time(),
        "is_paused": is_lecture_paused,
        "status": "ready"
    }


# ============================================================================
# 📡 Socket.IO 이벤트 핸들러
# ============================================================================

@sio.event
def connect():
    """✅ 서버 연결 성공 시 호출됩니다."""
    print("=" * 60)
    print("✅ 서버 연결 성공!")
    print(f"   서버 주소: {SERVER_URL}")
    print(f"   연결 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 상태 보고 스레드 시작
    start_status_reporter()


@sio.event
def disconnect():
    """❌ 서버 연결 해제 시 호출됩니다."""
    print("=" * 60)
    print("❌ 서버 연결 끊김!")
    print(f"   시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if RECONNECT_ENABLED:
        print(f"   🔄 {RECONNECT_DELAY}초 후 재연결 시도...")
    print("=" * 60)


@sio.event
def connect_error(data):
    """⚠️ 연결 오류 발생 시 호출됩니다."""
    print(f"⚠️ 연결 오류: {data}")
    print("   서버가 실행 중인지, URL이 올바른지 확인하세요.")


@sio.on(EVENT_EDITOR_SYNC)
def on_editor_sync(data):
    """
    📝 에디터 동기화 명령 수신 핸들러
    
    서버에서 editor_sync 이벤트를 받으면:
    1. 오디오가 있으면 먼저 재생
    2. 재생 완료 후 멘토님의 pywinauto 로직 실행
    
    Args:
        data: 서버에서 받은 명령 데이터 (dict 또는 JSON 문자열)
    """
    print("")
    print("=" * 60)
    print(f"📨 [{EVENT_EDITOR_SYNC}] 명령 수신!")
    print("=" * 60)
    
    # JSON 문자열이면 파싱
    if isinstance(data, str):
        try:
            command_data = json.loads(data)
        except json.JSONDecodeError:
            print(f"❌ JSON 파싱 실패: {data}")
            return
    else:
        command_data = data
    
    print(f"📦 데이터: {json.dumps(command_data, indent=2, ensure_ascii=False)}")
    
    # 1단계: 오디오 재생 (있는 경우)
    audio_url = command_data.get("audio_url")
    
    if audio_url and audio_handler:
        print("\n🔊 오디오 재생 시작...")
        audio_handler.play_from_url(audio_url)
        audio_handler.wait_until_done()  # 재생 완료까지 대기
        print("✅ 오디오 재생 완료!")
    
    # 2단계: 멘토님 로직 실행
    print("\n🎯 멘토님 로직 실행...")
    execute_mentor_logic(command_data)
    
    # 3단계: 작업 완료 알림 (서버에)
    try:
        sio.emit(EVENT_TASK_COMPLETE, {
            "status": "success",
            "command_id": command_data.get("id", "unknown"),
            "timestamp": time.time()
        })
        print("📤 작업 완료 알림 전송")
    except Exception as e:
        print(f"⚠️ 완료 알림 전송 실패: {e}")


@sio.on(EVENT_LECTURE_PAUSE)
def on_lecture_pause(data):
    """
    ⏸️ 강의 일시정지 신호 수신 핸들러 (Pause-and-Explain 기능)
    
    사용자가 질문을 하거나 추가 설명이 필요할 때
    서버에서 이 신호를 보냅니다.
    
    Args:
        data: 일시정지 관련 데이터 (이유, 메시지 등)
    """
    global is_lecture_paused
    
    print("")
    print("=" * 60)
    print(f"⏸️ [{EVENT_LECTURE_PAUSE}] 강의 일시정지!")
    print("=" * 60)
    
    is_lecture_paused = True
    
    # 오디오도 일시정지
    if audio_handler and audio_handler.is_playing:
        audio_handler.pause()
    
    # 일시정지 이유가 있으면 출력
    if isinstance(data, dict):
        reason = data.get("reason", "사용자 요청")
        message = data.get("message", "")
        print(f"   이유: {reason}")
        if message:
            print(f"   메시지: {message}")
    
    print("")
    print("💡 강의가 일시정지되었습니다.")
    print("   서버에서 lecture_resume 신호를 보내면 재개됩니다.")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님: 일시정지 시 추가 동작이 필요하면 여기에 구현
    # -------------------------------------------------------------------------
    # 예: 에디터 하이라이트, 알림 표시 등
    pass


@sio.on(EVENT_LECTURE_RESUME)
def on_lecture_resume(data):
    """
    ▶️ 강의 재개 신호 수신 핸들러
    
    일시정지 후 다시 강의를 재개할 때 서버에서 보냅니다.
    
    Args:
        data: 재개 관련 데이터
    """
    global is_lecture_paused
    
    print("")
    print("=" * 60)
    print(f"▶️ [{EVENT_LECTURE_RESUME}] 강의 재개!")
    print("=" * 60)
    
    is_lecture_paused = False
    
    # 오디오 재개
    if audio_handler and audio_handler.is_paused:
        audio_handler.resume()
    
    print("💡 강의가 재개되었습니다.")
    print("=" * 60)


# ============================================================================
# 📊 상태 보고 기능
# ============================================================================

def start_status_reporter():
    """
    📊 상태 보고 스레드를 시작합니다.
    
    STATUS_REPORT_INTERVAL 간격으로 서버에 로컬 상태를 보고합니다.
    """
    global status_report_running
    
    if status_report_running:
        return  # 이미 실행 중
    
    status_report_running = True
    
    def report_loop():
        while status_report_running and sio.connected:
            try:
                status = get_local_status()
                sio.emit(EVENT_LOCAL_STATUS, status)
                # 디버그용 (너무 많이 출력되면 주석 처리)
                # print(f"📤 상태 보고: {status}")
            except Exception as e:
                print(f"⚠️ 상태 보고 실패: {e}")
            
            time.sleep(STATUS_REPORT_INTERVAL)
    
    thread = threading.Thread(target=report_loop, daemon=True)
    thread.start()
    print(f"📊 상태 보고 시작 (간격: {STATUS_REPORT_INTERVAL}초)")


def stop_status_reporter():
    """📊 상태 보고 스레드를 중지합니다."""
    global status_report_running
    status_report_running = False
    print("📊 상태 보고 중지")


# ============================================================================
# 🚀 메인 실행부
# ============================================================================

def main():
    """
    🚀 메인 함수 - 프로그램 시작점
    
    1. 오디오 핸들러 초기화
    2. 서버 연결
    3. 연결 유지 (이벤트 대기)
    """
    global audio_handler
    
    print("")
    print("=" * 60)
    print("🚀 Part 3: 로컬 에이전트 시작!")
    print("=" * 60)
    print(f"   서버 URL: {SERVER_URL}")
    print(f"   자동 재연결: {'✅ 활성화' if RECONNECT_ENABLED else '❌ 비활성화'}")
    print(f"   상태 보고 간격: {STATUS_REPORT_INTERVAL}초")
    print("=" * 60)
    print("")
    
    # 오디오 핸들러 초기화
    audio_handler = AudioHandler()
    
    try:
        # 서버 연결 시도
        print(f"🔌 서버 연결 시도 중... ({SERVER_URL})")
        sio.connect(
            SERVER_URL,
            wait_timeout=CONNECTION_TIMEOUT,
            transports=['websocket', 'polling']  # WebSocket 우선, 폴링 폴백
        )
        
        # 연결 유지 (이벤트 대기)
        print("\n💡 Ctrl+C로 종료할 수 있습니다.\n")
        sio.wait()
        
    except socketio.exceptions.ConnectionError as e:
        print(f"\n❌ 서버 연결 실패!")
        print(f"   에러: {e}")
        print(f"\n🔧 확인해 주세요:")
        print(f"   1. 서버가 실행 중인가요? ({SERVER_URL})")
        print(f"   2. config.py의 SERVER_URL이 올바른가요?")
        print(f"   3. 네트워크 연결이 정상인가요?")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 종료됨 (Ctrl+C)")
        
    finally:
        # 정리 작업
        print("\n🧹 정리 작업 중...")
        stop_status_reporter()
        
        if sio.connected:
            sio.disconnect()
            print("   ✅ 서버 연결 해제")
        
        if audio_handler:
            audio_handler.cleanup()
            print("   ✅ 오디오 핸들러 정리")
        
        print("\n👋 Part 3 로컬 에이전트 종료!")


# ============================================================================
# 🖥️ 직접 실행 시
# ============================================================================

if __name__ == "__main__":
    main()
