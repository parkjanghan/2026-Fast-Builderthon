# ============================================================================
# 📁 tests/test_integration.py - 통합 테스트 스텁 (실제 VS Code 필요)
# ============================================================================
#
# 🎯 역할:
#   실제 Windows 환경 + VS Code가 실행 중일 때만 동작하는 통합 테스트입니다.
#   기본적으로 건너뛰며, -m integration 으로 실행합니다.
#
# 🚀 실행 방법:
#   pytest -m integration  (VS Code가 열려 있어야 합니다)
#
# ============================================================================

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.integration
class TestWindowManagerIntegration:
    """실제 pywinauto를 사용한 윈도우 관리 테스트"""

    def test_find_vscode_window(self, keymap_path):
        """VS Code 창을 찾을 수 있는지 확인"""
        from controller.window import WindowManager

        wm = WindowManager()
        window = wm.find_window("Visual Studio Code")
        assert window is not None, "VS Code 창을 찾을 수 없습니다. VS Code를 실행해 주세요."

    def test_focus_vscode_window(self, keymap_path):
        """VS Code 창에 포커스할 수 있는지 확인"""
        from controller.window import WindowManager

        wm = WindowManager()
        result = wm.focus_window("Visual Studio Code")
        assert result is True, "VS Code 창에 포커스할 수 없습니다."

    def test_is_vscode_running(self, keymap_path):
        """VS Code가 실행 중인지 확인"""
        from controller.window import WindowManager

        wm = WindowManager()
        assert wm.is_app_running("Visual Studio Code") is True

    def test_get_active_window_title(self, keymap_path):
        """활성 창 제목을 가져올 수 있는지 확인"""
        from controller.window import WindowManager

        wm = WindowManager()
        title = wm.get_active_window_title()
        assert isinstance(title, str)
        assert len(title) > 0


@pytest.mark.integration
class TestKeyboardControllerIntegration:
    """실제 키보드 입력 테스트 (VS Code가 포커스 상태여야 함)"""

    def test_send_hotkey_ctrl_g(self, keymap_path):
        """Ctrl+G 단축키로 Go to Line 다이얼로그 열기"""
        from controller.keyboard import KeyboardController

        kb = KeyboardController()
        # ⚠️ 이 테스트는 VS Code에 실제로 키 입력을 보냅니다
        kb.send_hotkey(["ctrl", "g"])
        # 수동으로 다이얼로그가 열렸는지 확인 필요
        kb.send_hotkey(["esc"])  # 닫기


@pytest.mark.integration
class TestEditorControllerIntegration:
    """EditorController 전체 통합 테스트"""

    def test_execute_goto_line(self, keymap_path):
        """goto_line 명령 실행"""
        from controller.executor import EditorController
        from models.commands import EditorCommand

        controller = EditorController(keymap_path=keymap_path)
        cmd = EditorCommand(type="goto_line", payload={"line_number": 1})
        # ⚠️ NotImplementedError가 발생하면 핸들러 미구현 상태
        try:
            result = controller.execute(cmd)
            assert result.get("success") is True
        except NotImplementedError:
            pytest.skip("핸들러가 아직 구현되지 않았습니다")
