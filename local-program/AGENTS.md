# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-01 | **Commit:** c885ce5 | **Branch:** main

## OVERVIEW

SyncSight AI local agent — the "Hands" in an Eyes-Brain-Hands architecture. Receives editor commands from server via WebSocket, plays TTS audio, controls Windows editors (VS Code) using pywinauto + keyboard. Python 3.14, async websockets in main.py + sync controller layer, Pydantic v2.

## STRUCTURE

```
local-program/
├── main.py                 # 🔒 WebSocket client, event handlers, audio orchestration (문건호)
├── config.py               # 🔒 Server URL, events, audio config (문건호)
├── audio_handler.py        # 🔒 playsound3 TTS playback (문건호)
├── controller/
│   ├── executor.py         # Command dispatcher (match/case → 8 handlers), keymap loader
│   ├── window.py           # pywinauto + pygetwindow: find/focus/ensure/launch windows
│   └── keyboard.py         # keyboard lib: hotkey, type_text, command_palette
├── models/
│   ├── commands.py         # EditorCommand + 8 payload models + from_legacy() adapter
│   └── status.py           # LocalStatus (IDLE/BUSY, active window, etc.)
├── keymaps/vscode.yaml     # Editor shortcuts (DO NOT hardcode in Python)
├── tests/                  # 96 unit + 6 integration (pytest + pytest-mock)
├── live_test_nadocoding*.py # Manual live test scripts
└── status_monitor.py       # Status monitoring utility
```

## OWNERSHIP & FORBIDDEN ZONES

| Zone | Owner | AI May Edit |
|------|-------|-------------|
| `main.py` | 문건호 | `execute_mentor_logic()` body ONLY |
| `config.py` | 문건호 | Bottom mentor settings section ONLY |
| `audio_handler.py` | 문건호 | **NEVER** |
| `controller/`, `models/`, `keymaps/` | Mentor | Freely |

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add command type | `models/commands.py` (payload model) → `controller/executor.py` (handler + match case) |
| Change editor shortcuts | `keymaps/vscode.yaml` (NOT Python code) |
| Window automation | `controller/window.py` (pywinauto for focus, pygetwindow for query) |
| Text/hotkey input | `controller/keyboard.py` (keyboard lib, NOT pywinauto type_keys) |
| Legacy command format | `EditorCommand.from_legacy()` in `models/commands.py` |
| Test fixtures/mocks | `tests/conftest.py` |

## CODE MAP

| Symbol | Location | Role |
|--------|----------|------|
| `EditorController` | `controller/executor.py` | Main dispatcher, 8 `_handle_*` methods, IDLE↔BUSY state |
| `WindowManager` | `controller/window.py` | find/focus/ensure/launch windows, `_select_best_title` |
| `KeyboardController` | `controller/keyboard.py` | send_hotkey, type_text, send_command_palette |
| `EditorCommand` | `models/commands.py` | 8 command types, `from_legacy()` classmethod |
| `LocalStatus` | `models/status.py` | Pydantic model for status reporting |

## CONVENTIONS

- **한글 주석 ONLY** — all comments in Korean, never English
- **Emoji prefixes** — 🎯 역할, 🔧 기능, ⚠️ 주의, ✅ 성공, ❌ 실패
- **Section headers** — `# ====` for modules, `# ----` for subsections
- **Docstrings** — Korean, must include `Example:` section
- **Type hints** — mandatory on all function signatures
- **Pydantic v2** — all structured data, no plain dicts

## ANTI-PATTERNS (THIS PROJECT)

| Forbidden | Reason |
|-----------|--------|
| `async`/`await` in controller/ | pygame + pywinauto are sync; only main.py uses async |
| New dependencies | Stick to `pyproject.toml`; no click, loguru, rich, asyncio |
| `pywinauto.type_keys()` for text | Special chars `{}+^%~()[]` break; use `keyboard.write()` |
| `app.window(class_name="Editor")` | Electron apps don't expose internals; use title regex |
| Exact window title match | Titles include filenames; use `title_re=".*VS Code.*"` |
| Hardcoded shortcuts | Load from `keymaps/*.yaml` |
| Extra threads | Don't block main thread; `execute_mentor_logic()` must return fast |
| `as any` / type suppression | Not applicable (Python), but no `# type: ignore` either |

## UNIQUE PATTERNS

- **Hybrid automation**: pywinauto for window mgmt only, `keyboard` lib for all input
- **ensure_window()**: find → auto-launch if missing → poll until ready → focus
- **_dismiss_stale_dialogs()**: Esc-spam before each command to clear leftover modals
- **_select_best_title()**: Multi-window disambiguation via `project_hint` + `TARGET_PROJECT_PATH`
- **from_legacy()**: Converts old `{action, target, content}` dicts to typed `EditorCommand`

## COMMANDS

```powershell
# Run agent
uv run python main.py

# Unit tests (96 expected pass, 6 integration deselected)
.venv\Scripts\pytest.exe tests/ -v -m "not integration"

# Lint + format
.venv\Scripts\ruff.exe check controller/ models/ tests/
.venv\Scripts\ruff.exe format --check controller/ models/ tests/
```

## NOTES

- **Python 3.14** required (`requires-python = ">=3.14"`)
- pywinauto special chars: `{}+^%~()[]` — always use `keyboard.write()` for text
- VS Code window title format: `"filename - project_folder - Visual Studio Code"`
- pygame build may fail without MSYS2 on some Windows setups (env issue, not code)
- Package manager: `uv` (not pip)
- 8 command types: focus_window, hotkey, type_text, command_palette, open_file, goto_line, open_folder, save_file
