# ============================================================================
# 📁 controller/window.py - 윈도우 관리 모듈
# ============================================================================
#
# 🎯 역할:
#   Windows 애플리케이션 창을 찾고, 포커스하고, 상태를 확인합니다.
#   앱이 꺼져있으면 자동 실행하고, 다중 창이면 프로젝트명으로 선택합니다.
#
# 🔧 주요 기능:
#   - find_window: 이름으로 창 찾기 (다중 창 시 프로젝트명 매칭)
#   - focus_window: 특정 창에 포커스
#   - ensure_window: 창 찾기 → 없으면 자동 실행 → 재시도 (통합)
#   - launch_app: 앱이 꺼져있을 때 자동 실행
#   - is_app_running: 애플리케이션 실행 여부 확인
#   - get_active_window_title: 현재 활성 창 제목 가져오기
#
# ⚠️ 예외 처리 전략:
#   1. 앱이 꺼져있음 → launch_app()으로 자동 실행 + 창 대기
#   2. 다중 VS Code 창 → 제목에서 프로젝트 폴더명 매칭
#   3. code 명령어 없음 → shutil.which() 사전 체크 + 에러 메시지
#   4. 실행 후 창이 안 뜸 → polling with timeout
#
# ============================================================================

import os
import re
import shutil
import subprocess
import time
from typing import Any

import pygetwindow as gw
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError


class WindowManager:
    """
    🪟 윈도우 관리 클래스

    Windows 애플리케이션 창을 찾고 제어하는 기능을 제공합니다.
    앱이 꺼져있으면 자동 실행, 다중 창이면 프로젝트명 매칭.

    Example:
        wm = WindowManager()

        # 앱이 꺼져있으면 자동 실행 + 포커스
        wm.ensure_window("Visual Studio Code", project_hint="my-project")

        # 단순 포커스 (앱이 이미 실행 중이어야 함)
        wm.focus_window("Visual Studio Code")

        # 현재 활성 창 제목 가져오기
        title = wm.get_active_window_title()
    """

    def __init__(self):
        """
        🏗️ WindowManager 초기화

        별도의 사전 연결 없이 메서드 호출 시 동적으로 연결합니다.
        """
        pass

    # ========================================================================
    # 🔍 창 검색
    # ========================================================================

    def find_window(self, name: str, project_hint: str = "") -> Any | None:
        """
        🔍 이름으로 윈도우 찾기 (다중 창 시 프로젝트명 매칭)

        1. pygetwindow로 빠르게 제목 목록 검색
        2. 다중 매칭 시 project_hint로 필터링
        3. pywinauto로 해당 창에 연결

        Args:
            name (str): 찾을 윈도우의 이름 또는 정규식 패턴
                예: "Visual Studio Code", ".*notepad.*"
            project_hint (str): 프로젝트 폴더명 힌트 (다중 창 구분용)
                예: "my-project", "2026-Fast-Builderthon"

        Returns:
            Optional[Any]: 찾은 윈도우 객체 (pywinauto WindowSpecification)
                찾지 못한 경우 None 반환

        Example:
            wm = WindowManager()

            # 단일 창
            vscode = wm.find_window("Visual Studio Code")

            # 다중 창에서 특정 프로젝트 선택
            vscode = wm.find_window("Visual Studio Code", project_hint="my-project")
        """
        try:
            pattern = name if _is_regex(name) else f".*{re.escape(name)}.*"
            compiled = re.compile(pattern, re.IGNORECASE)

            # 1단계: pygetwindow로 매칭되는 제목들 수집
            all_titles = gw.getAllTitles()
            matched_titles = [t for t in all_titles if t.strip() and compiled.search(t)]

            if not matched_titles:
                return None

            # 2단계: 다중 매칭 시 프로젝트 힌트로 필터링
            target_title = _select_best_title(matched_titles, project_hint)

            # 3단계: pywinauto로 해당 창에 연결 (re.escape로 정확 매칭)
            exact_pattern = f"^{re.escape(target_title)}$"
            app = Application(backend="uia").connect(
                title_re=exact_pattern, timeout=3, found_index=0
            )
            window = app.top_window()
            return window if window.exists() else None

        except (ElementNotFoundError, Exception) as e:
            print(f"❌ 윈도우 검색 실패 ({name}): {e}")
            return None

    def find_all_windows(self, name: str) -> list[str]:
        """
        📋 매칭되는 모든 윈도우 제목 목록 반환

        디버깅/선택용으로 매칭되는 모든 창 제목을 반환합니다.

        Args:
            name (str): 검색할 이름 또는 정규식 패턴

        Returns:
            List[str]: 매칭되는 윈도우 제목 목록

        Example:
            wm = WindowManager()
            titles = wm.find_all_windows("Visual Studio Code")
            # ["main.py - my-project - Visual Studio Code",
            #  "app.py - other-project - Visual Studio Code"]
        """
        try:
            pattern = name if _is_regex(name) else f".*{re.escape(name)}.*"
            compiled = re.compile(pattern, re.IGNORECASE)
            all_titles = gw.getAllTitles()
            return [t for t in all_titles if t.strip() and compiled.search(t)]
        except Exception:
            return []

    # ========================================================================
    # 🎯 포커스 & 보장
    # ========================================================================

    def focus_window(self, name: str, project_hint: str = "") -> bool:
        """
        🎯 특정 윈도우에 포커스

        주어진 이름의 윈도우를 찾아서 활성화(포커스)합니다.
        최소화된 창은 복원하고, 다른 창 뒤에 있으면 앞으로 가져옵니다.

        Args:
            name (str): 포커스할 윈도우의 이름
            project_hint (str): 프로젝트 폴더명 힌트

        Returns:
            bool: 포커스 성공 여부

        Example:
            wm = WindowManager()
            wm.focus_window("Visual Studio Code", project_hint="my-project")
        """
        try:
            window = self.find_window(name, project_hint=project_hint)
            if window is None:
                print(f"❌ 포커스할 윈도우를 찾을 수 없습니다: {name}")
                return False

            # 최소화 상태이면 복원
            if window.is_minimized():
                window.restore()
                time.sleep(0.2)

            # 포커스 설정
            window.set_focus()
            time.sleep(0.1)

            print(f"✅ 윈도우 포커스 성공: {name}")
            return True

        except Exception as e:
            print(f"❌ 윈도우 포커스 실패 ({name}): {e}")
            return False

    def ensure_window(
        self,
        name: str,
        project_hint: str = "",
        launch_cmd: str | None = None,
        auto_launch: bool = True,
        timeout: float = 15.0,
        poll_interval: float = 0.5,
    ) -> bool:
        """
        🛡️ 윈도우 보장 (찾기 → 없으면 실행 → 포커스)

        가장 핵심적인 메서드입니다.
        앱이 실행 중이면 포커스, 꺼져있으면 자동 실행 후 포커스합니다.

        Args:
            name (str): 찾을 윈도우 이름
            project_hint (str): 프로젝트 폴더명 (다중 창 구분)
            launch_cmd (Optional[str]): 앱 실행 명령어 (없으면 자동 감지)
            auto_launch (bool): 앱이 꺼져있을 때 자동 실행 여부
            timeout (float): 앱 실행 후 창 대기 시간 (초)
            poll_interval (float): 창 감지 폴링 간격 (초)

        Returns:
            bool: 최종 포커스 성공 여부

        Example:
            wm = WindowManager()

            # VS Code가 꺼져있으면 자동 실행
            success = wm.ensure_window(
                "Visual Studio Code",
                project_hint="my-project",
            )

            # 자동 실행 비활성화 (찾기만)
            success = wm.ensure_window("메모장", auto_launch=False)
        """
        # 1단계: 이미 실행 중인지 확인
        if self.focus_window(name, project_hint=project_hint):
            return True

        # 2단계: 자동 실행 비활성화면 실패
        if not auto_launch:
            print(f"❌ {name}이(가) 실행 중이지 않습니다 (auto_launch=False)")
            return False

        # 3단계: 앱 실행
        print(f"🚀 {name}이(가) 실행 중이지 않습니다. 자동 실행합니다...")
        launched = self.launch_app(name, launch_cmd=launch_cmd, project_hint=project_hint)
        if not launched:
            return False

        # 4단계: 창이 뜰 때까지 대기 (polling)
        print(f"⏳ 창이 열릴 때까지 대기합니다 (최대 {timeout}초)...")
        start = time.time()
        while time.time() - start < timeout:
            if self.focus_window(name, project_hint=project_hint):
                print(f"✅ {name} 자동 실행 + 포커스 완료!")
                return True
            time.sleep(poll_interval)

        print(f"❌ {name} 실행 후 {timeout}초 이내에 창이 나타나지 않았습니다")
        return False

    # ========================================================================
    # 🚀 앱 실행
    # ========================================================================

    def launch_app(
        self,
        name: str,
        launch_cmd: str | None = None,
        project_hint: str = "",
    ) -> bool:
        """
        🚀 애플리케이션 자동 실행

        앱이 꺼져있을 때 자동으로 실행합니다.
        VS Code의 경우 `code` CLI를 사용합니다.

        Args:
            name (str): 앱 이름 (VS Code 감지용)
            launch_cmd (Optional[str]): 직접 지정할 실행 명령어
            project_hint (str): VS Code 실행 시 열 프로젝트 경로

        Returns:
            bool: 실행 명령 성공 여부 (창이 뜰 때까지 기다리지 않음)

        Example:
            wm = WindowManager()
            wm.launch_app("Visual Studio Code", project_hint="C:/my-project")
        """
        try:
            # 직접 지정한 명령어가 있으면 사용
            if launch_cmd:
                subprocess.Popen(launch_cmd, shell=True)
                print(f"✅ 앱 실행 명령 전송: {launch_cmd}")
                return True

            # VS Code 자동 감지
            if _is_vscode(name):
                return _launch_vscode(project_hint)

            # 메모장 자동 감지
            if _is_notepad(name):
                subprocess.Popen(["notepad.exe"])
                print("✅ 메모장 실행")
                return True

            print(f"⚠️ {name}의 실행 방법을 알 수 없습니다. launch_cmd를 지정해주세요.")
            return False

        except Exception as e:
            print(f"❌ 앱 실행 실패: {e}")
            return False

    # ========================================================================
    # ✅ 상태 확인
    # ========================================================================

    def is_app_running(self, name: str) -> bool:
        """
        ✅ 애플리케이션 실행 여부 확인

        pygetwindow로 윈도우 제목 목록을 검색하여 판단합니다.

        Args:
            name (str): 확인할 애플리케이션 이름 또는 정규식 패턴

        Returns:
            bool: 실행 여부

        Example:
            wm = WindowManager()
            if wm.is_app_running("Visual Studio Code"):
                print("VS Code가 실행 중입니다")
        """
        try:
            pattern = name if _is_regex(name) else f".*{re.escape(name)}.*"
            compiled = re.compile(pattern, re.IGNORECASE)
            titles = gw.getAllTitles()
            return any(compiled.search(t) for t in titles if t.strip())
        except Exception as e:
            print(f"❌ 앱 실행 확인 실패 ({name}): {e}")
            return False

    def get_active_window_title(self) -> str:
        """
        📋 현재 활성 윈도우 제목 가져오기

        pygetwindow를 사용하여 현재 포커스된 윈도우의 제목을 반환합니다.

        Returns:
            str: 활성 윈도우의 제목. 없으면 "Unknown"

        Example:
            wm = WindowManager()
            title = wm.get_active_window_title()
            print(f"현재 활성 창: {title}")
        """
        try:
            active = gw.getActiveWindow()
            if active and active.title:
                return active.title
            return "Unknown"
        except Exception:
            return "Unknown"


# ============================================================================
# 🔧 내부 유틸리티
# ============================================================================


def _is_regex(pattern: str) -> bool:
    """정규식 패턴인지 판단 (메타문자 포함 여부)"""
    return bool(re.search(r"[.*+?^${}()|\\[\]]", pattern))


def _is_vscode(name: str) -> bool:
    """VS Code 관련 이름인지 판단"""
    lower = name.lower()
    return any(kw in lower for kw in ["visual studio code", "vscode", "vs code", "code"])


def _is_notepad(name: str) -> bool:
    """메모장 관련 이름인지 판단"""
    lower = name.lower()
    return any(kw in lower for kw in ["메모장", "notepad"])


def _select_best_title(titles: list[str], project_hint: str) -> str:
    """
    🎯 다중 윈도우 제목 중 최적의 것을 선택

    VS Code 제목 형식: "filename - project_folder - Visual Studio Code"

    선택 우선순위:
      1. project_hint가 제목에 포함된 창
      2. config.py의 TARGET_PROJECT_PATH의 폴더명이 포함된 창
      3. 첫 번째 매칭 (fallback)

    Args:
        titles (List[str]): 매칭된 윈도우 제목 목록
        project_hint (str): 프로젝트 힌트

    Returns:
        str: 선택된 윈도우 제목
    """
    if len(titles) == 1:
        return titles[0]

    # project_hint로 필터링
    if project_hint:
        hint_lower = project_hint.lower()
        for title in titles:
            if hint_lower in title.lower():
                print(f"📌 프로젝트 힌트로 창 선택: {title}")
                return title

    # config.py의 TARGET_PROJECT_PATH에서 폴더명 추출 시도
    try:
        from config import TARGET_PROJECT_PATH

        if TARGET_PROJECT_PATH:
            folder_name = os.path.basename(TARGET_PROJECT_PATH.rstrip("/\\"))
            if folder_name:
                folder_lower = folder_name.lower()
                for title in titles:
                    if folder_lower in title.lower():
                        print(f"📌 TARGET_PROJECT_PATH로 창 선택: {title}")
                        return title
    except (ImportError, AttributeError):
        pass

    # 다중 매칭 경고 + 첫 번째 반환
    if len(titles) > 1:
        print(f"⚠️ 여러 창이 매칭됩니다 ({len(titles)}개). 첫 번째를 선택합니다:")
        for i, t in enumerate(titles):
            print(f"   [{i}] {t}")
        print("   💡 config.py의 TARGET_PROJECT_PATH를 설정하면 정확한 창을 선택할 수 있습니다.")

    return titles[0]


def _launch_vscode(project_path: str = "") -> bool:
    """
    🚀 VS Code 실행

    config.py의 VSCODE_EXE_PATH를 우선 사용하고,
    없으면 PATH에서 "code" 명령어를 검색합니다.

    Args:
        project_path (str): 열 프로젝트 경로 (비어있으면 빈 VS Code 실행)

    Returns:
        bool: 실행 명령 성공 여부
    """
    # config에서 exe 경로 가져오기
    exe_path = ""
    try:
        from config import VSCODE_EXE_PATH

        exe_path = VSCODE_EXE_PATH
    except (ImportError, AttributeError):
        pass

    # exe 경로가 있으면 직접 실행
    if exe_path and os.path.exists(exe_path):
        cmd = [exe_path]
        if project_path and os.path.exists(project_path):
            cmd.append(project_path)
        subprocess.Popen(cmd)
        print(f"✅ VS Code 실행 (exe): {' '.join(cmd)}")
        return True

    # PATH에서 code 명령어 검색
    code_path = shutil.which("code")
    if code_path is None:
        print("❌ VS Code를 실행할 수 없습니다:")
        print("   - 'code' 명령어가 PATH에 없습니다")
        print("   - config.py의 VSCODE_EXE_PATH를 설정해주세요")
        print("   💡 VS Code에서 Ctrl+Shift+P → 'Shell Command: Install code' 실행")
        return False

    # code CLI로 실행
    cmd = ["code"]
    if project_path and os.path.exists(project_path):
        cmd.append(project_path)
    subprocess.Popen(cmd, shell=True)
    print(f"✅ VS Code 실행 (CLI): {' '.join(cmd)}")
    return True
