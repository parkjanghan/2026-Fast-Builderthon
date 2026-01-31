# ============================================================================
# 📁 models/status.py - 로컬 상태 스키마 (로컬 → 서버)
# ============================================================================
#
# 🎯 역할:
#   로컬 에이전트의 현재 상태를 Part 2 서버에 보고합니다.
#   1초마다 이 모델의 인스턴스를 생성하여 서버로 전송합니다.
#
# 📊 상태 정보:
#   - active_window: 현재 활성 창 제목
#   - target_app_running: 대상 애플리케이션(VS Code 등) 실행 여부
#   - status: 로컬 에이전트 상태 (IDLE, BUSY)
#   - current_keymap: 현재 키맵 설정 (vscode, vim 등)
#   - timestamp: 상태 보고 시간
#
# ============================================================================

from typing import ClassVar, Literal

from pydantic import BaseModel, Field


class LocalStatus(BaseModel):
    """
    📊 로컬 에이전트의 현재 상태

    이 모델은 로컬 에이전트가 1초마다 Part 2 서버에 보고하는 상태 정보입니다.
    서버는 이 정보를 통해 로컬 에이전트의 상태를 모니터링합니다.

    Example:
        status = LocalStatus(
            active_window="Visual Studio Code",
            target_app_running=True,
            status="IDLE",
            current_keymap="vscode",
            timestamp=1234567890.5
        )

        # JSON으로 직렬화하여 서버로 전송
        import json
        json.dumps(status.model_dump())
    """

    active_window: str = Field(..., description="현재 활성 창의 제목 (예: 'Visual Studio Code')")

    target_app_running: bool = Field(
        ..., description="대상 애플리케이션(VS Code 등)이 실행 중인지 여부"
    )

    status: Literal["IDLE", "BUSY"] = Field(
        ..., description="로컬 에이전트의 상태 (IDLE: 대기 중, BUSY: 명령 실행 중)"
    )

    current_keymap: str = Field(..., description="현재 키맵 설정 (예: 'vscode', 'vim', 'default')")

    timestamp: float = Field(..., description="상태 보고 시간 (Unix timestamp, 초 단위)")

    class Config:
        """Pydantic 설정"""

        json_schema_extra: ClassVar[dict] = {
            "example": {
                "active_window": "Visual Studio Code",
                "target_app_running": True,
                "status": "IDLE",
                "current_keymap": "vscode",
                "timestamp": 1704067200.5,
            }
        }
