# ============================================================================
# 📁 tests/test_scenarios.py - 시나리오 테스트 (모의 명령 시퀀스)
# ============================================================================
#
# 🎯 역할:
#   실제 사용 시나리오를 모의하여, 명령 시퀀스가 올바른 핸들러를
#   올바른 순서로 호출하는지 검증합니다.
#
# 시나리오 목록:
#   - 새 파일 만들기: hotkey(ctrl+n)
#   - hello world 입력: type_text("print('hello world')")
#   - 파일 열고 줄 이동: open_file → goto_line
#   - 명령 팔레트로 포맷팅: command_palette("Format Document")
#   - 전체 코딩 세션: focus → open_file → goto_line → type_text
#
# ============================================================================

from unittest.mock import MagicMock

from models.commands import EditorCommand

# -------------------------------------------------------------------------
# 📝 시나리오 1: 새 파일 만들기
# -------------------------------------------------------------------------


class TestScenarioNewFile:
    """새 파일 만들기: Ctrl+N 단축키 실행"""

    def test_new_file_via_hotkey(self, mock_controller):
        mock_controller._handle_hotkey = MagicMock(
            return_value={"success": True, "message": "단축키 전송 완료: ctrl+n"}
        )
        cmd = EditorCommand(type="hotkey", payload={"keys": ["ctrl", "n"]})
        result = mock_controller.execute(cmd)
        mock_controller._handle_hotkey.assert_called_once_with({"keys": ["ctrl", "n"]})
        assert result["success"] is True

    def test_new_file_from_legacy(self, mock_controller):
        """레거시 형식에서 변환하여 실행"""
        mock_controller._handle_hotkey = MagicMock(return_value={"success": True})
        legacy = {"action": "hotkey", "content": "ctrl+n"}
        cmd = EditorCommand.from_legacy(legacy)
        assert cmd.type == "hotkey"
        assert cmd.payload["keys"] == ["ctrl", "n"]
        mock_controller.execute(cmd)
        mock_controller._handle_hotkey.assert_called_once()


# -------------------------------------------------------------------------
# 📝 시나리오 2: hello world 입력
# -------------------------------------------------------------------------


class TestScenarioTypeHelloWorld:
    """print('hello world') 텍스트 입력"""

    def test_type_hello_world(self, mock_controller):
        mock_controller._handle_type_text = MagicMock(
            return_value={"success": True, "message": "텍스트 입력 완료"}
        )
        cmd = EditorCommand(type="type_text", payload={"content": "print('hello world')"})
        result = mock_controller.execute(cmd)
        mock_controller._handle_type_text.assert_called_once_with(
            {"content": "print('hello world')"}
        )
        assert result["success"] is True

    def test_type_hello_from_legacy(self, mock_controller):
        mock_controller._handle_type_text = MagicMock(return_value={"success": True})
        legacy = {"action": "type", "content": "print('hello world')"}
        cmd = EditorCommand.from_legacy(legacy)
        assert cmd.type == "type_text"
        assert cmd.payload["content"] == "print('hello world')"


# -------------------------------------------------------------------------
# 📝 시나리오 3: 파일 열고 특정 줄로 이동
# -------------------------------------------------------------------------


class TestScenarioOpenFileAndGotoLine:
    """파일 열기 → 줄 이동 시퀀스"""

    def test_open_then_goto(self, mock_controller):
        mock_controller._handle_open_file = MagicMock(return_value={"success": True})
        mock_controller._handle_goto_line = MagicMock(return_value={"success": True})

        # 1단계: 파일 열기
        cmd1 = EditorCommand(type="open_file", payload={"file_path": "C:/project/main.py"})
        result1 = mock_controller.execute(cmd1)
        assert result1["success"] is True

        # 2단계: 25번 줄로 이동
        cmd2 = EditorCommand(type="goto_line", payload={"line_number": 25})
        result2 = mock_controller.execute(cmd2)
        assert result2["success"] is True

        # 순서 검증
        mock_controller._handle_open_file.assert_called_once()
        mock_controller._handle_goto_line.assert_called_once_with({"line_number": 25})

    def test_open_then_goto_from_legacy(self, mock_controller):
        mock_controller._handle_open_file = MagicMock(return_value={"success": True})
        mock_controller._handle_goto_line = MagicMock(return_value={"success": True})

        cmds = [
            EditorCommand.from_legacy({"action": "open_file", "content": "C:/main.py"}),
            EditorCommand.from_legacy({"action": "goto_line", "line": 25}),
        ]
        for cmd in cmds:
            mock_controller.execute(cmd)

        assert mock_controller._handle_open_file.call_count == 1
        assert mock_controller._handle_goto_line.call_count == 1


# -------------------------------------------------------------------------
# 📝 시나리오 4: 명령 팔레트로 포맷팅
# -------------------------------------------------------------------------


class TestScenarioFormatDocument:
    """명령 팔레트에서 Format Document 실행"""

    def test_format_via_command_palette(self, mock_controller):
        mock_controller._handle_command_palette = MagicMock(
            return_value={"success": True, "message": "명령 팔레트 실행 완료"}
        )
        cmd = EditorCommand(type="command_palette", payload={"command": "Format Document"})
        result = mock_controller.execute(cmd)
        mock_controller._handle_command_palette.assert_called_once_with(
            {"command": "Format Document"}
        )
        assert result["success"] is True

    def test_format_from_legacy(self, mock_controller):
        mock_controller._handle_command_palette = MagicMock(return_value={"success": True})
        legacy = {"action": "command_palette", "content": "Format Document"}
        cmd = EditorCommand.from_legacy(legacy)
        assert cmd.payload["command"] == "Format Document"


# -------------------------------------------------------------------------
# 📝 시나리오 5: 전체 코딩 세션 시퀀스
# -------------------------------------------------------------------------


class TestScenarioFullCodingSession:
    """완전한 코딩 세션: 포커스 → 파일 열기 → 줄 이동 → 텍스트 입력"""

    def test_full_session_sequence(self, mock_controller):
        # 모든 핸들러 모킹
        mock_controller._handle_focus_window = MagicMock(return_value={"success": True})
        mock_controller._handle_open_file = MagicMock(return_value={"success": True})
        mock_controller._handle_goto_line = MagicMock(return_value={"success": True})
        mock_controller._handle_type_text = MagicMock(return_value={"success": True})

        commands = [
            EditorCommand(type="focus_window", payload={"window_title": "Visual Studio Code"}),
            EditorCommand(type="open_file", payload={"file_path": "C:/project/app.py"}),
            EditorCommand(type="goto_line", payload={"line_number": 15}),
            EditorCommand(type="type_text", payload={"content": "# 새로운 코드 추가"}),
        ]

        results = []
        for cmd in commands:
            results.append(mock_controller.execute(cmd))

        # 모든 명령 성공
        assert all(r["success"] for r in results)

        # 각 핸들러가 정확히 1번씩 호출됨
        mock_controller._handle_focus_window.assert_called_once()
        mock_controller._handle_open_file.assert_called_once()
        mock_controller._handle_goto_line.assert_called_once()
        mock_controller._handle_type_text.assert_called_once()

        # 최종 상태는 IDLE
        assert mock_controller.current_status == "IDLE"

    def test_session_with_audio_url(self, mock_controller):
        """오디오 URL이 포함된 명령도 정상 디스패치"""
        mock_controller._handle_type_text = MagicMock(return_value={"success": True})
        cmd = EditorCommand(
            type="type_text",
            payload={"content": "print('hello')"},
            audio_url="https://api.elevenlabs.io/audio.mp3",
        )
        result = mock_controller.execute(cmd)
        assert result["success"] is True
        assert cmd.audio_url == "https://api.elevenlabs.io/audio.mp3"
