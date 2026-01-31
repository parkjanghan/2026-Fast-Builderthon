# ============================================================================
# 📁 controller/keyboard.py - 키보드 제어 모듈
# ============================================================================
#
# 🎯 역할:
#   키보드 입력을 시뮬레이션하여 에디터를 제어합니다.
#   단축키 전송, 텍스트 입력, 명령 팔레트 실행 등을 담당합니다.
#
# 🔧 구현 전략:
#   - 단축키: keyboard 라이브러리의 send() 사용
#   - 텍스트 입력: keyboard 라이브러리의 write() 사용
#     (pywinauto의 type_keys()는 특수문자 이스케이핑 이슈가 있음)
#   - 명령 팔레트: send_hotkey → 딜레이 → type_text → Enter
#
# ⚠️ 주의사항:
#   - keyboard 라이브러리는 관리자 권한이 필요할 수 있습니다
#   - write()는 한글 입력을 지원하지 않습니다 (영문/특수문자만)
#   - send()의 키 이름: ctrl, shift, alt, enter, esc, tab, space 등
#
# ============================================================================

import time

import keyboard

# -------------------------------------------------------------------------
# 🔧 기본 딜레이 설정
# -------------------------------------------------------------------------

# 단축키 전송 후 대기 시간 (초)
HOTKEY_DELAY = 0.1

# 명령 팔레트 열린 후 대기 시간 (초)
PALETTE_OPEN_DELAY = 0.3

# 텍스트 입력 후 대기 시간 (초)
TYPE_DELAY = 0.05


class KeyboardController:
    """
    ⌨️ 키보드 제어 클래스

    keyboard 라이브러리를 사용하여 키보드 입력을 시뮬레이션합니다.
    Electron 앱(VS Code)에서도 안정적으로 동작합니다.

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

        keyboard 라이브러리는 별도 초기화가 필요 없습니다.
        """
        pass

    def send_hotkey(self, keys: list[str]) -> None:
        """
        🎹 키보드 단축키 전송

        여러 키를 동시에 누르는 단축키를 전송합니다.
        keyboard.send()를 사용하여 "+" 구분자로 조합합니다.

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
        """
        combo = "+".join(keys)
        keyboard.send(combo)
        time.sleep(HOTKEY_DELAY)

    def type_text(self, text: str) -> None:
        """
        ⌨️ 텍스트 입력

        keyboard.write()를 사용하여 텍스트를 입력합니다.
        pywinauto의 type_keys()와 달리 특수문자 이스케이핑이 불필요합니다.

        Args:
            text (str): 입력할 텍스트
                예: "print('Hello, World!')"

        Note:
            - 영문, 숫자, 특수문자 모두 지원
            - 한글은 keyboard.write()로 직접 지원되지 않음
            - delay 파라미터로 타이핑 속도 조절 가능

        Example:
            kb = KeyboardController()

            # 코드 입력 (특수문자 포함)
            kb.type_text("def hello():")
            kb.type_text("    print('Hello')")
        """
        keyboard.write(text, delay=TYPE_DELAY)
        time.sleep(HOTKEY_DELAY)

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
        """
        # 1. 명령 팔레트 열기
        self.send_hotkey(["ctrl", "shift", "p"])
        time.sleep(PALETTE_OPEN_DELAY)

        # 2. 명령어 입력
        self.type_text(command)
        time.sleep(PALETTE_OPEN_DELAY)

        # 3. 실행 (Enter)
        keyboard.send("enter")
        time.sleep(HOTKEY_DELAY)
