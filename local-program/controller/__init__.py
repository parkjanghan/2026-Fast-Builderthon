# ============================================================================
# 📁 controller/__init__.py - 컨트롤러 패키지 초기화
# ============================================================================
#
# 🎯 역할:
#   에디터 제어 관련 모듈들을 하나의 패키지로 묶습니다.
#   EditorController를 외부에서 쉽게 임포트할 수 있도록 재공개합니다.
#
# 📦 포함 모듈:
#   - window: 윈도우 관리 (WindowManager)
#   - keyboard: 키보드 제어 (KeyboardController)
#   - executor: 명령 실행 디스패처 (EditorController)
#
# 💡 사용 예시:
#   from controller import EditorController
#   
#   controller = EditorController()
#   result = controller.execute(command)
#
# ============================================================================

from controller.executor import EditorController

__all__ = ["EditorController"]
