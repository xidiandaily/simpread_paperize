"""运行时数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertOptions:
    """单次转换 / CLI 解析后的选项。"""

    input_path: Path
    output_pdf: Path | None = None
    output_dir: Path | None = None
    recursive: bool = False
    paper: str = "A4"
    margin: str = "14mm"
    debug: bool = False
    overwrite: bool = False
    print_background: bool = True
    prefer_css_page_size: bool = True


@dataclass
class CleanResult:
    """清洗阶段输出。"""

    title: str
    html: str
    source_type: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConvertResult:
    """单次文件转换结果。"""

    input_path: Path
    output_path: Path | None
    success: bool
    message: str
    debug_dir: Path | None = None
