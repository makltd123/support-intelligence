import os

import pytest
import reportlab

import fonts


def test_resolves_a_cyrillic_font(clean_env):
    regular, bold = fonts.find_font_pair()
    assert fonts.supports_cyrillic(regular)
    assert bold


def test_register_is_idempotent(clean_env):
    first = fonts.register_fonts()
    second = fonts.register_fonts()
    assert first == second
    assert first.regular == fonts.REGULAR_NAME


def test_env_override_missing_file_is_reported(clean_env):
    clean_env.setenv("REPORT_FONT_REGULAR", "/nope/missing.ttf")
    with pytest.raises(fonts.FontError, match="REPORT_FONT_REGULAR"):
        fonts.find_font_pair()


def test_font_without_cyrillic_is_rejected(clean_env, tmp_path):
    """В reportlab вложен Vera.ttf без кириллицы - на нём и проверяем."""
    vera = os.path.join(os.path.dirname(reportlab.__file__), "fonts", "Vera.ttf")
    assert not fonts.supports_cyrillic(vera)
    clean_env.setenv("REPORT_FONT_REGULAR", vera)
    with pytest.raises(fonts.FontError, match="кириллиц"):
        fonts.find_font_pair()


def test_missing_file_is_not_cyrillic():
    assert fonts.supports_cyrillic("/definitely/not/a/font.ttf") is False
