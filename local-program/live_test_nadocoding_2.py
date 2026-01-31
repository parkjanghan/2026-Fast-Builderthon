# ============================================================================
# live_test_nadocoding_2.py
# ============================================================================
#
# live_test_nadocoding.py (test 1) 실행 후 이어서 실행합니다.
# test 1의 결과물(PythonWorkspace/practice.py)을 인식하고
# 강의 영상의 다음 상태까지 따라갑니다.
#
# 전제 조건:
#   - test 1이 성공적으로 완료됨
#   - PythonWorkspace/practice.py 가 존재함
#   - VS Code가 PythonWorkspace를 열고 있음
#
# 실행:
#   cd local-program
#   PYTHONIOENCODING=utf-8 .venv\Scripts\python.exe live_test_nadocoding_2.py
#
# ============================================================================

import os
import sys
import time

from controller.executor import EditorController
from models.commands import EditorCommand

WORKSPACE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "PythonWorkspace")
PRACTICE_PATH = os.path.join(WORKSPACE_PATH, "practice.py")


def check_preconditions():
    """test 1의 결과물이 있는지 확인"""
    if not os.path.exists(WORKSPACE_PATH):
        print(f"  FAIL: workspace not found: {WORKSPACE_PATH}")
        print("  run live_test_nadocoding.py first")
        return False

    if not os.path.exists(PRACTICE_PATH):
        print(f"  FAIL: practice.py not found: {PRACTICE_PATH}")
        print("  run live_test_nadocoding.py first")
        return False

    with open(PRACTICE_PATH, encoding="utf-8") as f:
        content = f.read()

    print(f"  workspace: {WORKSPACE_PATH}")
    print(f"  practice.py found ({len(content)} bytes)")
    print()
    print("  current content:")
    for i, line in enumerate(content.splitlines(), 1):
        print(f"    {i}| {line}")
    print()
    return True


def main():
    print("=" * 60)
    print("  nadocoding lecture replay - part 2")
    print("=" * 60)
    print()

    if not check_preconditions():
        sys.exit(1)

    print("  target state:")
    print('    1| jumin = "990120-1234567"')
    print("    2|")
    print('    3| print("seongbyeol : " + jumin[7])')
    print('    4| print("yeon : " + jumin[0:2])  # 0 buteo 2 jikjeonkkaji')
    print('    5| print("wol : " + jumin[2:4])')
    print('    6| print("il : " + jumin[4:6])')
    print("    7|")
    print('    8| print("saengnyeonworil : " +)')
    print("                                      ^ Ln 8, Col 18")
    print()
    print("  also: create helloworld.py in workspace")
    print()
    print("  starting in 3 seconds...")
    print()

    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    controller = EditorController(keymap_path="keymaps/vscode.yaml")

    # --- Phase 0: helloworld.py를 Python으로 직접 생성 ---
    helloworld_path = os.path.join(WORKSPACE_PATH, "helloworld.py")
    with open(helloworld_path, "w", encoding="utf-8") as f:
        f.write('print("Hello World")\n')
    print(f"  [pre] helloworld.py 생성 완료: {helloworld_path}")
    print()

    steps = [
        # --- Phase 1: VS Code 포커스 + practice.py 열기 ---
        (
            "focus VS Code (PythonWorkspace)",
            EditorCommand(
                type="focus_window",
                payload={"window_title": "Visual Studio Code",
                         "project_hint": "PythonWorkspace"},
            ),
        ),
        (
            "open practice.py",
            EditorCommand(
                type="open_file",
                payload={"file_path": PRACTICE_PATH},
            ),
        ),
        # test 1에서 jumin[] 이었던 곳에 7 입력 -> jumin[7]
        # ⚠️ VS Code는 한글(성별)을 각 2컬럼으로 카운트 → 실제 col 23 + 2 = 25
        (
            "goto jumin[] -> type 7",
            EditorCommand(
                type="goto_line",
                payload={"line_number": 3, "column": 25},
            ),
        ),
        (
            "type 7 inside brackets",
            EditorCommand(type="type_text", payload={"content": "7"}),
        ),
        # 3행 끝으로 이동 후 새 줄 추가
        (
            "end of line 3",
            EditorCommand(type="hotkey", payload={"keys": ["end"]}),
        ),
        (
            "enter -> line 4",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "type line 4: print yeon",
            EditorCommand(
                type="type_text",
                payload={"content": 'print("연 : " + jumin[0:2])  # 0 부터 2 직전까지'},
            ),
        ),
        (
            "enter -> line 5",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "type line 5: print wol",
            EditorCommand(
                type="type_text",
                payload={"content": 'print("월 : " + jumin[2:4])'},
            ),
        ),
        (
            "enter -> line 6",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "type line 6: print il",
            EditorCommand(
                type="type_text",
                payload={"content": 'print("일 : " + jumin[4:6])'},
            ),
        ),
        # 빈 줄 + 8행
        (
            "enter -> blank line 7",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "enter -> line 8",
            EditorCommand(type="hotkey", payload={"keys": ["enter"]}),
        ),
        (
            "type line 8: print saengnyeonworil",
            EditorCommand(
                type="type_text",
                payload={"content": 'print("생년월일 : " +)'},
            ),
        ),
        # 커서를 Ln 8, Col 18로 (+ 뒤, ) 앞)
        (
            "cursor -> Ln 8, Col 18",
            EditorCommand(
                type="goto_line",
                payload={"line_number": 8, "column": 18},
            ),
        ),
        # 저장
        (
            "save practice.py",
            EditorCommand(type="save_file", payload={"file_name": None}),
        ),
    ]

    print()
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"  [{i}/{len(steps)}] {desc}")
        result = controller.execute(cmd)
        ok = "OK" if result.get("success") else "FAIL"
        print(f"         {ok}: {result.get('message', '')}")
        if cmd.type in ("save_file", "open_folder", "open_file"):
            time.sleep(1.0)
        else:
            time.sleep(0.5)

    print()
    print("=" * 60)
    print("  done. check VS Code:")
    print(f"  - workspace: {WORKSPACE_PATH}")
    print("  - helloworld.py (created)")
    print("  - practice.py (8 lines, cursor Ln 8 Col 18)")
    print("=" * 60)

    # 최종 파일 내용 출력
    print()
    print("  final practice.py:")
    with open(PRACTICE_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f.read().splitlines(), 1):
            print(f"    {i}| {line}")


if __name__ == "__main__":
    main()
