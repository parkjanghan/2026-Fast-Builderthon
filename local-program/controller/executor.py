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
from pathlib import Path
from typing import Any

import yaml

from controller.keyboard import KeyboardController
from controller.window import WindowManager
from models.commands import EditorCommand
from models.status import LocalStatus


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

        with open(keymap_file, encoding="utf-8") as f:
            self.keymap = yaml.safe_load(f)

        # 컨트롤러 초기화
        self.window_manager = WindowManager()
        self.keyboard_controller = KeyboardController()

        # 상태 관리
        self.current_status = "IDLE"

        print("✅ EditorController 초기화 완료")
        print(f"   키맵: {self.keymap.get('editor', 'Unknown')}")
        print(f"   윈도우 패턴: {self.keymap.get('window_title_pattern', 'Unknown')}")

    def execute(self, command: EditorCommand) -> dict[str, Any]:
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
            timestamp=time.time(),
        )

    # ========================================================================
    # 🔧 명령 핸들러 메서드들 (멘토가 구현할 예정)
    # ========================================================================

    def _handle_focus_window(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        🪟 창 포커스 핸들러 (자동 실행 + 프로젝트 매칭 지원)

        앱이 꺼져있으면 자동 실행하고, 다중 창이면 프로젝트명으로 선택합니다.

        Args:
            payload: {"window_title": str, "project_hint": str (선택)}

        Returns:
            실행 결과 딕셔너리

        Example:
            # 기본 사용
            result = controller._handle_focus_window({"window_title": "Visual Studio Code"})

            # 프로젝트 힌트 + 자동 실행
            result = controller._handle_focus_window({
                "window_title": "Visual Studio Code",
                "project_hint": "my-project"
            })
        """
        window_title = payload.get("window_title", "")
        project_hint = payload.get("project_hint", "")

        # config에서 자동 실행 설정 가져오기
        try:
            from config import APP_LAUNCH_POLL_INTERVAL, APP_LAUNCH_TIMEOUT, AUTO_LAUNCH_ENABLED
        except ImportError:
            AUTO_LAUNCH_ENABLED = True
            APP_LAUNCH_TIMEOUT = 15
            APP_LAUNCH_POLL_INTERVAL = 0.5

        # ensure_window: 찾기 → 없으면 실행 → 포커스
        success = self.window_manager.ensure_window(
            window_title,
            project_hint=project_hint,
            auto_launch=AUTO_LAUNCH_ENABLED,
            timeout=APP_LAUNCH_TIMEOUT,
            poll_interval=APP_LAUNCH_POLL_INTERVAL,
        )
        return {
            "success": success,
            "message": f"✅ 창 포커스 완료: {window_title}"
            if success
            else f"❌ 창 포커스 실패: {window_title}",
            "timestamp": time.time(),
        }

    def _handle_hotkey(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        🎹 단축키 핸들러

        Args:
            payload: {"keys": List[str]}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_hotkey({"keys": ["ctrl", "g"]})
        """
        keys = payload.get("keys", [])
        try:
            self.keyboard_controller.send_hotkey(keys)
            combo = "+".join(keys)
            return {
                "success": True,
                "message": f"✅ 단축키 전송 완료: {combo}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 단축키 전송 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_type_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        ⌨️ 텍스트 입력 핸들러

        Args:
            payload: {"content": str}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_type_text({"content": "print('hello')"})
        """
        content = payload.get("content", "")
        try:
            self.keyboard_controller.type_text(content)
            preview = content[:30] + "..." if len(content) > 30 else content
            return {
                "success": True,
                "message": f"✅ 텍스트 입력 완료: {preview}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 텍스트 입력 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_command_palette(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        🎨 명령 팔레트 핸들러

        Args:
            payload: {"command": str}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_command_palette({"command": "Format Document"})
        """
        command = payload.get("command", "")
        try:
            self.keyboard_controller.send_command_palette(command)
            return {
                "success": True,
                "message": f"✅ 명령 팔레트 실행 완료: {command}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 명령 팔레트 실행 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_open_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        📂 파일 열기 핸들러

        Ctrl+O → 딜레이 → 파일 경로 입력 → Enter로 파일을 엽니다.

        Args:
            payload: {"file_path": str}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_open_file({"file_path": "C:/project/main.py"})
        """
        import keyboard as kb

        file_path = payload.get("file_path", "")
        try:
            # Ctrl+O로 파일 열기 다이얼로그
            self.keyboard_controller.send_hotkey(["ctrl", "o"])
            time.sleep(0.5)

            # 파일 경로 입력
            self.keyboard_controller.type_text(file_path)
            time.sleep(0.2)

            # Enter로 열기
            kb.send("enter")
            time.sleep(0.3)

            return {
                "success": True,
                "message": f"✅ 파일 열기 완료: {file_path}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 파일 열기 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_goto_line(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        🔢 라인 이동 핸들러

        키맵에서 goto_line 단축키를 로드하여 실행합니다.
        Ctrl+G → 딜레이 → 라인 번호 입력 → Enter

        Args:
            payload: {"line_number": int}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_goto_line({"line_number": 42})
        """
        import keyboard as kb

        line_number = payload.get("line_number", 1)
        try:
            # 키맵에서 goto_line 단축키 가져오기
            goto_keys = self.keymap.get("shortcuts", {}).get("goto_line", ["ctrl", "g"])
            self.keyboard_controller.send_hotkey(goto_keys)
            time.sleep(0.3)

            # 라인 번호 입력
            self.keyboard_controller.type_text(str(line_number))
            time.sleep(0.1)

            # Enter로 이동
            kb.send("enter")
            time.sleep(0.1)

            return {
                "success": True,
                "message": f"✅ 라인 이동 완료: {line_number}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 라인 이동 실패: {e}",
                "timestamp": time.time(),
            }
