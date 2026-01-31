# ============================================================================
# 📁 tests/test_models.py - 모델 단위 테스트
# ============================================================================
#
# 🎯 역할:
#   EditorCommand, LocalStatus 모델의 생성, 검증, 직렬화를 테스트합니다.
#   from_legacy() 어댑터의 모든 action 타입 변환을 검증합니다.
#
# ============================================================================

import time

import pytest
from pydantic import ValidationError

from models.commands import (
    CommandPalettePayload,
    EditorCommand,
    FocusWindowPayload,
    GotoLinePayload,
    HotkeyPayload,
    OpenFilePayload,
    TypeTextPayload,
)
from models.status import LocalStatus

# -------------------------------------------------------------------------
# 🔧 EditorCommand 생성 테스트
# -------------------------------------------------------------------------


class TestEditorCommandCreation:
    """EditorCommand 직접 생성 테스트"""

    def test_focus_window(self):
        cmd = EditorCommand(type="focus_window", payload={"window_title": "VS Code"})
        assert cmd.type == "focus_window"
        assert cmd.payload["window_title"] == "VS Code"

    def test_hotkey(self):
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "g"]})
        assert cmd.type == "hotkey"
        assert cmd.payload["keys"] == ["ctrl", "g"]

    def test_type_text(self):
        cmd = EditorCommand(type="type_text", payload={"content": "print('hello')"})
        assert cmd.type == "type_text"
        assert cmd.payload["content"] == "print('hello')"

    def test_command_palette(self):
        cmd = EditorCommand(type="command_palette", payload={"command": "Go to Line"})
        assert cmd.type == "command_palette"

    def test_open_file(self):
        cmd = EditorCommand(type="open_file", payload={"file_path": "C:/project/main.py"})
        assert cmd.type == "open_file"

    def test_goto_line(self):
        cmd = EditorCommand(type="goto_line", payload={"line_number": 42})
        assert cmd.type == "goto_line"

    def test_optional_fields(self):
        cmd = EditorCommand(
            type="hotkey",
            payload={"keys": ["ctrl", "s"]},
            id="cmd-001",
            audio_url="https://example.com/audio.mp3",
        )
        assert cmd.id == "cmd-001"
        assert cmd.audio_url == "https://example.com/audio.mp3"

    def test_optional_fields_default_none(self):
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "s"]})
        assert cmd.id is None
        assert cmd.audio_url is None

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            EditorCommand(type="invalid_type", payload={})


# -------------------------------------------------------------------------
# 🔄 from_legacy() 변환 테스트
# -------------------------------------------------------------------------


class TestFromLegacy:
    """레거시 dict → EditorCommand 변환 테스트"""

    def test_type_action(self):
        cmd = EditorCommand.from_legacy({"action": "type", "content": "hello world"})
        assert cmd.type == "type_text"
        assert cmd.payload["content"] == "hello world"

    def test_hotkey_action_string(self):
        cmd = EditorCommand.from_legacy({"action": "hotkey", "content": "ctrl+g"})
        assert cmd.type == "hotkey"
        assert cmd.payload["keys"] == ["ctrl", "g"]

    def test_hotkey_action_list(self):
        cmd = EditorCommand.from_legacy({"action": "hotkey", "content": ["ctrl", "shift", "p"]})
        assert cmd.type == "hotkey"
        assert cmd.payload["keys"] == ["ctrl", "shift", "p"]

    def test_goto_line_action(self):
        cmd = EditorCommand.from_legacy({"action": "goto_line", "line": 25})
        assert cmd.type == "goto_line"
        assert cmd.payload["line_number"] == 25

    def test_goto_line_string(self):
        cmd = EditorCommand.from_legacy({"action": "goto_line", "line": "42"})
        assert cmd.type == "goto_line"
        assert cmd.payload["line_number"] == 42

    def test_command_palette_action(self):
        cmd = EditorCommand.from_legacy({"action": "command_palette", "content": "Format Document"})
        assert cmd.type == "command_palette"
        assert cmd.payload["command"] == "Format Document"

    def test_open_file_action(self):
        cmd = EditorCommand.from_legacy({"action": "open_file", "content": "C:/main.py"})
        assert cmd.type == "open_file"
        assert cmd.payload["file_path"] == "C:/main.py"

    def test_focus_window_action_target(self):
        cmd = EditorCommand.from_legacy({"action": "focus_window", "target": "VS Code"})
        assert cmd.type == "focus_window"
        assert cmd.payload["window_title"] == "VS Code"

    def test_focus_window_action_content_fallback(self):
        cmd = EditorCommand.from_legacy({"action": "focus_window", "content": "Notepad"})
        assert cmd.payload["window_title"] == "Notepad"

    def test_unknown_action_defaults_to_type_text(self):
        cmd = EditorCommand.from_legacy({"action": "unknown", "content": "some text"})
        assert cmd.type == "type_text"
        assert cmd.payload["content"] == "some text"

    def test_preserves_audio_url(self):
        cmd = EditorCommand.from_legacy(
            {"action": "type", "content": "x", "audio_url": "https://audio.mp3"}
        )
        assert cmd.audio_url == "https://audio.mp3"

    def test_preserves_id(self):
        cmd = EditorCommand.from_legacy({"action": "type", "content": "x", "id": "cmd-123"})
        assert cmd.id == "cmd-123"


# -------------------------------------------------------------------------
# 📦 페이로드 모델 테스트
# -------------------------------------------------------------------------


class TestPayloadModels:
    """각 페이로드 모델의 검증 테스트"""

    def test_focus_window_payload(self):
        p = FocusWindowPayload(window_title="VS Code")
        assert p.window_title == "VS Code"

    def test_hotkey_payload(self):
        p = HotkeyPayload(keys=["ctrl", "shift", "p"])
        assert len(p.keys) == 3

    def test_type_text_payload(self):
        p = TypeTextPayload(content="print('hello')")
        assert p.content == "print('hello')"

    def test_command_palette_payload(self):
        p = CommandPalettePayload(command="Format Document")
        assert p.command == "Format Document"

    def test_open_file_payload(self):
        p = OpenFilePayload(file_path="C:/project/main.py")
        assert p.file_path == "C:/project/main.py"

    def test_goto_line_payload(self):
        p = GotoLinePayload(line_number=42)
        assert p.line_number == 42

    def test_goto_line_rejects_zero(self):
        with pytest.raises(ValidationError):
            GotoLinePayload(line_number=0)

    def test_goto_line_rejects_negative(self):
        with pytest.raises(ValidationError):
            GotoLinePayload(line_number=-1)


# -------------------------------------------------------------------------
# 📊 LocalStatus 테스트
# -------------------------------------------------------------------------


class TestLocalStatus:
    """LocalStatus 모델의 생성과 직렬화 테스트"""

    def test_creation(self):
        status = LocalStatus(
            active_window="Visual Studio Code",
            target_app_running=True,
            status="IDLE",
            current_keymap="vscode",
            timestamp=time.time(),
        )
        assert status.status == "IDLE"
        assert status.target_app_running is True

    def test_busy_status(self):
        status = LocalStatus(
            active_window="VS Code",
            target_app_running=True,
            status="BUSY",
            current_keymap="vscode",
            timestamp=1.0,
        )
        assert status.status == "BUSY"

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            LocalStatus(
                active_window="VS Code",
                target_app_running=True,
                status="UNKNOWN",
                current_keymap="vscode",
                timestamp=1.0,
            )

    def test_model_dump(self):
        status = LocalStatus(
            active_window="VS Code",
            target_app_running=False,
            status="IDLE",
            current_keymap="vscode",
            timestamp=123.456,
        )
        d = status.model_dump()
        assert d["active_window"] == "VS Code"
        assert d["target_app_running"] is False
        assert d["timestamp"] == 123.456
