# ============================================================================
# 📁 controller/keyboard.py - 키보드 제어 모듈
# ============================================================================
#
# 🎯 역할:
#   키보드 입력을 시뮬레이션하여 에디터를 제어합니다.
#   단축키 전송, 텍스트 입력, 명령 팔레트 실행 등을 담당합니다.
#
# 🔧 주요 기능:
#   - send_hotkey: 키보드 단축키 전송 (Ctrl+G 등)
#   - type_text: 텍스트 입력 (특수문자 이스케이핑 포함)
#   - send_command_palette: VS Code 명령 팔레트 실행
#
# 📝 멘토님께:
#   이 모듈은 스캐폴드입니다. 모든 메서드가 NotImplementedError를 발생시킵니다.
#   pywinauto 또는 keyboard 라이브러리를 사용하여 실제 구현을 추가해 주세요.
#
# ============================================================================

from typing import List


class KeyboardController:
    """
    ⌨️ 키보드 제어 클래스
    
    키보드 입력을 시뮬레이션하여 에디터를 제어합니다.
    pywinauto의 type_keys() 또는 keyboard 라이브러리를 사용합니다.
    
    Example:
        kb = KeyboardController()
        
        # Ctrl+G 단축키 전송
        kb.send_hotkey(["ctrl", "g"])
        
        # 텍스트 입력
        kb.type_text("print('Hello, World!')")
        
        # 명령 팔레트에서 "Go to Line" 실행
        kb.send_command_palette("Go to Line")
    """
    
    def __init__(self):
        """
        🏗️ KeyboardController 초기화
        
        키보드 제어에 필요한 설정을 준비합니다.
        타이핑 딜레이, 특수키 매핑 등을 초기화합니다.
        """
        # 멘토가 키보드 제어 초기화 코드를 추가할 예정
        pass
    
    def send_hotkey(self, keys: List[str]) -> None:
        """
        🎹 키보드 단축키 전송
        
        여러 키를 동시에 누르는 단축키를 전송합니다.
        예: Ctrl+G, Ctrl+Shift+P 등
        
        Args:
            keys (List[str]): 단축키 조합
                예: ["ctrl", "g"], ["ctrl", "shift", "p"]
                
        Note:
            키 이름은 소문자로 통일합니다:
            - ctrl, shift, alt, win
            - a-z, 0-9
            - enter, esc, tab, space
            - up, down, left, right
        
        Example:
            kb = KeyboardController()
            
            # Ctrl+G (Go to Line)
            kb.send_hotkey(["ctrl", "g"])
            
            # Ctrl+Shift+P (Command Palette)
            kb.send_hotkey(["ctrl", "shift", "p"])
            
            # Alt+F4 (Close Window)
            kb.send_hotkey(["alt", "f4"])
        """
        raise NotImplementedError("멘토가 pywinauto로 구현할 예정입니다")
    
    def type_text(self, text: str) -> None:
        """
        ⌨️ 텍스트 입력
        
        주어진 텍스트를 키보드로 입력합니다.
        특수문자는 자동으로 이스케이핑됩니다.
        
        Args:
            text (str): 입력할 텍스트
                예: "print('Hello, World!')"
        
        Note:
            특수문자 처리 주의사항:
            - pywinauto의 경우 {}, +, ^, % 등은 이스케이핑 필요
            - 예: "Hello{Enter}" → "Hello{{Enter}}"
            - 한글 입력 시 IME 상태 확인 필요
        
        Example:
            kb = KeyboardController()
            
            # 일반 텍스트 입력
            kb.type_text("Hello, World!")
            
            # 코드 입력 (특수문자 포함)
            kb.type_text("def hello():")
            kb.type_text("    print('Hello')")
            
            # 한글 입력
            kb.type_text("안녕하세요")
        """
        raise NotImplementedError("멘토가 pywinauto로 구현할 예정입니다")
    
    def send_command_palette(self, command: str) -> None:
        """
        🎨 VS Code 명령 팔레트 실행
        
        Ctrl+Shift+P를 눌러 명령 팔레트를 열고
        주어진 명령을 입력하여 실행합니다.
        
        Args:
            command (str): 실행할 명령어
                예: "Go to Line", "Format Document"
        
        Implementation:
            1. Ctrl+Shift+P 전송 (명령 팔레트 열기)
            2. 짧은 딜레이 (팔레트가 열릴 때까지 대기)
            3. 명령어 입력
            4. Enter 전송 (명령 실행)
        
        Example:
            kb = KeyboardController()
            
            # Go to Line 명령 실행
            kb.send_command_palette("Go to Line")
            
            # Format Document 명령 실행
            kb.send_command_palette("Format Document")
            
            # Toggle Terminal 명령 실행
            kb.send_command_palette("Toggle Terminal")
        """
        raise NotImplementedError("멘토가 pywinauto로 구현할 예정입니다")
