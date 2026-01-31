# ============================================================================
# 📁 tests/test_edge_cases.py - 예외 상황 테스트
# ============================================================================
#
# 🎯 역할:
#   앱 미실행, 다중 창, 자동 실행 등 예외 상황을 테스트합니다.
#
# 시나리오:
#   - 앱이 꺼져있을 때 ensure_window 동작
#   - 다중 VS Code 창에서 프로젝트명 매칭
#   - 자동 실행 비활성화
#   - code 명령어 없을 때 에러 처리
#   - _select_best_title 로직
#
# ============================================================================

from unittest.mock import MagicMock, patch

# -------------------------------------------------------------------------
# 🎯 _select_best_title 테스트
# -------------------------------------------------------------------------


class TestSelectBestTitle:
    """다중 창에서 최적 제목 선택 로직"""

    def test_single_title_returns_it(self):
        from controller.window import _select_best_title

        result = _select_best_title(["main.py - Visual Studio Code"], "")
        assert result == "main.py - Visual Studio Code"

    def test_project_hint_matches(self):
        from controller.window import _select_best_title

        titles = [
            "app.py - other-project - Visual Studio Code",
            "main.py - my-project - Visual Studio Code",
        ]
        result = _select_best_title(titles, "my-project")
        assert "my-project" in result

    def test_project_hint_case_insensitive(self):
        from controller.window import _select_best_title

        titles = [
            "app.py - Other-Project - Visual Studio Code",
            "main.py - My-Project - Visual Studio Code",
        ]
        result = _select_best_title(titles, "my-project")
        assert "My-Project" in result

    def test_no_hint_returns_first(self):
        from controller.window import _select_best_title

        titles = [
            "first.py - Visual Studio Code",
            "second.py - Visual Studio Code",
        ]
        result = _select_best_title(titles, "")
        assert result == "first.py - Visual Studio Code"

    def test_hint_no_match_returns_first(self):
        from controller.window import _select_best_title

        titles = [
            "first.py - Visual Studio Code",
            "second.py - Visual Studio Code",
        ]
        result = _select_best_title(titles, "nonexistent-project")
        assert result == "first.py - Visual Studio Code"


# -------------------------------------------------------------------------
# 🎯 앱 감지 유틸리티 테스트
# -------------------------------------------------------------------------


class TestAppDetection:
    """_is_vscode, _is_notepad 헬퍼 함수"""

    def test_is_vscode_various(self):
        from controller.window import _is_vscode

        assert _is_vscode("Visual Studio Code") is True
        assert _is_vscode("vscode") is True
        assert _is_vscode("VS Code") is True
        assert _is_vscode("Notepad") is False

    def test_is_notepad_various(self):
        from controller.window import _is_notepad

        assert _is_notepad("메모장") is True
        assert _is_notepad("Notepad") is True
        assert _is_notepad("Visual Studio Code") is False


# -------------------------------------------------------------------------
# 🎯 ensure_window 테스트
# -------------------------------------------------------------------------


class TestEnsureWindow:
    """ensure_window 통합 로직 테스트"""

    def test_already_running_skips_launch(self, keymap_path):
        """이미 실행 중이면 launch 없이 포커스"""
        from controller.window import WindowManager

        wm = WindowManager()
        wm.focus_window = MagicMock(return_value=True)
        wm.launch_app = MagicMock()

        result = wm.ensure_window("Visual Studio Code")
        assert result is True
        wm.focus_window.assert_called_once()
        wm.launch_app.assert_not_called()

    def test_not_running_launches_and_waits(self, keymap_path):
        """꺼져있으면 launch 후 polling으로 포커스"""
        from controller.window import WindowManager

        wm = WindowManager()
        # 첫 번째 focus_window: False (앱 없음)
        # 두 번째: True (앱 실행됨)
        wm.focus_window = MagicMock(side_effect=[False, True])
        wm.launch_app = MagicMock(return_value=True)

        result = wm.ensure_window("Visual Studio Code", timeout=2, poll_interval=0.1)
        assert result is True
        wm.launch_app.assert_called_once()

    def test_auto_launch_disabled(self, keymap_path):
        """auto_launch=False면 실행 안 함"""
        from controller.window import WindowManager

        wm = WindowManager()
        wm.focus_window = MagicMock(return_value=False)
        wm.launch_app = MagicMock()

        result = wm.ensure_window("Visual Studio Code", auto_launch=False)
        assert result is False
        wm.launch_app.assert_not_called()

    def test_launch_fails(self, keymap_path):
        """launch_app 실패 시 False 반환"""
        from controller.window import WindowManager

        wm = WindowManager()
        wm.focus_window = MagicMock(return_value=False)
        wm.launch_app = MagicMock(return_value=False)

        result = wm.ensure_window("Visual Studio Code", timeout=1)
        assert result is False

    def test_timeout_exceeded(self, keymap_path):
        """launch 성공했지만 창이 안 뜨면 타임아웃"""
        from controller.window import WindowManager

        wm = WindowManager()
        wm.focus_window = MagicMock(return_value=False)
        wm.launch_app = MagicMock(return_value=True)

        result = wm.ensure_window("Visual Studio Code", timeout=0.3, poll_interval=0.1)
        assert result is False

    def test_project_hint_passed_through(self, keymap_path):
        """project_hint가 focus_window로 전달되는지 확인"""
        from controller.window import WindowManager

        wm = WindowManager()
        wm.focus_window = MagicMock(return_value=True)

        wm.ensure_window("Visual Studio Code", project_hint="my-project")
        wm.focus_window.assert_called_with("Visual Studio Code", project_hint="my-project")


# -------------------------------------------------------------------------
# 🎯 launch_app 테스트
# -------------------------------------------------------------------------


class TestLaunchApp:
    """launch_app 앱별 분기 테스트"""

    @patch("controller.window._launch_vscode", return_value=True)
    def test_vscode_detected(self, mock_launch, keymap_path):
        from controller.window import WindowManager

        wm = WindowManager()
        result = wm.launch_app("Visual Studio Code", project_hint="C:/project")
        assert result is True
        mock_launch.assert_called_once_with("C:/project")

    @patch("subprocess.Popen")
    def test_notepad_detected(self, mock_popen, keymap_path):
        from controller.window import WindowManager

        wm = WindowManager()
        result = wm.launch_app("메모장")
        assert result is True
        mock_popen.assert_called_once_with(["notepad.exe"])

    def test_unknown_app_fails(self, keymap_path):
        from controller.window import WindowManager

        wm = WindowManager()
        result = wm.launch_app("Unknown App 12345")
        assert result is False

    @patch("subprocess.Popen")
    def test_custom_launch_cmd(self, mock_popen, keymap_path):
        from controller.window import WindowManager

        wm = WindowManager()
        result = wm.launch_app("MyApp", launch_cmd="myapp.exe --flag")
        assert result is True
        mock_popen.assert_called_once_with("myapp.exe --flag", shell=True)


# -------------------------------------------------------------------------
# 🎯 executor _handle_focus_window + ensure_window 연동
# -------------------------------------------------------------------------


class TestExecutorFocusWindowEdgeCases:
    """executor가 ensure_window를 올바르게 호출하는지"""

    def test_calls_ensure_window(self, mock_controller):
        """_handle_focus_window가 ensure_window를 호출"""
        from models.commands import EditorCommand

        cmd = EditorCommand(type="focus_window", payload={"window_title": "VS Code"})
        result = mock_controller.execute(cmd)
        mock_controller.window_manager.ensure_window.assert_called_once()
        assert result["success"] is True

    def test_passes_project_hint(self, mock_controller):
        """payload에 project_hint가 있으면 전달"""
        from models.commands import EditorCommand

        cmd = EditorCommand(
            type="focus_window", payload={"window_title": "VS Code", "project_hint": "my-proj"}
        )
        mock_controller.execute(cmd)
        call_kwargs = mock_controller.window_manager.ensure_window.call_args
        assert call_kwargs[1]["project_hint"] == "my-proj"

    def test_ensure_window_failure(self, mock_controller):
        """ensure_window 실패 시 success=False"""
        from models.commands import EditorCommand

        mock_controller.window_manager.ensure_window.return_value = False
        cmd = EditorCommand(type="focus_window", payload={"window_title": "VS Code"})
        result = mock_controller.execute(cmd)
        assert result["success"] is False
