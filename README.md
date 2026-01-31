# SyncSight AI

> 실시간 AI 강의-에디터 싱크 에이전트

시각 장애 사용자의 학습 장벽을 제거하고, 일반 사용자에게 "핸즈프리" 코딩 학습 경험을 제공하는 실시간 AI 에이전트 시스템.

## 핵심 컨셉

강사의 강의 영상을 실시간으로 분석하여, 학생의 에디터를 자동으로 제어하고 음성 가이드를 제공합니다.

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Chrome Ext     │     │   Replit Server   │     │   Local Agent    │
│   👁️ Eyes        │────▶│   🧠 Brain        │────▶│   🤚 Hands       │
│                  │     │                  │     │                  │
│  - 프레임 캡처    │     │  - AI 분석       │     │  - 에디터 제어    │
│  - 메타데이터 전송 │     │  - TTS 생성      │     │  - 오디오 재생    │
│  - 재생 제어      │     │  - 명령 생성      │     │  - 상태 보고      │
│                  │     │                  │     │                  │
│  박장한           │     │  이재준           │     │  문건호 + 멘토    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## 아키텍처: Eyes-Brain-Hands

### Flow A: Eyes → Brain (원본 데이터)

Chrome Extension이 강의 영상 프레임을 1초 간격으로 캡처하여 서버로 전송합니다.

```json
{
  "event": "stream_frame",
  "image": "base64_encoded_frame",
  "metadata": { "timestamp": 1234567890 }
}
```

### Flow B: Brain → Hands/Eyes (명령)

서버가 AI 분석 결과를 기반으로 로컬 에이전트와 Chrome Extension에 명령을 전송합니다.

```json
{
  "action": "EDITOR_CONTROL",
  "command": "GOTO_LINE",
  "audio_url": "https://elevenlabs.io/.../audio.mp3",
  "params": { "line": 25 }
}
```

### Flow C: Hands → Brain (상태 보고)

로컬 에이전트가 현재 상태를 서버에 주기적으로 보고합니다.

```json
{
  "sender": "LOCAL_AGENT",
  "active_window": "VS Code",
  "status": "IDLE"
}
```

## 핵심 기능

### 1. Vision-to-Action
강사 화면 실시간 캡처 → 클릭, 타이핑, 파일 조작 식별 (NVIDIA VLM 시맨틱 분석)

### 2. Smart Pause-and-Explain
설명이 필요한 시점에서 강의 자동 일시정지 → ElevenLabs 음성 가이드 → 자동 재개

### 3. Universal Local Sync
pywinauto 기반 범용 Windows 에디터 제어 (VS Code, 점자 에디터 등)

## 프로젝트 구조

```
2026-Fast-Builderthon/
│
├── extension/              # Part 1: Chrome Extension (Eyes)
│   └── README.md           # 박장한 담당
│
├── server/                 # Part 2: Replit Server (Brain)
│   └── README.md           # 이재준 담당
│
├── local-program/          # Part 3: Local Agent (Hands)
│   ├── main.py             # WebSocket 클라이언트 + 이벤트 핸들러
│   ├── config.py           # 설정값 관리
│   ├── audio_handler.py    # ElevenLabs 오디오 재생
│   ├── controller/         # 에디터 제어 엔진 (멘토 구현)
│   │   ├── executor.py     # 명령 디스패치
│   │   ├── window.py       # 윈도우 관리 (pywinauto)
│   │   └── keyboard.py     # 키보드 제어
│   ├── models/             # Pydantic 스키마
│   │   ├── commands.py     # 명령 모델 (EditorCommand)
│   │   └── status.py       # 상태 모델 (LocalStatus)
│   ├── keymaps/            # 에디터별 키맵 프로파일
│   │   └── vscode.yaml     # VS Code 기본 단축키
│   ├── README.md           # Local Agent 상세 문서
│   └── AGENTS.md           # AI 에이전트 개발 가이드
│
└── README.md               # ← 이 파일
```

## 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| **Extension** | Manifest V3, WebSocket, chrome.tabCapture |
| **Server** | Replit, NVIDIA NIM (VLM), ElevenLabs, LangChain |
| **Local Agent** | Python 3.12, pywinauto, pygame, python-socketio, Pydantic |
| **통신** | WebSocket (Socket.IO) - 3자 실시간 통신 |
| **패키지 관리** | uv (Local Agent) |

## 통신 프로토콜

모든 통신은 WebSocket(Socket.IO) 기반입니다.

### 이벤트 정의

| 이벤트 | 방향 | 설명 |
|--------|------|------|
| `stream_frame` | Extension → Server | 캡처된 프레임 + 메타데이터 |
| `editor_sync` | Server → Local | 에디터 조작 명령 |
| `lecture_pause` | Server → Extension/Local | 강의 일시정지 (Pause-and-Explain) |
| `lecture_resume` | Server → Extension/Local | 강의 재개 |
| `local_status` | Local → Server | 로컬 상태 보고 (1초 간격) |
| `task_complete` | Local → Server | 명령 실행 완료 알림 |

### 명령 타입 (Server → Local)

| 타입 | 설명 | Payload 예시 |
|------|------|-------------|
| `focus_window` | 창 활성화 | `{"window_title": "Visual Studio Code"}` |
| `hotkey` | 단축키 전송 | `{"keys": ["ctrl", "g"]}` |
| `type_text` | 텍스트 입력 | `{"content": "print('hello')"}` |
| `command_palette` | 명령 팔레트 | `{"command": "Go to Line..."}` |
| `open_file` | 파일 열기 | `{"file_path": "C:/project/main.py"}` |
| `goto_line` | 줄 이동 | `{"line_number": 25}` |

## 차별화 전략

| vs | SyncSight AI |
|----|-------------|
| 단순 OCR | NVIDIA VLM으로 시맨틱 분석 (맥락, 메뉴 클릭, 커서 위치 이해) |
| 단일 에디터 솔루션 | pywinauto로 모든 Windows 앱 범용 제어 |
| 음성 간섭 | Pause-and-Explain: 강의 일시정지 후 설명, 음향 충돌 제거 |

## 개발 일정

| 단계 | 내용 |
|------|------|
| Phase 2 | 3자 WebSocket 통신 완성 (Chrome-Server-Local) |
| Phase 3 | Pause-and-Explain + pywinauto 제어 통합 |
| Phase 4 | 전체 워크플로우 테스트 + 시각장애인 페르소나 데모 영상 |
| Phase 5 | 최종 발표 + Replit 라이브 URL 검증 |

## 팀 구성

| 이름 | 역할 | 담당 파트 |
|------|------|----------|
| 박장한 | Chrome Extension 개발 | `extension/` - 프레임 캡처, 재생 제어 |
| 이재준 | 서버 & AI 파이프라인 | `server/` - VLM 분석, TTS 생성, 명령 라우팅 |
| 문건호 | 로컬 에이전트 통신 | `local-program/` - WebSocket, 오디오, 설정 |
| 멘토 | 로컬 에이전트 제어 | `local-program/controller/` - Windows 자동화 |

## 빠른 시작 (Local Agent)

```bash
cd local-program

# 의존성 설치
uv sync

# 실행 (서버 URL은 config.py에서 설정)
uv run python main.py
```

각 파트별 상세 문서는 해당 디렉토리의 README.md를 참고하세요.
