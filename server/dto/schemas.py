from pydantic import BaseModel
from typing import Any, Dict, Optional


class MessageEnvelope(BaseModel):
    source: str  # "chrome", "local"
    type: str  # "frame", "audio", "status"
    data: Dict[str, Any]
