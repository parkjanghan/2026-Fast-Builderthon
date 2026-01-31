# 🖥️ Part 3: 로컬 에이전트 (Windows 제어)

> AI 해커톤 프로젝트 - Part 2 서버와 통신하며 Windows를 자동화하는 로컬 에이전트

## 📁 프로젝트 구조

```
local-program/
├── .venv/                # 가상환경 (uv 자동 생성)
├── .audio_cache/         # 다운로드한 오디오 캐시
├── pyproject.toml        # 📦 uv 의존성 설정
├── uv.lock               # 🔒 잠금 파일
│
├── main.py               # 🎛️ 컨트롤 타워 (서버 통신 + 조합)
├── audio_handler.py      # 👄 입 (ElevenLabs 음성 재생) - playsound3 사용
├── status_monitor.py     # 👁️ 눈 (로컬 상태 감시)
├── config.py             # ⚙️ 설정값
└── README.md             # 📖 이 파일
```

## 🚀 빠른 시작

```powershell
cd c:\Users\mnb09\Desktop\2026-Fast-Builderthon\local-program

# 의존성 설치
python -m uv sync

# 실행
python -m uv run python main.py
```

## 📡 통신 프로토콜 (재준 님 형식)

### 📥 Downlink (서버 → 로컬)

```json
{
    "source": "server",
    "data": {
        "action": "GOTO_LINE",
        "params": { "line": 15 },
        "audio_url": "https://api.elevenlabs.io/.../audio.mp3",
        "timestamp": "2026-01-31 09:12:45"
    }
}
```

### 📤 Uplink (로컬 → 서버)

```json
{
    "source": "local",
    "data": {
        "type": "local_status",
        "active_window": "Visual Studio Code",
        "urgent": false,
        "timestamp": "2026-01-31 09:12:45"
    }
}
```

### 🛑 주요 액션 타입 (data.action)

| 액션 | 설명 | params 예시 |
|------|------|-------------|
| `GOTO_LINE` | 특정 줄로 이동 | `{ "line": 15 }` |
| `TYPE_CODE` | 코드 입력 | `{ "text": "print('hello')" }` |

## 🎯 역할 분담

| 담당자 | 역할 | 파일 |
|--------|------|------|
| 건호 님 | 통신 파이프라인 | `main.py`, `audio_handler.py`, `status_monitor.py` |
| 멘토님 | Windows 자동화 | `main.py`의 `execute_mentor_logic()` |

## 📝 멘토님께

### 작업할 위치

`main.py`에서 `execute_mentor_logic()` 함수를 찾아주세요:

```python
def execute_mentor_logic(command_data: Dict[str, Any]) -> Any:
    """
    🎯 멘토님 전용 함수 - pywinauto 로직이 들어갈 곳
    """
    action = command_data.get("action")
    params = command_data.get("params", {})
    
    # 여기에 pywinauto 코드를 작성해 주세요!
    pass
```

### pywinauto 설치

```powershell
python -m uv sync --extra windows
```

### 구현 예시

```python
from pywinauto import Application

def execute_mentor_logic(command_data):
    action = command_data.get("action")
    params = command_data.get("params", {})
    
    app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
    window = app.window(title_re=".*Visual Studio Code.*")
    
    if action == "GOTO_LINE":
        line = params.get("line", 1)
        window.type_keys("^g")  # Ctrl+G
        window.type_keys(str(line) + "{ENTER}")
        return True
    
    return False
```

## 📦 환경 정보

- **Python**: 3.14.2
- **websockets**: 16.0
- **requests**: 2.32.5
- **playsound3**: 3.3.1 (mp3 재생 경량화)
- **pygetwindow**: 0.0.9

## 📞 연락처

- **Part 1 (크롬 확장)**: [담당자]
- **Part 2 (서버)**: 재준 님
- **Part 3 (로컬)**: 건호 님 + 멘토님
