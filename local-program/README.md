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
Video Event → Chrome Extension → Server (Socket.IO)
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
│   └── keyboard.py           # Keyboard control (pywinauto/keyboard)
│
├── models/                    # 📦 Pydantic v2 schemas
│   ├── __init__.py           # Package exports
│   ├── commands.py           # EditorCommand (server → local)
│   └── status.py             # LocalStatus (local → server)
│
├── keymaps/                   # ⌨️ Editor keyboard shortcuts
│   └── vscode.yaml           # VS Code default keymap
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
- `python-socketio[client]` - WebSocket communication with server
- `requests` - HTTP client for audio downloads
- `pygame` - Audio playback
- `pydantic` - Data validation and schemas
- `pyyaml` - Keymap file parsing
- `pywinauto` - Windows automation
- `pygetwindow` - Window management

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
1. Connect to server via Socket.IO
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
- `EVENT_*`: Socket.IO event names (must match server)
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
- `_handle_*()`: Handler methods for each command type (NotImplementedError stubs)

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

**Key Methods** (all NotImplementedError stubs):
- `find_window(name)`: Find window by title pattern
- `focus_window(name)`: Activate and bring window to front
- `is_app_running(name)`: Check if app is running
- `get_active_window_title()`: Get current active window title

**Implementation Strategy**:
Use pywinauto for window management:
```python
from pywinauto import Application
app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
main_window = app.window(title_re=".*Visual Studio Code.*")
main_window.set_focus()
```

#### `controller/keyboard.py` - Keyboard Control

**Role**: Send keyboard input to active window

**Key Methods** (all NotImplementedError stubs):
- `send_hotkey(keys)`: Send key combination (["ctrl", "g"])
- `type_text(text)`: Type text with special character escaping
- `send_command_palette(command)`: Open palette + type command + Enter

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

**IMPLEMENT** (Mentor's scope):
- `controller/window.py` - All methods (currently NotImplementedError)
- `controller/keyboard.py` - All methods (currently NotImplementedError)
- `controller/executor.py` - Handler methods `_handle_*()` (currently NotImplementedError)

### Implementation Entry Point

The main entry point for mentor's logic is in `main.py`:

```python
def execute_mentor_logic(command_data: Dict[str, Any]):
    """
    🎯 Mentor's implementation goes here
    
    This function is called AFTER audio playback completes.
    Use EditorController to execute commands.
    """
    # Example implementation:
    from controller import EditorController
    from models import EditorCommand
    
    # Parse command
    cmd = EditorCommand.from_legacy(command_data)
    
    # Execute via controller
    controller = EditorController()
    result = controller.execute(cmd)
    
    print(f"✅ Command executed: {result}")
```

### Recommended Implementation Order

1. **Window Management** (`controller/window.py`):
   - Implement `find_window()` using pywinauto
   - Implement `focus_window()` using pywinauto
   - Implement `is_app_running()` using pywinauto
   - Implement `get_active_window_title()` using pygetwindow

2. **Keyboard Control** (`controller/keyboard.py`):
   - Implement `send_hotkey()` using keyboard library
   - Implement `type_text()` using keyboard library
   - Implement `send_command_palette()` combining hotkey + type + Enter

3. **Command Handlers** (`controller/executor.py`):
   - Implement `_handle_focus_window()` using WindowManager
   - Implement `_handle_hotkey()` using KeyboardController
   - Implement `_handle_type_text()` using KeyboardController
   - Implement `_handle_command_palette()` using KeyboardController
   - Implement `_handle_open_file()` using KeyboardController
   - Implement `_handle_goto_line()` using KeyboardController

4. **Integration** (`main.py`):
   - Replace stub in `execute_mentor_logic()` with controller calls

### Testing Approach

Manual verification procedure:

1. **Window Management Test**:
   ```python
   from controller.window import WindowManager
   wm = WindowManager()
   
   # Test: Find VS Code window
   assert wm.find_window("Visual Studio Code") is not None
   
   # Test: Focus VS Code
   assert wm.focus_window("Visual Studio Code") == True
   
   # Test: Check if running
   assert wm.is_app_running("Visual Studio Code") == True
   ```

2. **Keyboard Control Test**:
   ```python
   from controller.keyboard import KeyboardController
   kb = KeyboardController()
   
   # Test: Send Ctrl+G (should open Go to Line dialog)
   kb.send_hotkey(["ctrl", "g"])
   
   # Test: Type text
   kb.type_text("print('test')")
   ```

3. **End-to-End Test**:
   - Start local agent: `uv run python main.py`
   - Send test command from server
   - Verify audio plays
   - Verify editor action executes

## Known Issues

### pygame Build Failure

**Issue**: pygame fails to build on some Windows systems due to missing MSYS2/pacman.

**Error**:
```
error: `pacman` must be installed and on PATH to install pygame from source.
```

**Impact**: Blocks `uv run` commands during development.

**Workaround**: 
- Development: Code review verification instead of runtime tests
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
