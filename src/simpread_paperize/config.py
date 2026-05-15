"""默认配置与常量。"""

from pathlib import Path

DEFAULT_PAPER = "A4"
DEFAULT_MARGIN = "14mm"
MAX_TITLE_FILENAME_LEN = 120

# 包内资源根（安装后位于 site-packages/simpread_paperize/）
PACKAGE_ROOT = Path(__file__).resolve().parent


def styles_dir() -> Path:
    return PACKAGE_ROOT / "assets" / "styles"


def runtime_js_path() -> Path:
    return PACKAGE_ROOT / "runtime_patch.js"
