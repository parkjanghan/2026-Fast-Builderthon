# ============================================================================
# 📁 audio_handler.py - 오디오 재생 모듈 (입 👄)
# ============================================================================
#
# 🎯 역할:
#   ElevenLabs에서 생성된 TTS 오디오 URL(MP3)을 받아 재생합니다.
#   playsound3 라이브러리 사용 (가볍고 Python 3.14 호환!)
#
# 📝 사용 예시:
#   from audio_handler import AudioHandler
#   
#   handler = AudioHandler()
#   handler.play_from_url("https://api.elevenlabs.io/.../audio.mp3")
#
# ============================================================================

import os
import time
import threading
from typing import Optional

import requests

# playsound3 임포트 (가벼운 오디오 재생 라이브러리, Python 3.14 호환)
try:
    import playsound3
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    print("⚠️ [AudioHandler] playsound3 미설치. 'python -m uv add playsound3' 실행 필요")

# 설정값
AUDIO_CACHE_DIR = ".audio_cache"
AUDIO_DOWNLOAD_TIMEOUT = 30


class AudioHandler:
    """
    🔊 오디오 재생 핸들러 (경량 버전 - playsound3)
    
    playsound3를 사용하여 MP3 파일을 재생합니다.
    pygame보다 훨씬 가볍고 Python 3.14와 완벽 호환됩니다.
    """
    
    def __init__(self):
        """AudioHandler 초기화"""
        self.is_playing = False
        self._playback_thread: Optional[threading.Thread] = None
        
        # 캐시 디렉토리 생성
        if not os.path.exists(AUDIO_CACHE_DIR):
            os.makedirs(AUDIO_CACHE_DIR)
        
        if PLAYSOUND_AVAILABLE:
            print("🔊 [AudioHandler] 오디오 핸들러 초기화 완료 (playsound3)")
        else:
            print("⚠️ [AudioHandler] playsound3 없이 초기화됨 (오디오 재생 불가)")
    
    # -------------------------------------------------------------------------
    # 🎵 재생 메서드
    # -------------------------------------------------------------------------
    
    def play_from_url_sync(self, audio_url: str) -> bool:
        """
        🔊 URL에서 오디오를 다운로드하고 재생합니다 (동기식).
        
        재생이 완료될 때까지 이 함수는 반환하지 않습니다.
        
        Args:
            audio_url (str): MP3 오디오 파일의 URL
            
        Returns:
            bool: 재생 성공 여부
        """
        if not PLAYSOUND_AVAILABLE:
            print("❌ [AudioHandler] playsound3가 없어 재생할 수 없습니다.")
            return False
        
        try:
            # 1. 다운로드
            file_path = self._download_audio(audio_url)
            if not file_path:
                return False
            
            # 2. 재생
            print(f"▶️ [AudioHandler] 재생 시작: {os.path.basename(file_path)}")
            self.is_playing = True
            
            # playsound3.playsound(file_path) 호출
            playsound3.playsound(file_path)
            
            self.is_playing = False
            print("⏹️ [AudioHandler] 재생 완료")
            return True
            
        except Exception as e:
            print(f"❌ [AudioHandler] 재생 오류: {e}")
            self.is_playing = False
            return False
    
    def play_from_url_async(self, audio_url: str) -> None:
        """
        🔊 URL에서 오디오를 비동기로 재생합니다.
        
        재생이 백그라운드에서 진행됩니다.
        """
        def _play():
            self.play_from_url_sync(audio_url)
        
        self._playback_thread = threading.Thread(target=_play, daemon=True)
        self._playback_thread.start()
        print("🎵 [AudioHandler] 비동기 재생 시작됨")
    
    # -------------------------------------------------------------------------
    # 📥 다운로드 헬퍼
    # -------------------------------------------------------------------------
    
    def _download_audio(self, audio_url: str) -> Optional[str]:
        """URL에서 오디오 파일을 다운로드합니다."""
        try:
            print(f"📥 [AudioHandler] 다운로드 시작...")
            
            response = requests.get(
                audio_url,
                timeout=AUDIO_DOWNLOAD_TIMEOUT,
                stream=True
            )
            response.raise_for_status()
            
            # 임시 파일로 저장
            temp_file = os.path.join(
                AUDIO_CACHE_DIR,
                f"audio_{int(time.time() * 1000)}.mp3"
            )
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ [AudioHandler] 다운로드 완료")
            return temp_file
            
        except requests.RequestException as e:
            print(f"❌ [AudioHandler] 다운로드 실패: {e}")
            return None
    
    # -------------------------------------------------------------------------
    # 🧹 정리
    # -------------------------------------------------------------------------
    
    def cleanup(self):
        """🧹 리소스를 정리합니다."""
        # 캐시 파일 삭제
        try:
            if os.path.exists(AUDIO_CACHE_DIR):
                for file in os.listdir(AUDIO_CACHE_DIR):
                    file_path = os.path.join(AUDIO_CACHE_DIR, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print("🧹 [AudioHandler] 캐시 정리 완료")
        except Exception as e:
            print(f"⚠️ [AudioHandler] 캐시 정리 오류: {e}")
        
        print("🔇 [AudioHandler] 종료")


# ============================================================================
# 🧪 테스트 코드 (직접 실행 시)
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 AudioHandler 테스트 (playsound3)")
    print("=" * 50)
    
    handler = AudioHandler()
    
    # 무료 테스트 MP3 URL (짧은 샘플)
    TEST_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    print(f"\n🔊 테스트 URL: {TEST_URL}")
    print("   5초만 재생 후 종료...")
    
    # 비동기 재생 테스트
    handler.play_from_url_async(TEST_URL)
    
    # 5초 대기
    time.sleep(5)
    
    handler.cleanup()
    print("\n✅ 테스트 완료")
