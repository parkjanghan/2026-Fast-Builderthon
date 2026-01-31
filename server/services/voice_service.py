"""
🔊 Voice Service - ElevenLabs TTS 음성 생성
"""

import os
import httpx
from typing import Optional


class VoiceService:
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환합니다.
    생성된 음성은 URL로 반환되어 로컬 에이전트에서 재생됩니다.
    """

    # 한국어 지원 음성 ID (Rachel - 자연스러운 여성 음성)
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    # 대안 음성들:
    # "EXAVITQu4vr4xnSDxMaL"  # Bella (여성)
    # "ErXwobaYiN019PkySvjV"  # Antoni (남성)
    # "MF3mGyEYCl7XYWbV9V6O"  # Elli (여성)

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"

        if not self.api_key:
            print("⚠️ [VoiceService] ELEVENLABS_API_KEY가 설정되지 않았습니다.")

    async def generate_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """
        텍스트를 음성으로 변환하고 오디오 URL을 반환합니다.

        Args:
            text: 음성으로 변환할 텍스트 (guidance)
            voice_id: 사용할 음성 ID (기본값: Rachel)

        Returns:
            오디오 스트림 URL 또는 None (실패 시)
        """
        if not self.api_key:
            print("❌ [VoiceService] API 키가 없어 음성 생성을 건너뜁니다.")
            return None

        if not text or len(text.strip()) == 0:
            return None

        voice = voice_id or self.DEFAULT_VOICE_ID
        url = f"{self.base_url}/text-to-speech/{voice}/stream"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # 한국어 지원
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    # 스트리밍 URL 생성 (ElevenLabs는 직접 스트림 반환)
                    # 실제 환경에서는 S3나 Cloud Storage에 업로드 후 URL 반환
                    # 여기서는 base64 data URL로 반환
                    import base64

                    audio_b64 = base64.b64encode(response.content).decode("utf-8")
                    audio_url = f"data:audio/mpeg;base64,{audio_b64}"

                    print(f"✅ [VoiceService] 음성 생성 완료 ({len(text)}자)")
                    return audio_url
                else:
                    print(f"❌ [VoiceService] API 오류: {response.status_code}")
                    print(f"   응답: {response.text[:200]}")
                    return None

        except httpx.TimeoutException:
            print("❌ [VoiceService] 요청 타임아웃")
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
