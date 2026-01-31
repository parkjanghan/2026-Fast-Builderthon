# AGENTS.md - AI Agent Development Guidelines

This document provides comprehensive guidelines for AI agents (like Claude, GPT-4, etc.) working on the SyncSight AI local-program codebase. Read this carefully before making any changes.

## Project Context

### What is SyncSight AI?

SyncSight AI is an AI-powered lecture video synchronization system designed for coding education. It consists of three parts:

1. **Chrome Extension (Eyes)** - Watches lecture videos, detects code changes
2. **Replit Server (Brain)** - Processes events with AI, generates commands and TTS audio
3. **Local Agent (Hands)** - THIS PROJECT - Controls Windows editors, plays audio guidance

### Local Agent Role

The local agent is the "Hands" that execute commands on the student's Windows machine:
- Receives commands from server via WebSocket (Socket.IO)
- Plays audio guidance (ElevenLabs TTS)
- Controls Windows applications (VS Code, etc.) using pywinauto
- Reports local status back to server

### Team Structure

- **문건호**: Implemented server communication (`main.py`), audio playback (`audio_handler.py`), configuration (`config.py`)
- **Mentor**: Responsible for implementing Windows automation (`controller/` modules)
- **박장한**: Chrome extension (Part 1)
- **이재준**: Replit server (Part 2)

## Code Style Guide

This project follows strict conventions established by 문건호. **You MUST follow these patterns.**

### 1. Korean Comments (한글 주석)

All comments MUST be in Korean, not English.

```python
# ✅ CORRECT
# 윈도우를 찾아서 포커스합니다
def focus_window(name):
    pass

# ❌ WRONG
# Find and focus the window
def focus_window(name):
    pass
```

### 2. Emoji Prefixes

Use emoji prefixes for visual scanning and categorization:

```python
# 🎯 역할: (Role/Purpose)
# 🔧 주요 기능: (Key Features)
# 📝 멘토님께: (Notes for Mentor)
# 🚀 실행 방법: (How to Run)
# ⚠️ 주의사항: (Warnings)
# 💡 팁: (Tips)
# 📦 의존성: (Dependencies)
# 🔄 흐름: (Flow)
# ✅ 성공: (Success)
# ❌ 실패: (Failure)
```

### 3. Section Headers

Use consistent section separators with emoji:

```python
# ============================================================================
# 📁 module_name.py - 모듈 설명
# ============================================================================
#
# 🎯 역할:
#   이 모듈의 역할 설명
#
# 🔧 주요 기능:
#   - 기능 1
#   - 기능 2
#
# ============================================================================

# -------------------------------------------------------------------------
# 🔧 서브섹션 제목
# -------------------------------------------------------------------------
```

### 4. Docstrings with Examples

All functions MUST have docstrings with Examples section:

```python
def send_hotkey(self, keys: List[str]) -> None:
    """
    🎹 키보드 단축키 전송
    
    여러 키를 동시에 누르는 단축키를 전송합니다.
    
    Args:
        keys (List[str]): 단축키 조합
            예: ["ctrl", "g"], ["ctrl", "shift", "p"]
    
    Returns:
        None
    
    Note:
        키 이름은 소문자로 통일합니다:
        - ctrl, shift, alt, win
        - a-z, 0-9
        - enter, esc, tab, space
    
    Example:
        kb = KeyboardController()
        
        # Ctrl+G (Go to Line)
        kb.send_hotkey(["ctrl", "g"])
        
        # Ctrl+Shift+P (Command Palette)
        kb.send_hotkey(["ctrl", "shift", "p"])
    """
    pass
```

### 5. Type Hints

Use type hints on all function signatures:

```python
from typing import List, Dict, Any, Optional

def execute(self, command: EditorCommand) -> Dict[str, Any]:
    pass

def find_window(self, name: str) -> Optional[Any]:
    pass
```

## Forbidden Zones

**NEVER MODIFY THESE FILES** - They are 문건호's responsibility:

### `main.py`
- WebSocket client setup
- Event handlers (`on_editor_sync`, `on_lecture_pause`, `on_lecture_resume`)
- Status reporting thread
- Audio orchestration

**Exception**: You MAY implement the body of `execute_mentor_logic()` function, but DO NOT change its signature or location.

### `config.py`
- Server URL and connection settings
- Event name constants
- Audio configuration
- Status reporting interval

**Exception**: You MAY add mentor-specific settings at the bottom in the designated section.

### `audio_handler.py`
- Audio download logic
- pygame mixer setup
- Playback controls
- Cache management

**No exceptions** - This is entirely 문건호's domain.

## Architecture Principles

### 1. Separation of Concerns

The codebase is organized into clear layers:

```
main.py (Orchestration)
    ↓
controller/executor.py (Command Dispatch)
    ↓
controller/window.py + controller/keyboard.py (Low-level Control)
    ↓
pywinauto / keyboard library (System APIs)
```

**DO NOT** mix concerns:
- Window management logic belongs in `window.py`
- Keyboard input logic belongs in `keyboard.py`
- Command dispatch logic belongs in `executor.py`
- Orchestration logic stays in `main.py`

### 2. Pydantic Typing

All data structures use Pydantic v2 for validation:

```python
from pydantic import BaseModel, Field
from typing import Literal

class EditorCommand(BaseModel):
    type: Literal["focus_window", "hotkey", "type_text", ...]
    payload: Dict[str, Any]
```

**DO NOT** use plain dicts for structured data. Use Pydantic models from `models/` package.

### 3. Keymap Profiles

Editor-specific shortcuts are defined in YAML files under `keymaps/`:

```yaml
editor: "Visual Studio Code"
window_title_pattern: ".*Visual Studio Code.*"

shortcuts:
  goto_line: ["ctrl", "g"]
  command_palette: ["ctrl", "shift", "p"]
```

**DO NOT** hardcode shortcuts in Python. Load from keymap files.

### 4. No Async/Await

This project uses **synchronous threading**, not async/await:

```python
# ✅ CORRECT
import threading

def report_loop():
    while running:
        send_status()
        time.sleep(1.0)

thread = threading.Thread(target=report_loop, daemon=True)
thread.start()

# ❌ WRONG
import asyncio

async def report_loop():
    while running:
        await send_status()
        await asyncio.sleep(1.0)
```

**Reason**: pygame and pywinauto are synchronous libraries. Mixing async/sync causes complexity.

### 5. No Extra Dependencies

Stick to dependencies in `pyproject.toml`:

```toml
dependencies = [
    "python-socketio[client]>=5.10.0",
    "requests>=2.31.0",
    "pygame>=2.5.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "pywinauto>=0.6.8",
    "pygetwindow>=0.0.9",
    "keyboard>=0.13.5",
]
```

**DO NOT** add new dependencies without explicit approval. Use what's already there.

## Critical Warnings

### 1. pywinauto Special Characters

pywinauto's `type_keys()` treats certain characters as special:

```python
# ❌ WRONG - Will fail
window.type_keys("print('hello')")  # Parentheses are special
window.type_keys("x + y")           # Plus is special
window.type_keys("value^2")         # Caret is special

# ✅ CORRECT - Escape special chars
window.type_keys("print{(}'hello'{)}")  # Escape with {}
# OR use keyboard library instead:
import keyboard
keyboard.write("print('hello')")  # No escaping needed
```

**Special characters in pywinauto**: `{}+^%~()[]`

**Recommendation**: Use `keyboard` library for text input, pywinauto only for window management.

### 2. Electron App Limitations

VS Code is an Electron app, which has UI automation challenges:

**Problem**: pywinauto cannot reliably access VS Code's internal UI elements (editor pane, line numbers, etc.)

**Solution**: Hybrid approach
- **Window management**: Use pywinauto (`find_window`, `focus_window`, `set_focus`)
- **Editor control**: Use keyboard shortcuts and text input (Ctrl+G for goto line, etc.)

```python
# ✅ CORRECT - Hybrid approach
from pywinauto import Application
import keyboard

# 1. Focus window with pywinauto
app = Application(backend='uia').connect(title_re=".*Visual Studio Code.*")
window = app.window(title_re=".*Visual Studio Code.*")
window.set_focus()

# 2. Control editor with keyboard
keyboard.send("ctrl+g")  # Go to Line
time.sleep(0.2)
keyboard.write("42")
keyboard.send("enter")

# ❌ WRONG - Trying to access editor elements directly
editor_pane = window.child_window(class_name="Editor")  # Won't work reliably
```

### 3. Threading Issues

The status reporting thread runs in background:

```python
# In main.py
def report_loop():
    while status_report_running and sio.connected:
        status = get_local_status()
        sio.emit(EVENT_LOCAL_STATUS, status)
        time.sleep(STATUS_REPORT_INTERVAL)

thread = threading.Thread(target=report_loop, daemon=True)
thread.start()
```

**DO NOT**:
- Create additional threads without coordination
- Access shared state without locks if needed
- Block the main thread (it handles Socket.IO events)

**DO**:
- Keep `execute_mentor_logic()` synchronous but fast
- Use `time.sleep()` for short delays (0.1-0.5s)
- Return quickly to allow next command

### 4. Window Title Patterns

Use regex patterns for window matching:

```python
# ✅ CORRECT - Flexible pattern
window_pattern = ".*Visual Studio Code.*"
app.connect(title_re=window_pattern)

# ❌ WRONG - Exact match (fragile)
window_pattern = "Visual Studio Code"
app.connect(title=window_pattern)  # Fails if title is "main.py - Visual Studio Code"
```

**Reason**: Window titles often include file names, project names, etc.

## Development Workflow

### 1. Read Existing Code First

Before implementing, read:
- `main.py` - Understand command flow
- `models/commands.py` - Understand command structure
- `controller/executor.py` - Understand dispatch pattern
- `keymaps/vscode.yaml` - Understand available shortcuts

### 2. Current Implementation Status

All controller modules are **fully implemented and tested**:

| Module | Status | Description |
|--------|--------|-------------|
| `controller/window.py` | ✅ Complete | pywinauto + pygetwindow window management, auto-launch, multi-window support |
| `controller/keyboard.py` | ✅ Complete | keyboard library for hotkeys, text input, command palette |
| `controller/executor.py` | ✅ Complete | All 6 _handle_* methods implemented, state management (IDLE/BUSY) |
| `models/commands.py` | ✅ Complete | EditorCommand with from_legacy() adapter, 6 payload models |
| `models/status.py` | ✅ Complete | LocalStatus Pydantic model |
| `main.py` (execute_mentor_logic) | ✅ Complete | Calls EditorController, handles errors |

### 3. Development Workflow (for future changes)

When modifying existing code:

1. **Read existing code first** - Understand current implementation patterns
2. **Follow established patterns** - Match existing code style and structure
3. **Run automated tests** - Verify changes don't break existing functionality
4. **Run ruff linter** - Ensure code quality standards

### 4. Handle Errors Gracefully

Wrap pywinauto calls in try/except:

```python
def focus_window(self, name: str) -> bool:
    """윈도우에 포커스"""
    try:
        app = Application(backend='uia').connect(title_re=name, timeout=5)
        window = app.window(title_re=name)
        window.set_focus()
        return True
    except Exception as e:
        print(f"❌ 윈도우 포커스 실패: {e}")
        return False
```

**DO NOT** let exceptions crash the agent. Return error results instead.

## Testing

### Automated Tests (pytest + pytest-mock)

The project has comprehensive automated tests with mocked system dependencies (pywinauto, pygame, keyboard).

```powershell
cd local-program

# Run unit tests (excludes integration tests requiring VS Code)
.venv\Scripts\pytest.exe tests/ -v -m "not integration"
# Expected: 74 passed, 6 deselected

# Run ALL tests including integration
.venv\Scripts\pytest.exe tests/ -v

# Run specific test file
.venv\Scripts\pytest.exe tests/test_models.py -v
```

### Test Structure

| File | Tests | What it covers |
|------|-------|---------------|
| `test_models.py` | 21 | EditorCommand creation, from_legacy() conversion, payload validation, LocalStatus |
| `test_controller.py` | 11 | Dispatch routing to correct handlers, IDLE↔BUSY state transitions, get_status() |
| `test_edge_cases.py` | 20 | _select_best_title, app detection, ensure_window scenarios, launch_app, executor integration |
| `test_scenarios.py` | 12 | New file, hello world, file+goto, formatting, full coding session sequences |
| `test_integration.py` | 6 | End-to-end flows (marked @pytest.mark.integration, requires actual VS Code) |

### Code Quality (ruff)

```powershell
# Lint
.venv\Scripts\ruff.exe check controller/ models/ tests/

# Format
.venv\Scripts\ruff.exe format --check controller/ models/ tests/
```

### After making changes, ALWAYS:

1. Run `pytest tests/ -m "not integration"` — all 74 tests must pass
2. Run `ruff check controller/ models/ tests/` — must show "All checks passed!"
3. Run `ruff format --check controller/ models/ tests/` — must show no reformatting needed

### Manual Verification (Live Testing)

For testing with actual VS Code (not a substitute for automated tests):

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

### Common Issues and Solutions

#### Issue: "Element not found"

```python
# ❌ Problem
window = app.window(class_name="Editor")  # Too specific

# ✅ Solution
window = app.window(title_re=".*Visual Studio Code.*")  # Use title pattern
```

#### Issue: Keyboard input not working

```python
# ❌ Problem
window.type_keys("print('hello')")  # Special chars fail

# ✅ Solution
import keyboard
keyboard.write("print('hello')")  # Use keyboard library
```

#### Issue: Window not focusing

```python
# ❌ Problem
window.set_focus()  # Might not work if minimized

# ✅ Solution
if window.is_minimized():
    window.restore()
window.set_focus()
time.sleep(0.2)  # Give it time to focus
```

## Summary Checklist

Before submitting your implementation, verify:

- [x] All comments in Korean (한글 주석)
- [x] Emoji prefixes used consistently
- [x] Section headers follow `# ===` pattern
- [x] All functions have docstrings with Examples
- [x] Type hints on all function signatures
- [x] No modifications to `main.py` (except `execute_mentor_logic()` body)
- [x] No modifications to `config.py` (except mentor settings section)
- [x] No modifications to `audio_handler.py`
- [x] No async/await introduced
- [x] No extra dependencies added
- [x] Hybrid approach used (pywinauto for windows, keyboard for input)
- [x] Special characters handled correctly
- [x] Errors handled gracefully (try/except)
- [x] Code follows separation of concerns
- [x] All controller modules implemented
- [ ] Automated tests pass (74/74)
- [ ] ruff check passes
- [ ] ruff format passes

## Questions?

If you're unsure about:
- **Architecture decisions**: Check `decisions.md` in notepad
- **Known issues**: Check `issues.md` in notepad
- **Patterns used**: Check `learnings.md` in notepad
- **Code style**: Re-read this document

When in doubt, **ask the user** rather than making assumptions.

## Final Notes

This is a **student hackathon project** with implementation complete. Current priorities:

1. **Maintaining existing tests** when making changes
2. **Following established patterns** in existing code
3. **Running automated tests + ruff** before submitting changes

Remember: 문건호 handles server/audio, Mentor handles Windows automation. Stay in your lane.

Good luck!
