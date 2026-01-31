"""
🔊 Voice Service - ElevenLabs TTS 음성 생성
"""

import os
import time
from pathlib import Path
from typing import Optional

import httpx


class VoiceService:
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환합니다.
    생성된 음성은 서버의 /audio/{filename} 엔드포인트를 통해 URL로 제공됩니다.
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

        # 오디오 캐시 디렉토리 (main.py의 AUDIO_DIR과 반드시 동일해야 함)
        # voice_service.py → services/ → server/ = server/.audio_cache
        self.audio_dir = Path(__file__).parent.parent / ".audio_cache"
        self.audio_dir.mkdir(exist_ok=True)
        print(f"📁 [VoiceService] 오디오 캐시: {self.audio_dir.resolve()}")

        # 서버 공개 URL (Replit 환경 자동 감지)
        self.server_url = os.getenv("SERVER_URL", "").rstrip("/")
        if not self.server_url:
            # Replit 환경에서 자동 감지
            replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
            if replit_domain:
                self.server_url = f"https://{replit_domain}"

        if not self.api_key:
            print("⚠️ [VoiceService] ELEVENLABS_API_KEY가 설정되지 않았습니다.")

    async def generate_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """
        텍스트를 음성으로 변환하고 오디오 URL을 반환합니다.

        Args:
            text: 음성으로 변환할 텍스트 (guidance)
            voice_id: 사용할 음성 ID (기본값: Rachel)

        Returns:
            오디오 파일 URL (예: https://server.replit.app/audio/tts_1234.mp3)
            또는 None (실패 시)
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
                    # 파일로 저장하고 HTTP URL 반환
                    filename = f"tts_{int(time.time() * 1000)}.mp3"
                    file_path = self.audio_dir / filename

                    with open(file_path, "wb") as f:
                        f.write(response.content)

                    # 서버 URL + /audio/filename 형태로 반환
                    if self.server_url:
                        audio_url = f"{self.server_url}/audio/{filename}"
                    else:
                        # SERVER_URL이 없으면 상대 경로 (같은 호스트)
                        audio_url = f"/audio/{filename}"

                    print(
                        f"✅ [VoiceService] 음성 생성 완료 "
                        f"({len(text)}자, {len(response.content)}bytes) → {filename}"
                    )
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

    def cleanup_old_files(self, max_age_seconds: int = 300):
        """5분 이상 된 오래된 오디오 파일 삭제"""
        now = time.time()
        for f in self.audio_dir.glob("tts_*.mp3"):
            if now - f.stat().st_mtime > max_age_seconds:
                f.unlink(missing_ok=True)


# 지연 초기화 싱글톤 (load_dotenv 이후에 생성되도록)
_voice_service: VoiceService | None = None


def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
