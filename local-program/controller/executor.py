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
            # 📋 편집 명령이면 올바른 파일에서 작업하는지 사전 검증
            editing_commands = {"hotkey", "type_text", "goto_line", "save_file", "command_palette"}
            if command.type in editing_commands and command.target_file:
                self._ensure_correct_file(command.target_file, command.expected_content)

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

                case "open_folder":
                    result = self._handle_open_folder(command.payload)

                case "save_file":
                    result = self._handle_save_file(command.payload)

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
    # 🧹 다이얼로그 정리
    # ========================================================================

    def _dismiss_stale_dialogs(self) -> None:
        """
        🧹 잔여 다이얼로그/모달 정리 (모든 명령 실행 전 호출)

        이전 명령에서 Save As, 확인 다이얼로그 등이 닫히지 않고 남아있으면
        이후 키보드 입력이 다이얼로그에 빠져 전체 시퀀스가 망가집니다.
        활성 창 제목을 확인하여 다이얼로그가 감지되면 Esc로 닫습니다.

        Example:
            # execute() 시작 시 자동 호출됨
            self._dismiss_stale_dialogs()
        """
        import keyboard as kb

        try:
            active = self.window_manager.get_active_window_title()
            if not active:
                return

            # 알려진 다이얼로그 키워드 목록
            dialog_keywords = [
                "Save As",
                "다른 이름으로 저장",
                "확인",
                "Confirm",
                "열기",
                "Open",
                "파일 이름이 올바르지",
            ]
            if any(kw in active for kw in dialog_keywords):
                print(f"⚠️ 잔여 다이얼로그 감지: '{active}'")
                for _ in range(5):
                    kb.send("escape")
                    time.sleep(0.2)
                time.sleep(0.3)
                print("✅ 다이얼로그 정리 완료")
        except Exception:
            pass

    # ========================================================================
    # 🎯 편집 전 파일 컨텍스트 검증
    # ========================================================================

    def _ensure_correct_file(self, target_file: str, expected_content: str | None = None) -> None:
        """
        📋 편집 명령 실행 전 올바른 워크스페이스 + 파일이 열려있는지 + 내용 검증

        검증 순서:
          1. VS Code가 활성 창인지 확인 → 아니면 포커스/실행
          2. 워크스페이스가 올바른지 타이틀로 확인 → 아니면 폴더 열기
          3. 대상 파일이 열려있는지 확인 → 아니면 code CLI로 파일 열기
          4. expected_content가 있으면 로컬 파일 내용과 비교 → 불일치 시 덮어쓰기

        VS Code 타이틀 형식:
          "filename - project_folder - Visual Studio Code"
          "● filename - project_folder - Visual Studio Code" (수정됨)
          "Welcome - Visual Studio Code" (워크스페이스 없음)

        Args:
            target_file (str): 편집 대상 파일명 (예: "main.py", "practice.py")
            expected_content (str | None): 화면에 보이는 파일 내용 (검증용, None이면 스킵)

        Example:
            self._ensure_correct_file("practice.py", "print('hello')")
        """
        if not target_file:
            return

        import os
        import subprocess

        try:
            target_name = os.path.basename(target_file)

            # config에서 프로젝트 경로 가져오기
            project_path = ""
            try:
                from config import TARGET_PROJECT_PATH

                project_path = TARGET_PROJECT_PATH
            except (ImportError, AttributeError):
                pass

            # VS Code exe 경로
            exe_path = ""
            try:
                from config import VSCODE_EXE_PATH

                exe_path = VSCODE_EXE_PATH
            except (ImportError, AttributeError):
                pass

            # ----------------------------------------------------------------
            # 1단계: VS Code가 활성 창인지 확인
            # ----------------------------------------------------------------
            active_title = self.window_manager.get_active_window_title() or ""

            if "Visual Studio Code" not in active_title:
                print(f"⚠️ VS Code가 활성 창이 아닙니다: '{active_title}'")
                # 워크스페이스로 VS Code 열기 시도
                if project_path and exe_path and os.path.exists(exe_path):
                    print(f"🚀 VS Code를 워크스페이스와 함께 실행: {project_path}")
                    subprocess.Popen([exe_path, project_path])
                    # 창이 뜰 때까지 대기
                    for _ in range(30):
                        time.sleep(0.5)
                        if self.window_manager.focus_window(
                            "Visual Studio Code", project_hint=os.path.basename(project_path)
                        ):
                            break
                    time.sleep(1.0)
                else:
                    self.window_manager.ensure_window("Visual Studio Code", auto_launch=True)
                    time.sleep(1.0)

                active_title = self.window_manager.get_active_window_title() or ""

            # ----------------------------------------------------------------
            # 2단계: 워크스페이스가 올바른지 확인
            # ----------------------------------------------------------------
            if project_path:
                project_name = os.path.basename(project_path)

                # 타이틀에 프로젝트명이 없으면 → Welcome 탭이거나 다른 워크스페이스
                if project_name.lower() not in active_title.lower():
                    print(f"⚠️ 워크스페이스 불일치: '{active_title}' (기대: {project_name})")
                    print(f"📂 올바른 워크스페이스를 열고 있습니다: {project_path}")

                    # code CLI로 폴더 열기 (--reuse-window로 현재 창에서)
                    if exe_path and os.path.exists(exe_path):
                        subprocess.Popen([exe_path, project_path])
                    else:
                        subprocess.Popen(f'code "{project_path}"', shell=True)

                    # 워크스페이스가 로드될 때까지 대기
                    for _ in range(30):
                        time.sleep(0.5)
                        title = self.window_manager.get_active_window_title() or ""
                        if project_name.lower() in title.lower():
                            print(f"✅ 워크스페이스 로드 완료: {project_name}")
                            break
                    else:
                        print("⚠️ 워크스페이스 로드 타임아웃 (계속 진행)")

                    time.sleep(1.5)  # VS Code가 완전히 로드될 시간
                    active_title = self.window_manager.get_active_window_title() or ""

            # ----------------------------------------------------------------
            # 3단계: 대상 파일이 열려있는지 확인
            # ----------------------------------------------------------------
            # 타이틀에서 현재 파일명 추출
            current_file = active_title.split(" - ")[0].strip()
            current_file = current_file.lstrip("● ").strip()

            if current_file.lower() == target_name.lower():
                print(f"✅ 올바른 파일에서 작업 중: {target_name}")
                # 파일명은 같지만 내용이 다를 수 있으므로 검증
                if expected_content and project_path:
                    file_path = os.path.join(project_path, target_name)
                    self._verify_file_content(file_path, expected_content)
                return

            print(f"⚠️ 파일 불일치: 현재='{current_file}', 대상='{target_name}'")

            # code CLI로 파일 직접 열기 (Quick Open보다 안정적)
            if project_path and exe_path and os.path.exists(exe_path):
                # 파일이 없으면 빈 파일 생성
                full_path = os.path.join(project_path, target_name)
                if not os.path.exists(full_path):
                    print(f"📄 파일이 없어서 새로 생성: {full_path}")
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write("")

                print(f"📂 code CLI로 파일 열기: {full_path}")
                subprocess.Popen([exe_path, "--reuse-window", full_path])
            else:
                # exe가 없으면 code CLI 시도
                full_path = os.path.join(project_path, target_name) if project_path else target_name
                if project_path and not os.path.exists(full_path):
                    os.makedirs(
                        os.path.dirname(full_path) if os.path.dirname(full_path) else project_path,
                        exist_ok=True,
                    )
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write("")
                subprocess.Popen(f'code --reuse-window "{full_path}"', shell=True)

            # 파일이 열릴 때까지 대기 + 확인
            for _ in range(20):
                time.sleep(0.5)
                title = self.window_manager.get_active_window_title() or ""
                opened_file = title.split(" - ")[0].strip().lstrip("● ").strip()
                if opened_file.lower() == target_name.lower():
                    print(f"✅ 파일 열기 완료: {target_name}")
                    # 포커스 확실히 맞추기
                    self.window_manager.focus_window("Visual Studio Code")
                    time.sleep(0.3)
                    # 새로 연 파일 내용 검증
                    if expected_content and project_path:
                        file_path = os.path.join(project_path, target_name)
                        self._verify_file_content(file_path, expected_content)
                    return

            print(f"⚠️ 파일 열기 타임아웃: {target_name} (계속 진행)")

            # ----------------------------------------------------------------
            # 4단계: 파일 내용 검증 (expected_content가 있는 경우)
            # ----------------------------------------------------------------
            if expected_content and project_path:
                file_path = os.path.join(project_path, target_name)
                self._verify_file_content(file_path, expected_content)

        except Exception as e:
            print(f"⚠️ 파일 컨텍스트 검증 실패 (계속 진행): {e}")

    # ========================================================================
    # 🔍 파일 내용 검증
    # ========================================================================

    def _verify_file_content(self, file_path: str, expected_content: str) -> None:
        """
        🔍 로컬 파일 내용과 서버가 보낸 expected_content를 비교

        화면에서 AI가 읽은 내용(부분일 수 있음)이 로컬 파일에 포함되어 있는지 확인.
        불일치 시 로컬 파일을 expected_content로 덮어씁니다.

        Args:
            file_path (str): 검증할 파일의 절대 경로
            expected_content (str): 서버가 보낸 화면 속 파일 내용

        Example:
            self._verify_file_content("C:/project/main.py", "print('hello')")
        """
        import os

        if not expected_content or not expected_content.strip():
            return

        try:
            # 파일이 존재하지 않으면 expected_content로 생성
            if not os.path.exists(file_path):
                print(f"📄 파일이 없어서 expected_content로 생성: {file_path}")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(expected_content)
                return

            # 현재 파일 내용 읽기
            with open(file_path, encoding="utf-8") as f:
                local_content = f.read()

            # 비교: expected_content가 로컬 파일에 포함되어 있는지 확인
            # (AI는 화면에 보이는 부분만 보내므로 부분 일치도 OK)
            expected_stripped = expected_content.strip()
            local_stripped = local_content.strip()

            if not local_stripped:
                # 빈 파일이면 expected_content로 채우기
                print(f"📝 빈 파일에 expected_content 작성: {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(expected_content)
                return

            if expected_stripped in local_stripped:
                print(f"✅ 파일 내용 일치 확인: {os.path.basename(file_path)}")
                return

            # 줄 단위 비교 — expected의 줄들이 local에 몇 % 포함되는지
            expected_lines = [ln.strip() for ln in expected_stripped.splitlines() if ln.strip()]
            local_lines_set = {ln.strip() for ln in local_stripped.splitlines() if ln.strip()}

            if not expected_lines:
                return

            match_count = sum(1 for ln in expected_lines if ln in local_lines_set)
            match_ratio = match_count / len(expected_lines)

            if match_ratio >= 0.5:
                # 50% 이상 일치하면 같은 파일로 간주
                print(f"✅ 파일 내용 부분 일치 ({match_ratio:.0%}): {os.path.basename(file_path)}")
                return

            # 불일치: 다른 내용의 파일 → expected_content로 덮어쓰기
            print(f"⚠️ 파일 내용 불일치 ({match_ratio:.0%}): {os.path.basename(file_path)}")
            print(f"   로컬 {len(local_stripped)}자 vs 서버 {len(expected_stripped)}자")
            print(f"📝 서버의 expected_content로 파일 덮어쓰기: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(expected_content)
            print(f"✅ 파일 내용 동기화 완료: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"⚠️ 파일 내용 검증 실패 (계속 진행): {e}")

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

        # 🔄 폴백: 요청한 창을 못 찾으면 VS Code를 새로 열어서 포커스
        if not success:
            print(f"⚠️ '{window_title}' 창을 찾지 못했습니다. VS Code를 새로 실행합니다...")
            fallback_name = "Visual Studio Code"
            success = self.window_manager.ensure_window(
                fallback_name,
                project_hint=project_hint,
                auto_launch=True,
                timeout=APP_LAUNCH_TIMEOUT,
                poll_interval=APP_LAUNCH_POLL_INTERVAL,
            )
            if success:
                window_title = f"{window_title} → VS Code (폴백)"

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

        VS Code CLI (`code <filepath>`) 또는 exe로 파일을 직접 엽니다.
        네이티브 파일 다이얼로그를 사용하지 않아 안정적입니다.
        열기 후 해당 창에 포커스합니다.

        Args:
            payload: {"file_path": str}

        Returns:
            실행 결과 딕셔너리

        Example:
            result = controller._handle_open_file({"file_path": "C:/project/main.py"})
        """
        import os
        import subprocess

        file_path = payload.get("file_path", "")
        try:
            # VS Code exe 경로 가져오기
            exe_path = ""
            try:
                from config import VSCODE_EXE_PATH

                exe_path = VSCODE_EXE_PATH
            except (ImportError, AttributeError):
                pass

            # VS Code로 파일 열기 (--reuse-window로 기존 창에서 열기)
            if exe_path and os.path.exists(exe_path):
                subprocess.Popen([exe_path, "--reuse-window", file_path])
            else:
                subprocess.Popen(f'code --reuse-window "{file_path}"', shell=True)

            time.sleep(1.0)

            # 열린 파일의 VS Code 창에 포커스
            file_name = os.path.basename(file_path)
            self.window_manager.focus_window("Visual Studio Code", project_hint=file_name)
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
        🔢 라인(+컬럼) 이동 핸들러

        키맵에서 goto_line 단축키를 로드하여 실행합니다.
        VS Code의 Ctrl+G는 "줄:열" 형식을 지원합니다.
        - column 없음: Ctrl+G → "42" → Enter (라인만 이동)
        - column 있음: Ctrl+G → "42:23" → Enter (라인+컬럼 이동)

        Args:
            payload: {"line_number": int, "column": int (선택)}

        Returns:
            실행 결과 딕셔너리

        Example:
            # 라인만 이동
            result = controller._handle_goto_line({"line_number": 42})

            # 라인 + 컬럼 이동
            result = controller._handle_goto_line({"line_number": 3, "column": 23})
        """
        import keyboard as kb

        line_number = payload.get("line_number", 1)
        column = payload.get("column")
        try:
            # 키맵에서 goto_line 단축키 가져오기
            goto_keys = self.keymap.get("shortcuts", {}).get("goto_line", ["ctrl", "g"])
            self.keyboard_controller.send_hotkey(goto_keys)
            time.sleep(0.3)

            # "줄:열" 또는 "줄" 형식으로 입력
            goto_text = f"{line_number}:{column}" if column is not None else str(line_number)
            self.keyboard_controller.type_text(goto_text)
            time.sleep(0.1)

            # Enter로 이동
            kb.send("enter")
            time.sleep(0.1)

            return {
                "success": True,
                "message": f"✅ 라인 이동 완료: {goto_text}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 라인 이동 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_open_folder(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        📁 폴더 열기 핸들러 (워크스페이스)

        폴더가 없으면 생성하고, VS Code에서 워크스페이스로 엽니다.
        `code <folder_path>` CLI 또는 exe 직접 실행으로 동작합니다.

        Args:
            payload: {"folder_path": str, "new_window": bool (선택, 기본 False)}

        Returns:
            실행 결과 딕셔너리

        Example:
            # 폴더를 워크스페이스로 열기
            result = controller._handle_open_folder({
                "folder_path": "C:/Users/student/Desktop/PythonWorkspace"
            })

            # 새 창에서 열기
            result = controller._handle_open_folder({
                "folder_path": "C:/project",
                "new_window": True
            })
        """
        import os
        import subprocess

        folder_path = payload.get("folder_path", "")
        new_window = payload.get("new_window", False)
        try:
            # 폴더가 없으면 생성
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"📁 폴더 생성: {folder_path}")

            # VS Code exe 경로 가져오기
            exe_path = ""
            try:
                from config import VSCODE_EXE_PATH

                exe_path = VSCODE_EXE_PATH
            except (ImportError, AttributeError):
                pass

            # exe 경로로 실행
            if exe_path and os.path.exists(exe_path):
                cmd = [exe_path]
                if new_window:
                    cmd.append("--new-window")
                cmd.append(folder_path)
                subprocess.Popen(cmd)
            else:
                # code CLI로 실행
                cmd_str = "code"
                if new_window:
                    cmd_str += " --new-window"
                cmd_str += f' "{folder_path}"'
                subprocess.Popen(cmd_str, shell=True)

            # ensure_window로 창이 뜰 때까지 polling + 포커스
            folder_name = os.path.basename(folder_path)
            try:
                from config import APP_LAUNCH_POLL_INTERVAL, APP_LAUNCH_TIMEOUT
            except (ImportError, AttributeError):
                APP_LAUNCH_TIMEOUT = 15
                APP_LAUNCH_POLL_INTERVAL = 0.5

            # 이미 실행 명령을 보냈으니 launch 없이 polling만
            deadline = time.time() + APP_LAUNCH_TIMEOUT
            focused = False
            while time.time() < deadline:
                try:
                    focused = self.window_manager.focus_window(
                        "Visual Studio Code", project_hint=folder_name
                    )
                    if focused:
                        break
                except Exception:
                    pass
                time.sleep(APP_LAUNCH_POLL_INTERVAL)

            if not focused:
                return {
                    "success": False,
                    "message": f"❌ 폴더 열기 후 창 포커스 실패: {folder_path}",
                    "timestamp": time.time(),
                }

            # VS Code가 워크스페이스를 완전히 로드할 때까지 추가 대기
            time.sleep(1.5)

            return {
                "success": True,
                "message": f"✅ 폴더 열기 완료: {folder_path}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 폴더 열기 실패: {e}",
                "timestamp": time.time(),
            }

    def _handle_save_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        💾 파일 저장 핸들러

        file_name이 주어지면 Ctrl+Shift+S (다른 이름으로 저장) → 절대 경로 입력 → Enter.
        file_name이 없으면 Ctrl+S (현재 파일 저장).

        절대 경로 전략:
          - folder_path + file_name → 절대 경로 조합
          - folder_path 없이 file_name만 → 파일명만 입력 (기본 경로에 저장)
          - 네이티브 Save As 다이얼로그의 파일명 필드를 Ctrl+A로 전체 선택 후 덮어쓰기

        Args:
            payload: {"file_name": str | None, "folder_path": str | None}

        Returns:
            실행 결과 딕셔너리

        Example:
            # 현재 파일 저장
            result = controller._handle_save_file({"file_name": None})

            # 절대 경로로 저장
            result = controller._handle_save_file({
                "file_name": "practice.py",
                "folder_path": "C:/Users/student/Desktop/PythonWorkspace"
            })
        """
        import os

        import keyboard as kb

        file_name = payload.get("file_name")
        folder_path = payload.get("folder_path")
        try:
            if file_name:
                # 절대 경로 조합
                save_path = os.path.join(folder_path, file_name) if folder_path else file_name

                # ⚠️ 파일이 이미 존재하면 덮어쓰기 확인 다이얼로그가 뜸
                file_already_exists = os.path.exists(save_path)

                # 다른 이름으로 저장: Ctrl+Shift+S
                self.keyboard_controller.send_hotkey(["ctrl", "shift", "s"])
                time.sleep(1.5)

                # 파일명 필드를 전체 선택 후 절대 경로로 덮어쓰기
                kb.send("ctrl+a")
                time.sleep(0.1)
                self.keyboard_controller.type_text(save_path)
                time.sleep(0.3)

                # Enter로 저장
                kb.send("enter")

                if file_already_exists:
                    # 기존 파일 → 덮어쓰기 확인 다이얼로그 반복 시도
                    # Enter, Tab+Enter, Alt+Y 순서로 시도하며 다이얼로그가 닫힐 때까지 반복
                    for attempt, key_combo in enumerate(
                        ["enter", "left+enter", "alt+y", "enter", "escape"], start=1
                    ):
                        time.sleep(0.7)
                        active = self.window_manager.get_active_window_title()
                        # VS Code 에디터로 돌아왔으면 성공
                        if active and "Visual Studio Code" in active:
                            print(f"✅ 덮어쓰기 확인 완료 (시도 {attempt})")
                            break
                        # 아직 다이얼로그 → 키 전송
                        kb.send(key_combo)
                        print(f"🔄 덮어쓰기 시도 {attempt}: {key_combo} (활성: '{active}')")

                time.sleep(1.0)

                return {
                    "success": True,
                    "message": f"✅ 파일 저장 완료: {save_path}",
                    "timestamp": time.time(),
                }
            else:
                # 현재 파일 저장: Ctrl+S
                save_keys = self.keymap.get("shortcuts", {}).get("save", ["ctrl", "s"])
                self.keyboard_controller.send_hotkey(save_keys)
                time.sleep(0.3)
                return {
                    "success": True,
                    "message": "✅ 파일 저장 완료",
                    "timestamp": time.time(),
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 파일 저장 실패: {e}",
                "timestamp": time.time(),
            }
