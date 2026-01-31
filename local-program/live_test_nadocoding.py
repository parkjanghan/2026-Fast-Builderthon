# ============================================================================
# live_test_nadocoding.py
# ============================================================================
#
# 나도코딩 파이썬 기본편 강의 화면을 실제로 재현합니다.
#
# 목표:
#   Desktop/PythonWorkspace/ 폴더 생성 + VS Code 워크스페이스 열기
#   -> practice.py 생성 + 코드 입력 + 커서를 jumin[] 안에 위치
#
# 실행:
#   cd local-program
#   PYTHONIOENCODING=utf-8 .venv\Scripts\python.exe live_test_nadocoding.py
#
# ============================================================================

import os
import time

from controller.executor import EditorController
from models.commands import EditorCommand

# 워크스페이스 경로 (데스크탑에 생성)
WORKSPACE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "PythonWorkspace")


def main():
    print("=" * 60)
    print("  nadocoding lecture replay")
    print("=" * 60)
    print()
    print(f"  workspace: {WORKSPACE_PATH}")
    print("  file:      practice.py")
    print()
    print('  1| jumin = "990120-1234567"')
    print("  2|")
    print('  3| print("seongbyeol : " + jumin[])')
    print("                                       ^ Ln 3, Col 23")
    print()
    print("  starting in 3 seconds...")
    print()

    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    controller = EditorController(keymap_path="keymaps/vscode.yaml")

    steps = [
        # 1. 워크스페이스 폴더 열기 (없으면 생성 + VS Code에서 열기)
        (
            "open workspace folder",
            EditorCommand(
                type="open_folder",
                payload={"folder_path": WORKSPACE_PATH, "new_window": True},
            ),
        ),
        # 2. 새 파일 만들기
        (
            "new file (Ctrl+N)",
            EditorCommand(type="hotkey", payload={"keys": ["ctrl", "n"]}),
        ),
        # 3. 파일을 practice.py로 저장 (절대 경로)
        (
            "save as practice.py",
            EditorCommand(
                type="save_file",
                payload={"file_name": "practice.py", "folder_path": WORKSPACE_PATH},
            ),
        ),
        # 4. 1행 입력
        (
            'type line 1: jumin = "990120-1234567"',
            EditorCommand(
                type="type_text",
                payload={"content": 'jumin = "990120-1234567"'},
            ),
        ),
        # 5-6. Enter 2번
        (
            "enter (blank line)",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "enter (line 3 start)",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        # 7. 3행 입력
        (
            'type line 3: print("seongbyeol : " + jumin[])',
            EditorCommand(
                type="type_text",
                payload={"content": 'print("성별 : " + jumin[])'},
            ),
        ),
        # 8. 커서 이동
        (
            "cursor -> Ln 3, Col 23",
            EditorCommand(
                type="goto_line",
                payload={"line_number": 3, "column": 23},
            ),
        ),
        # 9. 저장
        (
            "save (Ctrl+S)",
            EditorCommand(
                type="save_file",
                payload={"file_name": None},
            ),
        ),
    ]

    print()
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"  [{i}/{len(steps)}] {desc}")
        result = controller.execute(cmd)
        ok = "OK" if result.get("success") else "FAIL"
        print(f"         {ok}: {result.get('message', '')}")
        # save_file과 open_folder 후에는 더 긴 대기
        if cmd.type in ("save_file", "open_folder"):
            time.sleep(1.0)
        else:
            time.sleep(0.5)

    print()
    print("=" * 60)
    print("  done. check VS Code:")
    print(f"  - workspace: {WORKSPACE_PATH}")
    print("  - file: practice.py (saved)")
    print("  - cursor: Ln 3, Col 23 (inside jumin[])")
    print("=" * 60)


if __name__ == "__main__":
    main()
