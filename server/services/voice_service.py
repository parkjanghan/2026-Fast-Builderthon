"""
🔊 Voice Service - ElevenLabs TTS 음성 생성 (스트리밍 방식)
"""

import os
import uuid
import httpx
from typing import Optional, Dict


# 설정
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:5000")


class VoiceService:
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환합니다.
    음성은 파일 저장 없이 동적 스트리밍 URL로 제공됩니다.
    """

    # 한국어 TTS 음성 (Bella - 부드럽고 자연스러운 여성 음성)
    DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # 대기 중인 TTS 요청 저장 (id -> text)
        self.pending_requests: Dict[str, str] = {}
        
        if not self.api_key:
            print("⚠️ [VoiceService] ELEVENLABS_API_KEY가 설정되지 않았습니다.")

    def queue_speech(self, text: str) -> Optional[str]:
        """
        TTS 요청을 큐에 등록하고 HTTP URL을 반환합니다.
        로컬이 이 URL을 호출하면 그때 음성이 생성됩니다.
        
        Args:
            text: 음성으로 변환할 텍스트 (guidance)
            
        Returns:
            TTS 스트리밍 URL 또는 None (실패 시)
        """
        if not self.api_key:
            print("❌ [VoiceService] API 키가 없어 음성 생성을 건너뜁니다.")
            return None
            
        if not text or len(text.strip()) == 0:
            return None

        # 고유 ID 생성 및 텍스트 저장
        request_id = str(uuid.uuid4())[:8]
        self.pending_requests[request_id] = text
        
        # HTTP URL 생성 (로컬이 이 URL을 호출하면 음성 스트리밍)
        audio_url = f"{SERVER_BASE_URL}/tts/{request_id}"
        
        print(f"✅ [VoiceService] TTS 요청 등록 ({len(text)}자) → {audio_url}")
        return audio_url

    async def stream_speech(self, request_id: str) -> Optional[bytes]:
        """
        등록된 TTS 요청 ID로 음성을 생성하고 바이너리를 반환합니다.
        
        Args:
            request_id: queue_speech에서 반환된 ID
            
        Returns:
            MP3 바이너리 데이터 또는 None
        """
        text = self.pending_requests.pop(request_id, None)
        if not text:
            print(f"❌ [VoiceService] 요청 ID {request_id}를 찾을 수 없습니다.")
            return None

        voice = self.DEFAULT_VOICE_ID
        url = f"{self.base_url}/text-to-speech/{voice}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        
        # 더 자연스럽고 여유로운(천천히 말하는) 한국어 TTS 설정
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # 다국어 모델 (한국어 지원)
            "voice_settings": {
                "stability": 0.8,           # 0.65 -> 0.8 (안정성을 높여 더 신중하고 천천히 말하게 함)
                "similarity_boost": 0.5,    # 0.6 -> 0.5 (모델의 여유 공간 확보)
                "style": 0.0,               # 0.35 -> 0.0 (표현력을 줄여 차분한 톤 유지)
                "use_speaker_boost": True   # 음성 선명도 유지
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    print(f"✅ [VoiceService] 음성 스트리밍 완료 ({len(text)}자)")
                    return response.content
                else:
                    print(f"❌ [VoiceService] API 오류: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ [VoiceService] 오류: {e}")
            return None


# 지연 초기화 싱글톤 (load_dotenv 이후에 생성되도록)
_voice_service: VoiceService | None = None


def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
