from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal, List


# --- 기존 Envelope 유지 ---
class MessageEnvelope(BaseModel):
    source: str  # "chrome", "local"
    type: str  # "frame", "status", "ack"
    data: Dict[str, Any]


# --- 제공해주신 EditorCommand 스키마 통합 ---
class EditorCommand(BaseModel):
    type: Literal["focus_window", "hotkey", "type_text", "command_palette",
                  "open_file", "goto_line", "open_folder", "save_file"]
    payload: Dict[str, Any]
    id: Optional[str] = None
    audio_url: Optional[str] = None  # ElevenLabs에서 생성된 음성 경로
