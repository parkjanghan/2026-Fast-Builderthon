import os


class Config:
    # export로 주입된 환경변수를 읽어옵니다.
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    @classmethod
    def check_config(cls):
        if not cls.NVIDIA_API_KEY:
            print("❌ 에러: NVIDIA_API_KEY가 export되지 않았습니다.")
            return False
        print(f"✅ 환경변수 로드 완료 (Key: {cls.NVIDIA_API_KEY[:7]}...)")
        return True
