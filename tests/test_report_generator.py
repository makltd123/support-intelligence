import re

import pytest
from pypdf import PdfReader

import report_generator as rg


def _text(path):
    return "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def test_builds_pdf_on_this_platform(tmp_path):
    """Регрессия: раньше шрифт брался из C:/Windows/Fonts и импорт падал вне Windows."""
    out = tmp_path / "r.pdf"
    assert rg.generate_report({"problems": "A", "features": "B", "sentiment": "C"}, str(out))
    assert out.is_file() and out.stat().st_size > 1000


def test_cyrillic_and_all_sections_present(tmp_path):
    out = tmp_path / "r.pdf"
    rg.generate_report(
        {"problems": "Проблема входа", "features": "Пожелание", "sentiment": "Негатив"},
        str(out),
    )
    text = _text(out)
    for expected in ("Топ проблем", "Feature Requests", "Тональность клиентов",
                     "Проблема входа", "Пожелание", "Негатив"):
        assert expected in text


def test_missing_sections_become_placeholder(tmp_path):
    out = tmp_path / "r.pdf"
    rg.generate_report({"problems": "только проблемы"}, str(out))
    text = _text(out)
    assert text.count(rg.EMPTY_SECTION) == 2


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Billing & Payments", "Billing &amp; Payments"),
        ("SLA <24h> нарушен", "SLA &lt;24h&gt; нарушен"),
        ("**жирный** и *курсив*", "жирный и курсив"),
        ("## Заголовок", "Заголовок"),
        ("строка1\nстрока2", "строка1<br/>строка2"),
        ("абзац1\n\nабзац2", "абзац1<br/><br/>абзац2"),
    ],
)
def test_clean_markdown(raw, expected):
    assert rg.clean_markdown(raw) == expected


def test_clean_markdown_handles_none():
    assert rg.clean_markdown(None) == rg.EMPTY_SECTION


def test_angle_bracket_text_survives_into_pdf(tmp_path):
    """Регрессия: `<unknown attr='1'>` молча выпадал из отчёта."""
    out = tmp_path / "r.pdf"
    rg.generate_report({"problems": "тег <unknown attr='1'> внутри"}, str(out))
    assert "unknown" in re.sub(r"\s+", " ", _text(out))


def test_ampersand_survives_into_pdf(tmp_path):
    out = tmp_path / "r.pdf"
    rg.generate_report({"features": "Billing & Payments"}, str(out))
    assert "Billing & Payments" in re.sub(r"\s+", " ", _text(out))
