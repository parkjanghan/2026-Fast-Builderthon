# SyncSight AI - Local Automation Agent

> Part 3: The "Hands" of the Eyes-Brain-Hands Architecture

SyncSight AI is an AI-powered lecture video synchronization system that helps students follow along with coding tutorials by automatically controlling their local development environment. This local agent serves as the "Hands" component, receiving commands from the server (Brain) and executing them on the Windows machine.

## Architecture Overview

SyncSight AI consists of three interconnected parts:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Chrome Ext     │      │  Replit Server  │      │  Local Agent    │
│  (Eyes)         │─────▶│  (Brain)        │─────▶│  (Hands)        │
│  박장한         │      │  이재준         │      │  문건호 + Mentor│
└─────────────────┘      └─────────────────┘      └─────────────────┘
     Watches video          Processes AI           Controls editors
     Detects events         Generates commands     Plays audio
```

### Component Roles

1. **Chrome Extension (Eyes)**: Monitors lecture video playback, detects code changes, sends events to server
2. **Replit Server (Brain)**: Receives events, processes with AI, generates editor commands and TTS audio
3. **Local Agent (Hands)**: Receives commands via WebSocket, plays audio guidance, controls Windows editors

### Communication Flow

```
Video Event → Chrome Extension → Server (WebSocket)
                                     ↓
                               AI Processing
                               TTS Generation
                                     ↓
                     Command + Audio URL → Local Agent
                                     ↓
                               Audio Playback
                               Editor Control
```

## Directory Structure

```
local-program/
├── main.py                    # 🚀 Entry point - WebSocket client, event handlers
├── config.py                  # 🔧 Configuration - server URL, event names, settings
├── audio_handler.py           # 🔊 Audio playback - ElevenLabs TTS streaming
│
├── controller/                # 🎮 Editor control modules
│   ├── __init__.py           # Package exports
│   ├── executor.py           # Command dispatcher, keymap loader
│   ├── window.py             # Window management (pywinauto)
│   └── keyboard.py           # Keyboard control (keyboard library)
│
├── models/                    # 📦 Pydantic v2 schemas
│   ├── __init__.py           # Package exports
│   ├── commands.py           # EditorCommand (server → local)
│   └── status.py             # LocalStatus (local → server)
│
├── keymaps/                   # ⌨️ Editor keyboard shortcuts
│   └── vscode.yaml           # VS Code default keymap
│
├── tests/                     # 🧪 Automated test suite
│   ├── conftest.py            # Pytest fixtures (mocked controllers)
│   ├── test_controller.py     # Dispatch routing, state transitions
│   ├── test_models.py         # EditorCommand, LocalStatus validation
│   ├── test_edge_cases.py     # Window edge cases, error handling
│   ├── test_scenarios.py      # Real-world command sequences
│   └── test_integration.py    # E2E tests (requires VS Code)
│
├── pyproject.toml            # 📦 uv project config & dependencies
├── uv.lock                   # 🔒 Dependency lock file
├── .audio_cache/             # 🎵 Downloaded audio files (auto-created)
└── README.md                 # 📖 This file
```

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

### Prerequisites

- Python 3.12 or higher
- Windows OS (pywinauto dependency)
- uv package manager

### Install Dependencies

```powershell
# Install all dependencies and create virtual environment
uv sync
```

This will install:
- `websockets` - Pure WebSocket communication with server
- `requests` - HTTP client for audio downloads
- `pygame` - Audio playback
- `pydantic` - Data validation and schemas
- `pyyaml` - Keymap file parsing
- `pywinauto` - Windows automation
- `pygetwindow` - Window management
- `keyboard` - Keyboard input simulation (text typing, hotkeys)

## Configuration

Edit `config.py` to match your environment:

```python
# Server URL (get from 이재준)
SERVER_URL = "https://your-project.replit.app"

# Reconnection settings
RECONNECT_ENABLED = True
RECONNECT_DELAY = 2
RECONNECT_MAX_ATTEMPTS = 10

# Status reporting interval (seconds)
STATUS_REPORT_INTERVAL = 1.0
```

### Mentor Settings

The following mentor-specific settings are configured in the bottom section of `config.py`:

```python
# 멘토 설정 (config.py 하단)
TARGET_EDITOR = "Visual Studio Code"
TARGET_PROJECT_PATH = ""  # 다중 VS Code 창 시 프로젝트 선택용
AUTO_LAUNCH_ENABLED = True
APP_LAUNCH_TIMEOUT = 15
VSCODE_EXE_PATH = r"C:\Users\...\Code.exe"
```

These settings control window selection, auto-launch behavior, and editor-specific paths.

## Running the Agent

```powershell
# Run with uv
uv run python main.py
```

Expected output:
```
============================================================
🚀 Part 3: 로컬 에이전트 시작!
============================================================
   서버 URL: https://your-project.replit.app
   자동 재연결: ✅ 활성화
   상태 보고 간격: 1.0초
============================================================

🔌 서버 연결 시도 중...
============================================================
✅ 서버 연결 성공!
   서버 주소: https://your-project.replit.app
   연결 시간: 2026-01-31 12:00:00
============================================================
📊 상태 보고 시작 (간격: 1.0초)

💡 Ctrl+C로 종료할 수 있습니다.
```

## Module Documentation

### `main.py` - Entry Point (건호's Module)

**Role**: WebSocket client that connects to server, receives commands, orchestrates audio + control flow

**Key Functions**:
- `execute_mentor_logic(command_data)`: Entry point for mentor's pywinauto logic
- `get_local_status()`: Returns current local state (active window, pause status)
- Event handlers: `on_editor_sync`, `on_lecture_pause`, `on_lecture_resume`

**Flow**:
1. Connect to server via WebSocket
2. Start status reporting thread (1Hz)
3. Listen for `editor_sync` events
4. On command received:
   - Play audio if `audio_url` present
   - Call `execute_mentor_logic()` with command data
   - Send `task_complete` event to server

### `config.py` - Configuration (건호's Module)

**Role**: Centralized configuration for server connection, events, audio settings

**Key Settings**:
- `SERVER_URL`: Replit server address
- `CONNECTION_TIMEOUT`, `RECONNECT_*`: WebSocket 연결 설정
- `AUDIO_*`: pygame mixer settings, cache directory
- `STATUS_REPORT_INTERVAL`: How often to send status updates

### `audio_handler.py` - Audio Playback (건호's Module)

**Role**: Downloads and plays ElevenLabs TTS audio from URLs

**Key Methods**:
- `play_from_url(audio_url)`: Download MP3 from URL and play
- `wait_until_done()`: Block until playback completes
- `pause()` / `resume()` / `stop()`: Playback controls
- `cleanup()`: Delete cached audio files

**Usage**:
```python
handler = AudioHandler()
handler.play_from_url("https://api.elevenlabs.io/.../audio.mp3")
handler.wait_until_done()  # Wait for audio to finish
```

### `controller/` - Editor Control (Mentor's Modules)

#### `controller/executor.py` - Command Dispatcher

**Role**: Receives `EditorCommand` objects, dispatches to appropriate handlers

**Key Methods**:
- `execute(command: EditorCommand)`: Main dispatcher (uses match/case)
- `get_status()`: Returns `LocalStatus` object
- `_handle_*()`: Handler methods for each command type

**Command Types**:
1. `focus_window`: Bring target window to foreground
2. `hotkey`: Send keyboard shortcut (Ctrl+G, etc.)
3. `type_text`: Type text into editor
4. `command_palette`: Open VS Code command palette and execute command
5. `open_file`: Open file in editor
6. `goto_line`: Jump to specific line number

**Keymap Loading**:
```python
controller = EditorController(keymap_path="keymaps/vscode.yaml")
# Loads shortcuts from YAML: goto_line: ["ctrl", "g"]
```

#### `controller/window.py` - Window Management

**Role**: Find, focus, and query Windows application windows

**Key Methods** (fully implemented):
- `find_window(name, project_hint)`: Find window by title, with multi-window project filtering
- `find_all_windows(name)`: Returns all matching window titles
- `focus_window(name, project_hint)`: Activate and bring window to front, handles minimized
- `ensure_window(name, project_hint, launch_cmd, auto_launch, timeout, poll_interval)`: Core method: find → auto-launch if needed → poll until ready → focus
- `launch_app(name, launch_cmd, project_hint)`: Auto-detects VS Code/Notepad, supports custom launch commands
- `is_app_running(name)`: Check via window titles (pygetwindow)
- `get_active_window_title()`: Returns current active window title

**Implementation Strategy**:
Uses pywinauto for window management:
```python
from pywinauto import Application
app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
main_window = app.window(title_re=".*Visual Studio Code.*")
main_window.set_focus()
```

#### `controller/keyboard.py` - Keyboard Control

**Role**: Send keyboard input to active window

**Key Methods** (fully implemented):
- `send_hotkey(keys)`: Uses keyboard.send() with "+" separator
- `type_text(text)`: Uses keyboard.write() (avoids pywinauto special char issues)
- `send_command_palette(command)`: Ctrl+Shift+P → type → Enter

**Implementation Strategy**:
Hybrid approach due to Electron app limitations:
- **Window management**: pywinauto (reliable for focus/activation)
- **Keyboard input**: `keyboard` library (more reliable for Electron apps like VS Code)

**Special Character Escaping**:
pywinauto's `type_keys()` treats `{}+^%` as special:
```python
# BAD: Will fail
window.type_keys("print('hello')")  # Parentheses cause issues

# GOOD: Use keyboard library instead
import keyboard
keyboard.write("print('hello')")
```

### `models/` - Data Schemas (Pydantic v2)

#### `models/commands.py` - Server → Local Commands

**Role**: Validate and parse commands from server

**Main Model**: `EditorCommand`
```python
class EditorCommand(BaseModel):
    type: Literal["focus_window", "hotkey", "type_text", ...]
    payload: Dict[str, Any]
    id: Optional[str]
    audio_url: Optional[str]
```

**Payload Models**:
- `FocusWindowPayload`: `{window_title: str}`
- `HotkeyPayload`: `{keys: List[str]}`
- `TypeTextPayload`: `{content: str}`
- `CommandPalettePayload`: `{command: str}`
- `OpenFilePayload`: `{file_path: str}`
- `GotoLinePayload`: `{line_number: int}`

**Legacy Adapter**:
```python
# Convert old dict format to EditorCommand
legacy = {"action": "type", "content": "hello"}
cmd = EditorCommand.from_legacy(legacy)
assert cmd.type == "type_text"
assert cmd.payload["content"] == "hello"
```

#### `models/status.py` - Local → Server Status

**Role**: Report local agent state to server

**Model**: `LocalStatus`
```python
class LocalStatus(BaseModel):
    active_window: str
    target_app_running: bool
    status: Literal["IDLE", "BUSY"]
    current_keymap: str
    timestamp: float
```

### `keymaps/` - Editor Keyboard Shortcuts

**Role**: Define editor-specific keyboard shortcuts in YAML

**Format** (`vscode.yaml`):
```yaml
editor: "Visual Studio Code"
window_title_pattern: ".*Visual Studio Code.*"

shortcuts:
  goto_line: ["ctrl", "g"]
  command_palette: ["ctrl", "shift", "p"]
  save: ["ctrl", "s"]
  # ... more shortcuts
```

**Usage**:
```python
controller = EditorController(keymap_path="keymaps/vscode.yaml")
# controller.keymap["shortcuts"]["goto_line"] → ["ctrl", "g"]
```

## Command Interface

The local agent receives 6 types of commands from the server:

### 1. Focus Window
Bring target application window to foreground.

```json
{
  "type": "focus_window",
  "payload": {
    "window_title": "Visual Studio Code"
  }
}
```

### 2. Hotkey
Send keyboard shortcut combination.

```json
{
  "type": "hotkey",
  "payload": {
    "keys": ["ctrl", "g"]
  }
}
```

### 3. Type Text
Type text into active window.

```json
{
  "type": "type_text",
  "payload": {
    "content": "print('Hello, World!')"
  }
}
```

### 4. Command Palette
Open VS Code command palette and execute command.

```json
{
  "type": "command_palette",
  "payload": {
    "command": "Go to Line"
  }
}
```

### 5. Open File
Open file in editor.

```json
{
  "type": "open_file",
  "payload": {
    "file_path": "C:\\Users\\student\\project\\main.py"
  }
}
```

### 6. Go to Line
Jump to specific line number.

```json
{
  "type": "goto_line",
  "payload": {
    "line_number": 42
  }
}
```

## Development (For Mentor)

### Code Ownership

**DO NOT MODIFY** (건호's modules):
- `main.py` - WebSocket client and event handling
- `config.py` - Configuration management
- `audio_handler.py` - Audio playback logic

**IMPLEMENTED** (Mentor's scope) - All complete:
- `controller/window.py` - All methods fully implemented
- `controller/keyboard.py` - All methods fully implemented
- `controller/executor.py` - All handler methods fully implemented

## Testing

### Automated Tests (pytest)

The project includes a comprehensive test suite covering all controller functionality:

```powershell
cd local-program

# Run all unit tests (excludes integration tests)
.venv\Scripts\pytest.exe tests/ -v -m "not integration"
# Result: 74 passed, 6 deselected

# Run ALL tests including integration (requires VS Code running)
.venv\Scripts\pytest.exe tests/ -v

# Run specific test file
.venv\Scripts\pytest.exe tests/test_models.py -v

# Run with short output
.venv\Scripts\pytest.exe tests/ -m "not integration" -q
```

**Test breakdown**:

| File | Tests | Coverage |
|------|-------|----------|
| test_models.py | 21 | EditorCommand, from_legacy, payloads, LocalStatus |
| test_controller.py | 11 | Dispatch routing, IDLE/BUSY state, get_status |
| test_edge_cases.py | 20 | Window selection, app detection, ensure_window, launch_app |
| test_scenarios.py | 12 | New file, hello world, file+goto, formatting, full session |
| test_integration.py | 6 | E2E flows (marked @pytest.mark.integration, requires VS Code) |

**Code Quality (ruff)**:

```powershell
# Lint check
.venv\Scripts\ruff.exe check controller/ models/ tests/

# Format check
.venv\Scripts\ruff.exe format --check controller/ models/ tests/
```

### Manual Verification (Live Testing)

For testing with actual VS Code and real window interactions:

#### 1. Window Management Test

```python
# In Python REPL or test script
from controller.window import WindowManager

wm = WindowManager()

# Open VS Code first, then run:
print("Test 1: Find window")
window = wm.find_window("Visual Studio Code")
assert window is not None, "Failed to find VS Code"
print("✅ Pass")

print("Test 2: Focus window")
result = wm.focus_window("Visual Studio Code")
assert result == True, "Failed to focus VS Code"
print("✅ Pass")

print("Test 3: Check if running")
result = wm.is_app_running("Visual Studio Code")
assert result == True, "VS Code should be running"
print("✅ Pass")

print("Test 4: Get active window")
title = wm.get_active_window_title()
assert "Visual Studio Code" in title, f"Expected VS Code, got {title}"
print("✅ Pass")
```

#### 2. Keyboard Control Test

```python
# Open VS Code and focus it first
from controller.keyboard import KeyboardController
import time

kb = KeyboardController()

print("Test 1: Send hotkey (Ctrl+G)")
kb.send_hotkey(["ctrl", "g"])
time.sleep(0.5)
# Verify: Go to Line dialog should appear
input("Press Enter if Go to Line dialog appeared...")
kb.send_hotkey(["esc"])  # Close dialog
print("✅ Pass")

print("Test 2: Type text")
kb.type_text("# Test comment")
time.sleep(0.5)
# Verify: Text should appear in editor
input("Press Enter if text appeared...")
print("✅ Pass")

print("Test 3: Command palette")
kb.send_command_palette("Go to Line")
time.sleep(0.5)
# Verify: Go to Line dialog should appear
input("Press Enter if dialog appeared...")
kb.send_hotkey(["esc"])
print("✅ Pass")
```

#### 3. End-to-End Test

```bash
# Terminal 1: Start local agent
uv run python main.py

# Terminal 2: Send test command (requires server running)
# Or manually trigger from server UI
```

Verify:
1. Audio plays (if audio_url provided)
2. Editor action executes correctly
3. `task_complete` event sent to server
4. No errors in console

## Known Issues

### pygame Build Failure

**Issue**: pygame fails to build on some Windows systems due to missing MSYS2/pacman.

**Error**:
```
error: `pacman` must be installed and on PATH to install pygame from source.
```

**Impact**: May block `uv sync` on some systems.

**Workaround**: 
- Development: Use pre-built pygame wheels or install MSYS2
- Testing: Automated tests work fine with mocked dependencies
- Deployment: Use environment with MSYS2 installed, or use pre-built pygame wheels

**Status**: Does not affect production deployment on properly configured systems.

### Emoji Encoding in Terminal

**Issue**: Korean comments with emoji prefixes may display incorrectly in Windows terminal (cp949 codec).

**Impact**: Cosmetic only, does not affect functionality.

**Workaround**: Use UTF-8 compatible terminal (Windows Terminal, VS Code integrated terminal).

## Contributing

### Code Style

This project follows specific conventions established by 건호:

1. **Korean Comments**: All comments in Korean (한글 주석)
2. **Emoji Prefixes**: Section headers use emoji for visual scanning
3. **Section Headers**: Use `# ===` style separators
4. **Docstrings**: Include Examples section

Example:
```python
# ============================================================================
# 📁 module_name.py - 모듈 설명
# ============================================================================
#
# 🎯 역할:
#   이 모듈의 역할 설명
#
# ============================================================================

def function_name():
    """
    🔧 함수 설명
    
    Args:
        param: 파라미터 설명
    
    Returns:
        반환값 설명
    
    Example:
        result = function_name()
    """
    pass
```

### Scope Boundaries

**Mentor's Scope**:
- Implement controller modules (window, keyboard, executor handlers)
- Add pywinauto/keyboard logic
- Test and verify editor control

**Out of Scope**:
- Server communication (건호's responsibility)
- Audio playback (건호's responsibility)
- Configuration management (건호's responsibility)
- Adding async/await (project uses synchronous threading)
- Adding extra dependencies (stick to pyproject.toml)

### Pull Request Guidelines

1. Test manually with VS Code before submitting
2. Ensure no changes to `main.py`, `config.py`, `audio_handler.py`
3. Follow existing code style (Korean comments, emoji prefixes)
4. Include test procedure in PR description

## License

AI Hackathon Project - Educational Use

## Team

- **Part 1 (Chrome Extension)**: 박장한
- **Part 2 (Replit Server)**: 이재준
- **Part 3 (Local Agent)**: 문건호 (comms/audio) + Mentor (controller)
