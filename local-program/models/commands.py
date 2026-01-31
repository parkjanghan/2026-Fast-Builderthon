# ============================================================================
# 📁 models/commands.py - 에디터 명령 스키마 (서버 → 로컬)
# ============================================================================
#
# 🎯 역할:
#   Part 2 서버에서 받은 에디터 조작 명령을 검증하고 파싱합니다.
#   Pydantic v2를 사용하여 타입 안전성을 보장합니다.
#
# 📝 명령 타입:
#   - focus_window: 특정 창에 포커스
#   - hotkey: 단축키 실행 (Ctrl+G 등)
#   - type_text: 텍스트 입력
#   - command_palette: VS Code 명령 팔레트 실행
#   - open_file: 파일 열기
#   - goto_line: 특정 라인으로 이동
#   - open_folder: 폴더를 워크스페이스로 열기
#   - save_file: 파일 저장 (이름 지정 가능)
#
# ============================================================================

from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================================
# 🔧 페이로드 모델들 (각 명령 타입별)
# ============================================================================


class FocusWindowPayload(BaseModel):
    """창 포커스 명령 페이로드"""

    window_title: str = Field(..., description="포커스할 창의 제목")


class HotkeyPayload(BaseModel):
    """단축키 명령 페이로드"""

    keys: list[str] = Field(..., description="단축키 조합 (예: ['ctrl', 'g'])")


class TypeTextPayload(BaseModel):
    """텍스트 입력 명령 페이로드"""

    content: str = Field(..., description="입력할 텍스트")


class CommandPalettePayload(BaseModel):
    """명령 팔레트 명령 페이로드"""

    command: str = Field(..., description="실행할 명령어 (예: 'Go to Line')")


class OpenFilePayload(BaseModel):
    """파일 열기 명령 페이로드"""

    file_path: str = Field(..., description="열 파일의 경로")


class GotoLinePayload(BaseModel):
    """라인 이동 명령 페이로드"""

    line_number: int = Field(..., description="이동할 라인 번호", ge=1)
    column: int | None = Field(None, description="이동할 컬럼 번호 (선택)", ge=1)


class OpenFolderPayload(BaseModel):
    """폴더 열기 명령 페이로드"""

    folder_path: str = Field(..., description="열 폴더 경로")
    new_window: bool = Field(False, description="새 창에서 열기 여부")


class SaveFilePayload(BaseModel):
    """파일 저장 명령 페이로드"""

    file_name: str | None = Field(None, description="저장할 파일명 (None이면 현재 파일 저장)")
    folder_path: str | None = Field(
        None, description="저장 폴더 경로 (file_name과 조합하여 절대 경로 생성)"
    )


# ============================================================================
# 🎯 메인 명령 모델
# ============================================================================


class EditorCommand(BaseModel):
    """
    📡 서버에서 받은 에디터 조작 명령

    이 모델은 Part 2 서버에서 전송한 명령을 검증하고 파싱합니다.
    각 명령 타입에 따라 다른 페이로드 구조를 가집니다.

    Example:
        # 단축키 명령
        cmd = EditorCommand(
            type="hotkey",
            payload={"keys": ["ctrl", "g"]}
        )

        # 텍스트 입력 명령
        cmd = EditorCommand(
            type="type_text",
            payload={"content": "print('Hello')"}
        )
    """

    type: Literal[
        "focus_window",
        "hotkey",
        "type_text",
        "command_palette",
        "open_file",
        "goto_line",
        "open_folder",
        "save_file",
    ] = Field(..., description="명령 타입")

    payload: dict[str, Any] = Field(..., description="명령별 페이로드 데이터")

    # 선택적 필드들 (레거시 호환성)
    id: str | None = Field(None, description="명령 ID (추적용)")
    audio_url: str | None = Field(None, description="재생할 오디오 URL")
    target_file: str | None = Field(None, description="편집 대상 파일명 (VS Code 타이틀로 검증용)")
    expected_content: str | None = Field(
        None, description="화면에 보이는 파일 내용 (로컬 파일 검증용)"
    )

    @classmethod
    def from_legacy(cls, command_data: dict[str, Any]) -> "EditorCommand":
        """
        🔄 서버 명령을 EditorCommand로 변환 (신규 + 레거시 형식 모두 지원)

        서버 신규 형식 (params 딕셔너리):
            {"action": "FOCUS_WINDOW", "params": {"window_title": "..."}}
        레거시 형식 (플랫 필드):
            {"action": "focus_window", "target": "...", "content": "..."}

        Args:
            command_data: 서버 명령 데이터
                - action: 수행할 동작 (FOCUS_WINDOW, TYPE_CODE, GOTO_LINE 등)
                - params: 동작 파라미터 딕셔너리 (신규 형식)
                - target: 대상 요소 (레거시)
                - content / text: 입력 내용
                - line: 라인 번호
                - audio_url: 재생할 오디오 URL
                - id: 명령 ID

        Returns:
            EditorCommand: 변환된 명령 객체

        Example:
            legacy_cmd = {
                "action": "type",
                "target": "editor",
                "content": "hello world",
                "audio_url": "https://..."
            }
            cmd = EditorCommand.from_legacy(legacy_cmd)
            assert cmd.type == "type_text"
            assert cmd.payload["content"] == "hello world"
        """
        # 🔀 params 딕셔너리가 있으면 최상위로 병합 (서버 신규 형식 지원)
        # 서버 형식: {"action": "FOCUS_WINDOW", "params": {"window_title": "..."}}
        # 레거시 형식: {"action": "focus_window", "target": "...", "content": "..."}
        params = command_data.get("params", {})
        merged = {**command_data, **params} if params else command_data

        action = merged.get("action", "").lower()
        target = merged.get("target", "")
        content = merged.get("content", merged.get("text", ""))
        line = merged.get("line", merged.get("line_number"))
        audio_url = merged.get("audio_url")
        cmd_id = merged.get("id")

        # 🔀 action을 type으로 매핑
        if action in ("type", "type_code", "type_text"):
            cmd_type = "type_text"
            payload = {"content": content}

        elif action == "hotkey":
            cmd_type = "hotkey"
            # params에 keys 리스트가 있으면 우선 사용, content가 리스트여도 OK
            raw_keys = merged.get("keys")
            if isinstance(raw_keys, list) and raw_keys:
                keys = raw_keys
            elif isinstance(content, list) and content:
                keys = content
            elif isinstance(content, str) and content:
                # content가 "ctrl+g" 형식이면 파싱 (레거시)
                keys = [k.strip() for k in content.split("+")]
            else:
                keys = []
            # 빈 문자열 키 제거
            keys = [k for k in keys if k]
            payload = {"keys": keys}

        elif action == "goto_line":
            cmd_type = "goto_line"
            line_num = line if isinstance(line, int) else int(line or 1)
            column = merged.get("column")
            payload: dict[str, Any] = {"line_number": line_num}
            if column is not None:
                payload["column"] = int(column)

        elif action == "command_palette":
            cmd_type = "command_palette"
            command_text = merged.get("command", "") or content
            payload = {"command": command_text}

        elif action == "open_file":
            cmd_type = "open_file"
            file_path = merged.get("file_path", "") or content
            payload = {"file_path": file_path}

        elif action == "focus_window":
            cmd_type = "focus_window"
            window_title = merged.get("window_title", "") or target or content
            payload = {"window_title": window_title}

        elif action == "open_folder":
            cmd_type = "open_folder"
            folder_path = merged.get("folder_path", content)
            new_window = merged.get("new_window", False)
            payload = {"folder_path": folder_path, "new_window": new_window}

        elif action == "save_file":
            cmd_type = "save_file"
            file_name = merged.get("file_name", content or None)
            folder_path = merged.get("folder_path")
            payload = {"file_name": file_name, "folder_path": folder_path}

        else:
            # 기본값: type_text로 처리
            cmd_type = "type_text"
            payload = {"content": content}

        # 편집 대상 파일명 추출 (서버가 target_file을 보내는 경우)
        target_file = merged.get("target_file")
        # 화면에 보이는 파일 내용 (파일 검증용)
        expected_content = merged.get("expected_content")

        return cls(
            type=cmd_type,
            payload=payload,
            audio_url=audio_url,
            id=cmd_id,
            target_file=target_file,
            expected_content=expected_content,
        )
