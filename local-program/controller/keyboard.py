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
        ⌨️ 텍스트 입력 (클립보드 붙여넣기 방식)

        텍스트를 클립보드에 복사한 뒤 Ctrl+V로 붙여넣습니다.
        keyboard.write()는 문자 하나씩 타이핑하기 때문에
        VS Code 자동 들여쓰기가 줄바꿈마다 작동하여 코드가 망가집니다.
        붙여넣기는 auto-indent를 트리거하지 않으므로 안전합니다.

        Args:
            text (str): 입력할 텍스트
                예: "print('Hello, World!')"

        Note:
            - 영문, 숫자, 특수문자, 한글 모두 지원
            - 여러 줄 코드도 들여쓰기가 보존됨
            - 붙여넣기 후 원래 클립보드 내용은 복원하지 않음

        Example:
            kb = KeyboardController()

            # 코드 입력 (여러 줄도 들여쓰기 정확)
            kb.type_text("def hello():\\n    print('Hello')")
        """
        import os
        import subprocess
        import tempfile

        # 임시 파일에 텍스트 저장 후 PowerShell로 클립보드 복사
        # stdin 파이프는 줄바꿈을 배열로 분리하여 개행이 손실될 수 있음
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", encoding="utf-8", delete=False
            ) as tmp:
                tmp.write(text)
                tmp_path = tmp.name

            # Get-Content -Raw로 파일 전체를 단일 문자열로 읽어서 클립보드에 복사
            ps_cmd = f'Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 "{tmp_path}")'
            process = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if process.returncode != 0:
                raise RuntimeError(f"클립보드 복사 실패: {process.stderr}")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        time.sleep(0.05)

        # Ctrl+V로 붙여넣기
        keyboard.send("ctrl+v")
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
