# ============================================================================
# 📁 tests/test_controller.py - 컨트롤러 디스패치 단위 테스트
# ============================================================================
#
# 🎯 역할:
#   EditorController의 디스패치 로직, 상태 전환, get_status()를 테스트합니다.
#   핸들러는 모킹하여 디스패치가 올바른 핸들러를 호출하는지 검증합니다.
#
# ============================================================================

from unittest.mock import MagicMock

import pytest

from controller.executor import EditorController
from models.commands import EditorCommand

# -------------------------------------------------------------------------
# 🎯 디스패치 라우팅 테스트
# -------------------------------------------------------------------------


class TestDispatchRouting:
    """execute()가 올바른 핸들러로 디스패치하는지 테스트"""

    def test_dispatch_focus_window(self, mock_controller):
        mock_controller._handle_focus_window = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="focus_window", payload={"window_title": "VS Code"})
        result = mock_controller.execute(cmd)
        mock_controller._handle_focus_window.assert_called_once_with({"window_title": "VS Code"})
        assert result["success"] is True

    def test_dispatch_hotkey(self, mock_controller):
        mock_controller._handle_hotkey = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "g"]})
        mock_controller.execute(cmd)
        mock_controller._handle_hotkey.assert_called_once_with({"keys": ["ctrl", "g"]})

    def test_dispatch_type_text(self, mock_controller):
        mock_controller._handle_type_text = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="type_text", payload={"content": "hello"})
        mock_controller.execute(cmd)
        mock_controller._handle_type_text.assert_called_once_with({"content": "hello"})

    def test_dispatch_command_palette(self, mock_controller):
        mock_controller._handle_command_palette = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="command_palette", payload={"command": "Go to Line"})
        mock_controller.execute(cmd)
        mock_controller._handle_command_palette.assert_called_once_with({"command": "Go to Line"})

    def test_dispatch_open_file(self, mock_controller):
        mock_controller._handle_open_file = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="open_file", payload={"file_path": "C:/main.py"})
        mock_controller.execute(cmd)
        mock_controller._handle_open_file.assert_called_once_with({"file_path": "C:/main.py"})

    def test_dispatch_goto_line(self, mock_controller):
        mock_controller._handle_goto_line = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="goto_line", payload={"line_number": 42})
        mock_controller.execute(cmd)
        mock_controller._handle_goto_line.assert_called_once_with({"line_number": 42})

    def test_dispatch_goto_line_with_column(self, mock_controller):
        mock_controller._handle_goto_line = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="goto_line", payload={"line_number": 3, "column": 23})
        mock_controller.execute(cmd)
        mock_controller._handle_goto_line.assert_called_once_with(
            {"line_number": 3, "column": 23}
        )

    def test_dispatch_open_folder(self, mock_controller):
        mock_controller._handle_open_folder = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="open_folder", payload={"folder_path": "C:/workspace"})
        mock_controller.execute(cmd)
        mock_controller._handle_open_folder.assert_called_once_with(
            {"folder_path": "C:/workspace"}
        )

    def test_dispatch_save_file(self, mock_controller):
        mock_controller._handle_save_file = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="save_file", payload={"file_name": "app.py"})
        mock_controller.execute(cmd)
        mock_controller._handle_save_file.assert_called_once_with({"file_name": "app.py"})

    def test_dispatch_save_file_no_name(self, mock_controller):
        mock_controller._handle_save_file = MagicMock(return_value={"success": True})
        cmd = EditorCommand(type="save_file", payload={"file_name": None})
        mock_controller.execute(cmd)
        mock_controller._handle_save_file.assert_called_once_with({"file_name": None})


# -------------------------------------------------------------------------
# 🔄 상태 전환 테스트
# -------------------------------------------------------------------------


class TestStateTransitions:
    """execute() 전후로 IDLE/BUSY 상태 전환 테스트"""

    def test_idle_before_and_after(self, mock_controller):
        mock_controller._handle_hotkey = MagicMock(return_value={"success": True})
        assert mock_controller.current_status == "IDLE"
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "s"]})
        mock_controller.execute(cmd)
        assert mock_controller.current_status == "IDLE"

    def test_busy_during_execution(self, mock_controller):
        """실행 중에는 BUSY 상태인지 확인"""
        captured_status = []

        def capture_handler(payload):
            captured_status.append(mock_controller.current_status)
            return {"success": True}

        mock_controller._handle_hotkey = capture_handler
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "s"]})
        mock_controller.execute(cmd)
        assert captured_status[0] == "BUSY"
        assert mock_controller.current_status == "IDLE"

    def test_idle_restored_on_exception(self, mock_controller):
        """핸들러 예외 시에도 IDLE 복원"""
        mock_controller._handle_hotkey = MagicMock(side_effect=RuntimeError("boom"))
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "s"]})
        with pytest.raises(RuntimeError):
            mock_controller.execute(cmd)
        assert mock_controller.current_status == "IDLE"


# -------------------------------------------------------------------------
# 📊 get_status() 테스트
# -------------------------------------------------------------------------


class TestGetStatus:
    """get_status() 반환값 테스트"""

    def test_returns_local_status(self, mock_controller):
        status = mock_controller.get_status()
        assert status.active_window == "Visual Studio Code"
        assert status.target_app_running is True
        assert status.status == "IDLE"
        assert status.current_keymap == "Visual Studio Code"

    def test_fallback_on_error(self, keymap_path):
        """WindowManager가 예외 발생 시 폴백 확인"""
        controller = EditorController(keymap_path=keymap_path)
        # WindowManager 메서드가 예외를 발생시키도록 모킹
        controller.window_manager.get_active_window_title = MagicMock(
            side_effect=NotImplementedError
        )
        controller.window_manager.is_app_running = MagicMock(side_effect=NotImplementedError)
        status = controller.get_status()
        assert status.active_window == "Unknown (구현 필요)"
        assert status.target_app_running is False
