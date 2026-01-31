# 🖥️ Part 3: 로컬 에이전트 (Windows 제어)

> AI 해커톤 프로젝트 - Part 2 서버와 통신하며 Windows를 자동화하는 로컬 에이전트

## 📁 프로젝트 구조

```
part3/
├── .venv/                # 가상환경 (uv가 자동 생성)
├── .audio_cache/         # 다운로드한 오디오 캐시 (자동 생성)
├── pyproject.toml        # 📦 uv 프로젝트 설정 & 의존성
├── uv.lock               # 🔒 의존성 잠금 파일 (자동 생성)
├── config.py             # 🔧 설정값 (서버 URL, 이벤트 이름 등)
├── main.py               # 🚀 메인 엔트리포인트 (멘토님과의 접점!)
├── audio_handler.py      # 🔊 ElevenLabs 음성 재생
└── README.md             # 📖 이 파일
```

## 🚀 빠른 시작

### 1. 의존성 설치 (uv 사용)

```powershell
# 의존성 설치 + 가상환경 자동 생성
uv sync
```

### 2. 서버 URL 설정

`config.py` 파일을 열고 `SERVER_URL`을 Part 2 담당자(재준님)에게 받은 주소로 변경:

```python
SERVER_URL = "https://your-project.replit.app"  # ← 여기 수정!
```

### 3. 실행

```powershell
uv run python main.py
```

성공하면 아래처럼 출력됩니다:
```
✅ 서버 연결 성공!
   서버 주소: https://your-project.replit.app
```

## 🎯 역할 분담

| 담당자 | 역할 | 파일 |
|--------|------|------|
| 건호 님 | 서버 통신 + 오디오 재생 | `main.py`, `audio_handler.py`, `config.py` |
| 멘토님 | Windows 자동화 (pywinauto) | `main.py`의 `execute_mentor_logic()` |

## 📝 멘토님께

### 작업할 위치

`main.py` 파일에서 **"멘토님 전용 구역"**을 찾아주세요:

```python
def execute_mentor_logic(command_data: Dict[str, Any]):
    """
    🎯 멘토님 전용 함수 - pywinauto 로직이 들어갈 곳
    """
    # 여기에 Windows 자동화 코드를 작성해 주세요!
    pass
```

### pywinauto 설치

```powershell
# Windows 자동화 패키지 포함 설치
uv sync --extra windows
```

### 받을 수 있는 데이터 예시

```json
{
    "action": "type",
    "target": "editor",
    "content": "print('Hello, World!')",
    "line": 15,
    "audio_url": "https://api.elevenlabs.io/.../audio.mp3"
}
```

## 🔌 서버 이벤트 목록

| 방향 | 이벤트 이름 | 설명 |
|------|-------------|------|
| 서버 → 로컬 | `editor_sync` | 에디터 조작 명령 |
| 서버 → 로컬 | `lecture_pause` | 강의 일시정지 (Pause-and-Explain) |
| 서버 → 로컬 | `lecture_resume` | 강의 재개 |
| 로컬 → 서버 | `local_status` | 로컬 상태 보고 (1초마다) |
| 로컬 → 서버 | `task_complete` | 작업 완료 알림 |

## 🔧 uv 명령어 정리

```powershell
# 의존성 설치
uv sync

# pywinauto 포함 설치 (멘토님용)
uv sync --extra windows

# 실행
uv run python main.py

# 패키지 추가
uv add <패키지명>

# 패키지 제거
uv remove <패키지명>
```

## 🔧 트러블슈팅

### "서버 연결 실패" 오류

1. Part 2 서버가 실행 중인지 확인
2. `config.py`의 `SERVER_URL`이 올바른지 확인
3. 방화벽/네트워크 문제 확인

### 오디오가 재생되지 않음

1. 스피커/헤드폰 연결 확인
2. Windows 볼륨 설정 확인
3. pygame 설치 확인: `uv sync`

### 재연결이 안 됨

`config.py`에서 재연결 설정 확인:
```python
RECONNECT_ENABLED = True
RECONNECT_DELAY = 2
RECONNECT_MAX_ATTEMPTS = 10
```

## 📞 연락처

- **Part 1 (크롬 확장)**: [Part 1 담당자]
- **Part 2 (서버)**: 재준 님
- **Part 3 (로컬)**: 건호 님 + 멘토님
