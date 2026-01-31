# ============================================================================
# 📁 audio_handler.py - ElevenLabs 오디오 재생 모듈
# ============================================================================
#
# 🎯 역할:
#   ElevenLabs에서 생성된 TTS 오디오 URL(MP3)을 받아 실시간으로 재생합니다.
#   서버에서 음성 URL이 오면 이 모듈이 다운로드 → 재생을 담당합니다.
#
# 📝 사용 예시:
#   from audio_handler import AudioHandler
#   
#   handler = AudioHandler()
#   handler.play_from_url("https://api.elevenlabs.io/.../audio.mp3")
#   handler.wait_until_done()  # 재생 완료까지 대기
#
# ============================================================================

import os
import time
import tempfile
import threading
from typing import Optional, Callable

import requests
import pygame

# 설정값 임포트
from config import (
    AUDIO_CACHE_DIR,
    AUDIO_DOWNLOAD_TIMEOUT,
    AUDIO_FREQUENCY,
    AUDIO_CHANNELS,
    AUDIO_BUFFER
)


class AudioHandler:
    """
    🔊 오디오 재생 핸들러
    
    ElevenLabs TTS 오디오를 다운로드하고 재생하는 클래스입니다.
    pygame.mixer를 사용하여 MP3 파일을 재생합니다.
    
    Attributes:
        is_playing (bool): 현재 오디오 재생 중인지 여부
        is_paused (bool): 현재 일시정지 상태인지 여부
    """
    
    def __init__(self):
        """
        AudioHandler 초기화
        
        pygame.mixer를 초기화하고 캐시 디렉토리를 생성합니다.
        """
        # pygame 믹서 초기화
        pygame.mixer.init(
            frequency=AUDIO_FREQUENCY,
            channels=AUDIO_CHANNELS,
            buffer=AUDIO_BUFFER
        )
        
        # 상태 플래그
        self.is_playing = False
        self.is_paused = False
        self._current_file: Optional[str] = None
        
        # 캐시 디렉토리 생성
        if not os.path.exists(AUDIO_CACHE_DIR):
            os.makedirs(AUDIO_CACHE_DIR)
            
        # 재생 완료 콜백 (선택사항)
        self._on_complete_callback: Optional[Callable] = None
        
        print("🔊 [AudioHandler] 오디오 핸들러 초기화 완료")
    
    # -------------------------------------------------------------------------
    # 🎵 핵심 재생 메서드들
    # -------------------------------------------------------------------------
    
    def play_from_url(self, audio_url: str, on_complete: Optional[Callable] = None) -> bool:
        """
        🌐 URL에서 오디오를 다운로드하고 재생합니다.
        
        Args:
            audio_url (str): MP3 오디오 파일의 URL (ElevenLabs 등)
            on_complete (Callable, optional): 재생 완료 시 호출할 콜백 함수
            
        Returns:
            bool: 재생 시작 성공 여부
            
        Example:
            handler.play_from_url(
                "https://api.elevenlabs.io/.../audio.mp3",
                on_complete=lambda: print("재생 완료!")
            )
        """
        try:
            print(f"🎵 [AudioHandler] 오디오 다운로드 시작: {audio_url[:50]}...")
            
            # 1. URL에서 오디오 파일 다운로드
            response = requests.get(
                audio_url,
                timeout=AUDIO_DOWNLOAD_TIMEOUT,
                stream=True
            )
            response.raise_for_status()
            
            # 2. 임시 파일로 저장
            temp_file = os.path.join(
                AUDIO_CACHE_DIR,
                f"audio_{int(time.time() * 1000)}.mp3"
            )
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ [AudioHandler] 다운로드 완료: {temp_file}")
            
            # 3. 재생
            return self.play_from_file(temp_file, on_complete)
            
        except requests.RequestException as e:
            print(f"❌ [AudioHandler] 다운로드 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ [AudioHandler] 오류 발생: {e}")
            return False
    
    def play_from_file(self, file_path: str, on_complete: Optional[Callable] = None) -> bool:
        """
        📂 로컬 파일에서 오디오를 재생합니다.
        
        Args:
            file_path (str): MP3 파일 경로
            on_complete (Callable, optional): 재생 완료 시 호출할 콜백 함수
            
        Returns:
            bool: 재생 시작 성공 여부
        """
        try:
            # 기존 재생 중지
            self.stop()
            
            # 파일 로드 및 재생
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            self.is_playing = True
            self.is_paused = False
            self._current_file = file_path
            self._on_complete_callback = on_complete
            
            print(f"▶️ [AudioHandler] 재생 시작: {os.path.basename(file_path)}")
            
            # 백그라운드에서 재생 완료 모니터링
            threading.Thread(target=self._monitor_playback, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ [AudioHandler] 재생 실패: {e}")
            return False
    
    def _monitor_playback(self):
        """
        🔄 백그라운드에서 재생 완료를 모니터링합니다.
        
        재생이 끝나면 콜백을 호출하고 상태를 업데이트합니다.
        """
        while pygame.mixer.music.get_busy() or self.is_paused:
            time.sleep(0.1)
        
        self.is_playing = False
        print("⏹️ [AudioHandler] 재생 완료")
        
        # 콜백 호출
        if self._on_complete_callback:
            try:
                self._on_complete_callback()
            except Exception as e:
                print(f"⚠️ [AudioHandler] 콜백 실행 중 오류: {e}")
    
    # -------------------------------------------------------------------------
    # ⏸️ 재생 컨트롤 메서드들
    # -------------------------------------------------------------------------
    
    def pause(self):
        """⏸️ 재생을 일시정지합니다."""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("⏸️ [AudioHandler] 일시정지")
    
    def resume(self):
        """▶️ 일시정지된 재생을 재개합니다."""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("▶️ [AudioHandler] 재생 재개")
    
    def stop(self):
        """⏹️ 재생을 완전히 중지합니다."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        print("⏹️ [AudioHandler] 재생 중지")
    
    def wait_until_done(self):
        """
        ⏳ 현재 재생이 완료될 때까지 대기합니다.
        
        이 메서드는 블로킹 방식으로, 오디오 재생이 끝날 때까지 반환하지 않습니다.
        '소리 먼저 재생 → 그다음 작업'의 순서를 보장하고 싶을 때 사용하세요.
        
        Example:
            handler.play_from_url(audio_url)
            handler.wait_until_done()  # 재생 완료까지 대기
            execute_mentor_logic(data)  # 그 다음 작업 실행
        """
        print("⏳ [AudioHandler] 재생 완료 대기 중...")
        while self.is_playing:
            time.sleep(0.1)
        print("✅ [AudioHandler] 대기 완료")
    
    # -------------------------------------------------------------------------
    # 🧹 정리 메서드
    # -------------------------------------------------------------------------
    
    def cleanup(self):
        """
        🧹 리소스를 정리합니다.
        
        프로그램 종료 시 호출하여 캐시 파일을 삭제하고 pygame을 정리합니다.
        """
        self.stop()
        
        # 캐시 파일 삭제
        try:
            for file in os.listdir(AUDIO_CACHE_DIR):
                file_path = os.path.join(AUDIO_CACHE_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("🧹 [AudioHandler] 캐시 정리 완료")
        except Exception as e:
            print(f"⚠️ [AudioHandler] 캐시 정리 중 오류: {e}")
        
        pygame.mixer.quit()
        print("🔇 [AudioHandler] pygame 종료")


# ============================================================================
# 🧪 테스트 코드 (직접 실행 시)
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 AudioHandler 테스트")
    print("=" * 50)
    
    handler = AudioHandler()
    
    # 테스트용 URL이 있다면 여기에 입력
    TEST_URL = None  # 예: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    if TEST_URL:
        print(f"\n테스트 URL: {TEST_URL}")
        handler.play_from_url(TEST_URL)
        handler.wait_until_done()
    else:
        print("\n⚠️ 테스트 URL이 설정되지 않았습니다.")
        print("   TEST_URL 변수에 MP3 URL을 입력하고 다시 실행하세요.")
    
    handler.cleanup()
    print("\n✅ 테스트 완료")
