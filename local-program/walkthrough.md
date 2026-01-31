# 🚶 Part 3 로컬 에이전트 작업 내역 (Walkthrough)

## 📅 작업 개요
**목표**: Part 2(서버)와 통신하고 Windows를 제어하는 로컬 에이전트 구축
**주요 변경**: Python 3.14 마이그레이션, 오디오 모듈 경량화, 통신 프로토콜 표준화

## ✨ 주요 구현 사항

### 1. 최신 환경 구축 (2026년 표준)
- **Python 3.14.2** 적용 (최신 Stable 버전)
- **uv** 패키지 매니저 도입 (속도 및 의존성 관리 최적화)
- `pyproject.toml` 기반 프로젝트 관리

### 2. 오디오 모듈 경량화
- **Before**: `pygame-ce` (약 20MB, 게임 엔진이라 무거움)
- **After**: `playsound3` (초경량, Python 3.14 공식 지원)
- **이점**: 설치 속도 향상, 메모리 점유율 감소, MP3 재생 호환성 확보

### 3. 통신 프로토콜 표준화 (재준 님 서버 연동)
- **구조**: `source` + `data` 래핑 구조 적용
- **Uplink (로컬 -> 서버)**:
  ```json
  {
      "source": "local",
      "data": { "type": "local_status", "active_window": "...", ... }
  }
  ```
- **Downlink (서버 -> 로컬)**:
  ```json
  {
      "source": "server",
      "data": { "action": "GOTO_LINE", "params": {...} }
  }
  ```

### 4. 로직 단순화
- 'Pause-and-Explain' (자동 강의 일시정지) 로직 제거
- 사용자 수동 제어로 변경하여 코드 복잡도 제거

## 🛠️ 파일 구조

| 파일 | 역할 |
|------|------|
| `main.py` | 컨트롤 타워. 웹소켓 통신 및 로직 분배 담당. |
| `status_monitor.py` | '눈'. 현재 활성화된 윈도우 제목 등을 감시. |
| `audio_handler.py` | '입'. `playsound3`를 이용한 비동기 오디오 재생. |
| `config.py` | 서버 URL 등 설정 관리. |

## 🚀 실행 방법

```powershell
# 1. 의존성 동기화
python -m uv sync

# 2. 실행
python -m uv run python main.py
```

## 📝 멘토님 전달 사항
`main.py` 파일 하단의 `execute_mentor_logic` 함수에 `pywinauto` 코드를 작성해주시면 됩니다.

```python
def execute_mentor_logic(command_data):
    # 여기에 pywinauto 로직 구현
    pass
```
