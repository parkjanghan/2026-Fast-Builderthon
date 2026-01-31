# ============================================================================
# 📁 status_monitor.py - 로컬 상태 모니터링 모듈 (눈 👁️)
# ============================================================================
#
# 🎯 역할:
#   현재 컴퓨터의 상태를 감시하고 서버에 보고할 데이터를 수집합니다.
#   - 현재 활성 창 제목 (Active Window Title)
#   - 화면 해상도, 마우스 위치 등 (확장 가능)
#
# 📝 사용 예시:
#   from status_monitor import StatusMonitor
#   
#   monitor = StatusMonitor()
#   status = monitor.get_current_status()
#   print(status)  # {"active_window": "Visual Studio Code", ...}
#
# ============================================================================

import time
from typing import Dict, Any, Optional

# pygetwindow: 현재 활성 창 정보를 가져오는 라이브러리
try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False
    print("⚠️ [StatusMonitor] pygetwindow 미설치. 'uv add pygetwindow' 실행 필요")


class StatusMonitor:
    """
    👁️ 로컬 상태 모니터
    
    현재 컴퓨터의 상태를 수집하여 서버에 보고할 데이터를 생성합니다.
    
    Attributes:
        sender_id (str): 이 에이전트를 식별하는 ID
    """
    
    def __init__(self, sender_id: str = "LOCAL_AGENT_KUNHO"):
        """
        StatusMonitor 초기화
        
        Args:
            sender_id (str): 서버에 보고할 때 사용할 발신자 ID
        """
        self.sender_id = sender_id
        self._last_active_window: str = "Unknown"
        
        print(f"👁️ [StatusMonitor] 상태 모니터 초기화 완료")
        print(f"   발신자 ID: {self.sender_id}")
        print(f"   pygetwindow: {'✅ 사용 가능' if PYGETWINDOW_AVAILABLE else '❌ 미설치'}")
    
    # -------------------------------------------------------------------------
    # 📊 상태 수집 메서드들
    # -------------------------------------------------------------------------
    
    def get_active_window_title(self) -> str:
        """
        🪟 현재 활성화된 창의 제목을 가져옵니다.
        
        Returns:
            str: 활성 창 제목 (예: "Visual Studio Code", "Chrome - Google")
        """
        if not PYGETWINDOW_AVAILABLE:
            return "Unknown (pygetwindow 미설치)"
        
        try:
            active_window = gw.getActiveWindow()
            if active_window and active_window.title:
                self._last_active_window = active_window.title
                return active_window.title
            else:
                return "No Active Window"
        except Exception as e:
            print(f"⚠️ [StatusMonitor] 활성 창 조회 실패: {e}")
            return self._last_active_window  # 마지막으로 알려진 값 반환
    
    def get_all_windows(self) -> list:
        """
        📋 열려있는 모든 창 목록을 가져옵니다.
        
        Returns:
            list: 창 제목 목록
        """
        if not PYGETWINDOW_AVAILABLE:
            return []
        
        try:
            windows = gw.getAllWindows()
            return [w.title for w in windows if w.title]
        except Exception as e:
            print(f"⚠️ [StatusMonitor] 창 목록 조회 실패: {e}")
            return []
    
    def is_vscode_active(self) -> bool:
        """
        💻 VS Code가 현재 활성 창인지 확인합니다.
        
        Returns:
            bool: VS Code가 활성화되어 있으면 True
        """
        active = self.get_active_window_title()
        return "Visual Studio Code" in active or "Code" in active
    
    # -------------------------------------------------------------------------
    # 📤 서버 보고용 데이터 생성
    # -------------------------------------------------------------------------
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        📊 현재 로컬 상태를 JSON-직렬화 가능한 딕셔너리로 반환합니다.
        
        이 메서드의 반환값이 서버로 전송됩니다.
        
        Returns:
            Dict[str, Any]: 상태 정보
                - sender: 발신자 ID
                - type: 메시지 타입
                - active_window: 현재 활성 창 제목
                - is_vscode: VS Code 활성화 여부
                - timestamp: 현재 시간 (Unix timestamp)
        
        Example:
            {
                "sender": "LOCAL_AGENT_KUNHO",
                "type": "local_status",
                "active_window": "Visual Studio Code",
                "is_vscode": true,
                "timestamp": 1706745600.123
            }
        """
        active_window = self.get_active_window_title()
        
        return {
            "sender": self.sender_id,
            "type": "local_status",
            "active_window": active_window,
            "is_vscode": self.is_vscode_active(),
            "timestamp": time.time()
        }
    
    # -------------------------------------------------------------------------
    # 🛠️ 멘토님 확장 구역
    # -------------------------------------------------------------------------
    #
    # 멘토님이 pywinauto를 사용하시면 아래 메서드들을 추가할 수 있습니다:
    #
    # def get_cursor_position_in_editor(self) -> Dict[str, int]:
    #     """에디터에서 현재 커서 위치 (줄, 열) 반환"""
    #     pass
    #
    # def get_selected_text(self) -> str:
    #     """현재 선택된 텍스트 반환"""
    #     pass
    #


# ============================================================================
# 🧪 테스트 코드 (직접 실행 시)
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 StatusMonitor 테스트")
    print("=" * 50)
    
    monitor = StatusMonitor()
    
    print("\n📊 현재 상태:")
    status = monitor.get_current_status()
    
    import json
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print("\n📋 열린 창 목록:")
    for i, title in enumerate(monitor.get_all_windows()[:10], 1):
        print(f"   {i}. {title}")
    
    print("\n✅ 테스트 완료")
