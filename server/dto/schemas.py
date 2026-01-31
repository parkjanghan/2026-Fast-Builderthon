from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal, List


# ============================================================================
# 📨 공통 Envelope (Extension & Local Agent 모두 동일 형식)
# ============================================================================


class MessageEnvelope(BaseModel):
    """
    모든 클라이언트가 보내는 래퍼 형식:
      { "source": "chrome" | "local", "data": { ... } }
    """

    source: Literal["chrome", "local"]
    data: Dict[str, Any]


# ============================================================================
# 📥 Extension → Server (data 내부 스키마)
# ============================================================================


class FrameData(BaseModel):
    """Extension이 보내는 화면 캡처 — envelope.data 내부"""

    type: Literal["frame"]
    timestamp: int
    videoTime: float
    image: str  # data:image/jpeg;base64,...
    capturedAt: int


class TranscriptData(BaseModel):
    """Extension이 보내는 STT 자막 — envelope.data 내부"""

    type: Literal["transcript"]
    timestamp: int
    videoTime: float
    text: str
    videoTimeStart: float
    videoTimeEnd: float


# ============================================================================
# 📤 Server → Extension (protocol.md 기준)
# ============================================================================


class ConnectedMessage(BaseModel):
    type: Literal["connected"] = "connected"
    message: str = "Connection established"
    timestamp: int


class ServerTranscriptMessage(BaseModel):
    """서버가 Extension에 보내는 transcript 응답"""

    type: Literal["transcript"] = "transcript"
    startTime: float
    endTime: float
    text: str
    fullContext: str = ""


class CommandMessage(BaseModel):
    type: Literal["command"] = "command"
    action: Literal["pause", "resume", "seek"]
    value: Optional[float] = None


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


# ============================================================================
# 📤 Server → Local Agent (editor_command)
# ============================================================================


class EditorCommand(BaseModel):
    type: Literal[
        "focus_window",
        "hotkey",
        "type_text",
        "command_palette",
        "open_file",
        "goto_line",
        "open_folder",
        "save_file",
    ]
    payload: Dict[str, Any]
    id: Optional[str] = None
    audio_url: Optional[str] = None  # ElevenLabs 음성 URL
