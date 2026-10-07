"""Подбор шрифта для PDF-отчёта на любой ОС.

Отчёт на русском, поэтому нужен TTF с кириллицей. Порядок поиска:

1. пути из переменных REPORT_FONT_REGULAR / REPORT_FONT_BOLD;
2. типовые системные шрифты Windows, macOS и Linux;
3. если ничего не нашлось - понятная ошибка с подсказкой, что установить.

Встроенные в reportlab шрифты (Helvetica, Vera) кириллицу не содержат,
поэтому в качестве запасного варианта они не годятся.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

REGULAR_NAME = "ReportSans"
BOLD_NAME = "ReportSans-Bold"

#: Проба на кириллицу: если в шрифте нет этих символов, он не подходит.
CYRILLIC_PROBE = (
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
)

_WINDOWS_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

#: Пары (обычный, жирный) в порядке предпочтения.
FONT_CANDIDATES: tuple[tuple[str, str], ...] = (
    # Windows
    (str(_WINDOWS_DIR / "arial.ttf"), str(_WINDOWS_DIR / "arialbd.ttf")),
    (str(_WINDOWS_DIR / "segoeui.ttf"), str(_WINDOWS_DIR / "segoeuib.ttf")),
    # macOS
    (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ),
    (
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ),
    # Linux
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
        "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ),
)

_INSTALL_HINT = {
    "linux": "установи шрифты: sudo apt install fonts-dejavu-core (или fonts-liberation)",
    "darwin": "проверь наличие /System/Library/Fonts/Supplemental/Arial.ttf",
    "win32": r"проверь наличие C:\Windows\Fonts\arial.ttf",
}


class FontError(RuntimeError):
    """Не удалось найти TTF-шрифт с поддержкой кириллицы."""


@dataclass(frozen=True)
class FontSet:
    """Имена зарегистрированных в reportlab шрифтов плюс путь к файлу."""

    regular: str
    bold: str
    source: str


def supports_cyrillic(path: str | os.PathLike[str]) -> bool:
    """True, если TTF по этому пути содержит глифы для русских букв."""
    try:
        face = TTFont("__probe__", str(path)).face
    except Exception:
        return False
    return all(ord(char) in face.charToGlyph for char in CYRILLIC_PROBE)


def _env_candidate() -> tuple[str, str] | None:
    regular = os.environ.get("REPORT_FONT_REGULAR", "").strip()
    if not regular:
        return None
    bold = os.environ.get("REPORT_FONT_BOLD", "").strip() or regular
    return regular, bold


def find_font_pair() -> tuple[str, str]:
    """Найти пару (обычный, жирный) TTF с кириллицей.

    Шрифт из REPORT_FONT_REGULAR проверяется первым; если он задан, но не
    подходит, об этом говорится в ошибке отдельно - молча подменять его на
    системный было бы неожиданно.
    """
    env_pair = _env_candidate()
    if env_pair is not None:
        regular, bold = env_pair
        if not Path(regular).is_file():
            raise FontError(
                f"REPORT_FONT_REGULAR указывает на несуществующий файл: {regular}"
            )
        if not supports_cyrillic(regular):
            raise FontError(
                f"Шрифт {regular} из REPORT_FONT_REGULAR не содержит кириллицу."
            )
        if not Path(bold).is_file():
            bold = regular
        return regular, bold

    for regular, bold in FONT_CANDIDATES:
        if not Path(regular).is_file() or not supports_cyrillic(regular):
            continue
        if not Path(bold).is_file():
            bold = regular
        return regular, bold

    hint = _INSTALL_HINT.get(sys.platform, "установи любой TTF с кириллицей")
    raise FontError(
        "Не найден TTF-шрифт с поддержкой кириллицы. "
        f"{hint}, либо задай путь в REPORT_FONT_REGULAR (и REPORT_FONT_BOLD)."
    )


_REGISTERED: FontSet | None = None


def register_fonts() -> FontSet:
    """Зарегистрировать шрифты в reportlab. Повторные вызовы безопасны."""
    global _REGISTERED
    if _REGISTERED is not None:
        return _REGISTERED

    regular_path, bold_path = find_font_pair()
    pdfmetrics.registerFont(TTFont(REGULAR_NAME, regular_path))
    pdfmetrics.registerFont(TTFont(BOLD_NAME, bold_path))
    pdfmetrics.registerFontFamily(
        REGULAR_NAME, normal=REGULAR_NAME, bold=BOLD_NAME,
        italic=REGULAR_NAME, boldItalic=BOLD_NAME,
    )
    _REGISTERED = FontSet(REGULAR_NAME, BOLD_NAME, regular_path)
    return _REGISTERED
