# ============================================================================
# 📁 tests/conftest.py - pytest 공통 픽스처 및 설정
# ============================================================================
#
# 🎯 역할:
#   테스트에서 공통으로 사용하는 픽스처, 마커, 모킹 헬퍼를 정의합니다.
#   pygame/socketio 의존성 없이 controller/models를 단독 테스트합니다.
#
# ============================================================================

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# -------------------------------------------------------------------------
# 🔧 pygame / socketio 모킹 (빌드 없이 임포트 가능하도록)
# -------------------------------------------------------------------------

# pygame 모킹
_pygame_mock = MagicMock()
_pygame_mock.mixer = MagicMock()
sys.modules.setdefault("pygame", _pygame_mock)

# socketio 모킹
_sio_mock = MagicMock()
sys.modules.setdefault("socketio", _sio_mock)
sys.modules.setdefault("engineio", MagicMock())

# pywinauto 모킹 (테스트 환경에 없을 수 있으므로)
for mod_name in [
    "pywinauto",
    "pywinauto.application",
    "pywinauto.findwindows",
    "pygetwindow",
]:
    sys.modules.setdefault(mod_name, MagicMock())

# -------------------------------------------------------------------------
# 📂 프로젝트 경로 설정
# -------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# -------------------------------------------------------------------------
# 🔧 픽스처: 키맵 경로
# -------------------------------------------------------------------------


@pytest.fixture
def keymap_path() -> str:
    """VS Code 키맵 YAML 경로"""
    return str(PROJECT_ROOT / "keymaps" / "vscode.yaml")


# -------------------------------------------------------------------------
# 🔧 픽스처: EditorCommand 팩토리
# -------------------------------------------------------------------------


@pytest.fixture
def make_command():
    """EditorCommand 팩토리 픽스처"""
    from models.commands import EditorCommand

    def _make(cmd_type: str, payload: dict, **kwargs):
        return EditorCommand(type=cmd_type, payload=payload, **kwargs)

    return _make


# -------------------------------------------------------------------------
# 🔧 픽스처: 모킹된 EditorController
# -------------------------------------------------------------------------


@pytest.fixture
def mock_controller(keymap_path):
    """WindowManager와 KeyboardController가 모킹된 EditorController"""
    from controller.executor import EditorController

    controller = EditorController(keymap_path=keymap_path)
    controller.window_manager = MagicMock()
    controller.keyboard_controller = MagicMock()

    # 기본 반환값 설정
    controller.window_manager.get_active_window_title.return_value = "Visual Studio Code"
    controller.window_manager.is_app_running.return_value = True
    controller.window_manager.focus_window.return_value = True
    controller.window_manager.find_window.return_value = MagicMock()
    controller.window_manager.ensure_window.return_value = True
    controller.window_manager.find_all_windows.return_value = ["Visual Studio Code"]

    return controller
