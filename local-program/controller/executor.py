# ============================================================================
# 📁 controller/executor.py - 명령 실행 디스패처
# ============================================================================
#
# 🎯 역할:
#   서버에서 받은 EditorCommand를 파싱하고 적절한 핸들러로 디스패치합니다.
#   키맵 파일(YAML)을 로드하여 에디터별 단축키를 관리합니다.
#
# 🔧 주요 기능:
#   - execute: 명령을 받아 적절한 핸들러로 디스패치
#   - get_status: 현재 로컬 상태 반환
#   - 각 명령 타입별 핸들러 메서드들
#
# 📝 멘토님께:
#   execute() 메서드는 실제 디스패치 로직이 구현되어 있습니다.
#   각 핸들러 메서드(_handle_*)는 NotImplementedError를 발생시킵니다.
#   WindowManager와 KeyboardController를 사용하여 핸들러를 구현해 주세요.
#
# ============================================================================

import time
import yaml
from pathlib import Path
from typing import Dict, Any

from models.commands import EditorCommand
from models.status import LocalStatus
from controller.window import WindowManager
from controller.keyboard import KeyboardController


class EditorController:
    """
    🎮 에디터 제어 컨트롤러
    
    서버에서 받은 명령을 파싱하고 실행하는 메인 컨트롤러입니다.
    WindowManager와 KeyboardController를 조합하여 에디터를 제어합니다.
    
    Attributes:
        keymap (Dict[str, Any]): 로드된 키맵 설정
        window_manager (WindowManager): 윈도우 관리 인스턴스
        keyboard_controller (KeyboardController): 키보드 제어 인스턴스
        current_status (str): 현재 상태 ("IDLE" 또는 "BUSY")
    
    Example:
        # 컨트롤러 초기화
        controller = EditorController(keymap_path="keymaps/vscode.yaml")
        
        # 명령 실행
        command = EditorCommand(
            type="hotkey",
            payload={"keys": ["ctrl", "g"]}
        )
        result = controller.execute(command)
        
        # 상태 확인
        status = controller.get_status()
        print(f"현재 상태: {status.status}")
    """
    
    def __init__(self, keymap_path: str = "keymaps/vscode.yaml"):
        """
        🏗️ EditorController 초기화
        
        키맵 파일을 로드하고 WindowManager, KeyboardController를 초기화합니다.
        
        Args:
            keymap_path (str): 키맵 YAML 파일 경로
                기본값: "keymaps/vscode.yaml"
        
        Raises:
            FileNotFoundError: 키맵 파일을 찾을 수 없는 경우
            yaml.YAMLError: 키맵 파일 파싱 실패
        """
        # 키맵 로드
        keymap_file = Path(keymap_path)
        if not keymap_file.exists():
            raise FileNotFoundError(f"키맵 파일을 찾을 수 없습니다: {keymap_path}")
        
        with open(keymap_file, "r", encoding="utf-8") as f:
            self.keymap = yaml.safe_load(f)
        
        # 컨트롤러 초기화
        self.window_manager = WindowManager()
        self.keyboard_controller = KeyboardController()
        
        # 상태 관리
        self.current_status = "IDLE"
        
        print(f"✅ EditorController 초기화 완료")
        print(f"   키맵: {self.keymap.get('editor', 'Unknown')}")
        print(f"   윈도우 패턴: {self.keymap.get('window_title_pattern', 'Unknown')}")
    
    def execute(self, command: EditorCommand) -> Dict[str, Any]:
        """
        🎯 명령 실행 디스패처
        
        EditorCommand를 받아 타입에 따라 적절한 핸들러로 디스패치합니다.
        실행 전후로 상태를 BUSY/IDLE로 변경합니다.
        
        Args:
            command (EditorCommand): 실행할 명령
        
        Returns:
            Dict[str, Any]: 실행 결과
                - success (bool): 성공 여부
                - message (str): 결과 메시지
                - timestamp (float): 실행 시간
        
        Raises:
            ValueError: 알 수 없는 명령 타입
        
        Example:
            controller = EditorController()
            
            # 단축키 명령
            cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "g"]})
            result = controller.execute(cmd)
            
            # 텍스트 입력 명령
            cmd = EditorCommand(type="type_text", payload={"content": "Hello"})
            result = controller.execute(cmd)
        """
        # 상태를 BUSY로 변경
        self.current_status = "BUSY"
        
        try:
            # 명령 타입에 따라 핸들러 디스패치
            match command.type:
                case "focus_window":
                    result = self._handle_focus_window(command.payload)
                
                case "hotkey":
                    result = self._handle_hotkey(command.payload)
                
                case "type_text":
                    result = self._handle_type_text(command.payload)
                
                case "command_palette":
                    result = self._handle_command_palette(command.payload)
                
                case "open_file":
                    result = self._handle_open_file(command.payload)
                
                case "goto_line":
                    result = self._handle_goto_line(command.payload)
                
                case _:
                    raise ValueError(f"알 수 없는 명령 타입: {command.type}")
            
            return result
        
        finally:
            # 상태를 IDLE로 복원
            self.current_status = "IDLE"
    
    def get_status(self) -> LocalStatus:
        """
        📊 현재 로컬 상태 반환
        
        WindowManager를 사용하여 현재 활성 창, 대상 앱 실행 여부 등을
        확인하고 LocalStatus 객체로 반환합니다.
        
        Returns:
            LocalStatus: 현재 로컬 상태
                - active_window: 현재 활성 창 제목
                - target_app_running: 대상 앱 실행 여부
                - status: 현재 상태 (IDLE/BUSY)
                - current_keymap: 현재 키맵 이름
                - timestamp: 현재 시간
        
        Example:
            controller = EditorController()
            status = controller.get_status()
            
            print(f"활성 창: {status.active_window}")
            print(f"VS Code 실행 중: {status.target_app_running}")
            print(f"상태: {status.status}")
        """
        # 현재 활성 창 제목 가져오기
        try:
            active_window = self.window_manager.get_active_window_title()
        except NotImplementedError:
            active_window = "Unknown (구현 필요)"
        
        # 대상 앱 실행 여부 확인
        window_pattern = self.keymap.get("window_title_pattern", "Visual Studio Code")
        try:
            target_app_running = self.window_manager.is_app_running(window_pattern)
        except NotImplementedError:
            target_app_running = False
        
        # LocalStatus 객체 생성
        return LocalStatus(
            active_window=active_window,
            target_app_running=target_app_running,
            status=self.current_status,
            current_keymap=self.keymap.get("editor", "vscode"),
            timestamp=time.time()
        )
    
    # ========================================================================
    # 🔧 명령 핸들러 메서드들 (멘토가 구현할 예정)
    # ========================================================================
    
    def _handle_focus_window(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        🪟 창 포커스 핸들러
        
        Args:
            payload: {"window_title": str}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 WindowManager를 사용하여 구현할 예정입니다")
    
    def _handle_hotkey(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎹 단축키 핸들러
        
        Args:
            payload: {"keys": List[str]}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 KeyboardController를 사용하여 구현할 예정입니다")
    
    def _handle_type_text(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⌨️ 텍스트 입력 핸들러
        
        Args:
            payload: {"content": str}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 KeyboardController를 사용하여 구현할 예정입니다")
    
    def _handle_command_palette(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎨 명령 팔레트 핸들러
        
        Args:
            payload: {"command": str}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 KeyboardController를 사용하여 구현할 예정입니다")
    
    def _handle_open_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        📂 파일 열기 핸들러
        
        Args:
            payload: {"file_path": str}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 KeyboardController를 사용하여 구현할 예정입니다")
    
    def _handle_goto_line(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔢 라인 이동 핸들러
        
        Args:
            payload: {"line_number": int}
        
        Returns:
            실행 결과 딕셔너리
        """
        raise NotImplementedError("멘토가 KeyboardController를 사용하여 구현할 예정입니다")
