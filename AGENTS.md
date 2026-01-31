# AGENTS.md - SyncSight AI 프로젝트 전체 가이드

이 문서는 AI 에이전트가 SyncSight AI 프로젝트에서 작업할 때 필요한 전체 컨텍스트를 제공합니다.

## 프로젝트 개요

SyncSight AI는 실시간 강의 영상 분석 → 에디터 자동 제어 시스템입니다.
3파트 아키텍처(Eyes-Brain-Hands)로 구성되며, 각 파트는 독립적으로 개발됩니다.

## 아키텍처

```
Chrome Extension (Eyes) ──WebSocket──▶ Replit Server (Brain) ──WebSocket──▶ Local Agent (Hands)
     박장한                                 이재준                          문건호 + 멘토
```

### 데이터 흐름

1. Extension이 강의 영상 프레임을 캡처하여 Server로 전송
2. Server가 NVIDIA VLM으로 분석, ElevenLabs로 TTS 생성
3. Server가 Local Agent에 에디터 제어 명령 + 오디오 URL 전송
4. Local Agent가 오디오 재생 후 Windows 에디터 제어 실행
5. Local Agent가 상태를 Server에 보고 (1초 간격)

## 디렉토리 구조 & 소유권

```
2026-Fast-Builderthon/
├── extension/              # 박장한 소유 - 수정 금지
├── server/                 # 이재준 소유 - 수정 금지
├── local-program/          # 문건호 + 멘토 소유
│   ├── main.py             # 문건호 소유 (execute_mentor_logic 본문만 수정 가능)
│   ├── config.py           # 문건호 소유 (하단 멘토 설정 구역만 추가 가능)
│   ├── audio_handler.py    # 문건호 소유 - 수정 금지
│   ├── controller/         # 멘토 소유 - 자유롭게 수정
│   ├── models/             # 멘토 소유 - 자유롭게 수정
│   └── keymaps/            # 멘토 소유 - 자유롭게 수정
├── README.md               # 루트 프로젝트 문서
└── AGENTS.md               # ← 이 파일
```

### 소유권 규칙

| 영역 | 소유자 | AI 에이전트 수정 가능 여부 |
|------|--------|--------------------------|
| `extension/` | 박장한 | **절대 금지** |
| `server/` | 이재준 | **절대 금지** |
| `local-program/main.py` | 문건호 | `execute_mentor_logic()` 본문만 |
| `local-program/config.py` | 문건호 | 하단 멘토 설정 구역만 |
| `local-program/audio_handler.py` | 문건호 | **절대 금지** |
| `local-program/controller/` | 멘토 | **자유** |
| `local-program/models/` | 멘토 | **자유** |
| `local-program/keymaps/` | 멘토 | **자유** |

## 통신 프로토콜

모든 통신은 WebSocket(Socket.IO) 기반. JSON을 bytes로 변환하여 전송.

### 이벤트 목록

| 이벤트 | 방향 | 정의 위치 |
|--------|------|----------|
| `stream_frame` | Extension → Server | extension/ |
| `editor_sync` | Server → Local | `config.py:EVENT_EDITOR_SYNC` |
| `lecture_pause` | Server → Local/Extension | `config.py:EVENT_LECTURE_PAUSE` |
| `lecture_resume` | Server → Local/Extension | `config.py:EVENT_LECTURE_RESUME` |
| `local_status` | Local → Server | `config.py:EVENT_LOCAL_STATUS` |
| `task_complete` | Local → Server | `config.py:EVENT_TASK_COMPLETE` |

### 명령 스키마 (Pydantic)

명령 스키마는 `local-program/models/commands.py`에 정의되어 있습니다.
서버와 공유 가능하도록 Pydantic v2로 작성되었습니다.

```python
from models.commands import EditorCommand

# 서버에서 보내는 레거시 형식
legacy = {"action": "type", "content": "hello", "line": 15}

# Pydantic 모델로 변환
command = EditorCommand.from_legacy(legacy)
```

6가지 명령 타입: `focus_window`, `hotkey`, `type_text`, `command_palette`, `open_file`, `goto_line`

## 기술적 제약사항

### 1. Electron 앱 한계

VS Code는 Electron 기반이라 pywinauto의 UIA 트리가 에디터 내부 요소를 노출하지 않습니다.

**해결 전략 (하이브리드)**:
- 창 관리: pywinauto (find_window, focus_window)
- 에디터 제어: 키보드 단축키 (Ctrl+G, Ctrl+Shift+P 등)
- 키맵 프로파일: `keymaps/vscode.yaml`로 에디터별 단축키 관리

### 2. pywinauto 특수문자

`type_keys()`는 `{}+^%~()[]`를 메타키로 해석합니다.
텍스트 입력 시 반드시 이스케이프 처리하거나 keyboard 라이브러리를 사용하세요.

### 3. Threading

`main.py`는 sync + threading 패턴을 사용합니다.
**async/await 패턴 도입 금지** — pygame과 pywinauto가 동기 라이브러리입니다.

### 4. pygame 빌드

Windows 환경에서 MSYS2가 없으면 pygame 빌드가 실패할 수 있습니다.
이는 환경 이슈이며 코드 문제가 아닙니다.

## 코드 스타일 (local-program)

local-program은 문건호가 확립한 코드 스타일을 따릅니다:

1. **한글 주석**: 모든 주석은 한국어로 작성
2. **이모지 프리픽스**: 섹션/상태 표시 (🎯, 🔧, 📝, ⚠️, ✅, ❌)
3. **섹션 헤더**: `# ====` 구분선으로 모듈 구역 분리
4. **Docstring**: 모든 함수에 한글 docstring + Examples 섹션
5. **Type Hints**: 모든 함수 시그니처에 타입 힌트 필수

## 개발 우선순위

local-program 멘토 구현 순서:

1. `controller/window.py` — pywinauto 창 관리 (find, focus, is_running)
2. `controller/keyboard.py` — 키보드 입력 시뮬레이션 (hotkey, type_text, command_palette)
3. `controller/executor.py` — 핸들러 메서드 구현 (_handle_* 메서드들)

현재 모든 핸들러는 `NotImplementedError`로 스캐폴딩되어 있습니다.
디스패치 로직(execute 메서드)은 이미 작동합니다.

## 의존성

### local-program

```toml
python = ">=3.12"
dependencies = [
    "python-socketio[client]>=5.10.0",  # WebSocket 통신
    "requests>=2.31.0",                 # HTTP 요청
    "pygame>=2.5.0",                    # 오디오 재생
    "pydantic>=2.0",                    # 데이터 검증
    "pyyaml>=6.0",                      # 키맵 설정
    "pywinauto>=0.6.8",                 # Windows 자동화
    "pygetwindow>=0.0.9",              # 활성 창 정보
]
```

패키지 관리: `uv`

### 금지 의존성

다음 의존성은 추가하지 마세요:
- `click`, `typer` — CLI 불필요
- `loguru`, `rich` — 기존 print 패턴 유지
- `asyncio`, `aiohttp` — sync 패턴 유지

## 파트별 상세 문서

| 파트 | 문서 위치 |
|------|----------|
| Local Agent 상세 | `local-program/README.md` |
| Local Agent AI 가이드 | `local-program/AGENTS.md` |
| Extension | `extension/README.md` (TBD) |
| Server | `server/README.md` (TBD) |

각 파트에서 작업할 때는 **반드시 해당 파트의 AGENTS.md를 먼저 읽으세요.**
