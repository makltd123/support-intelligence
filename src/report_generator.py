"""Сборка PDF-отчёта из результатов работы агентов."""

from __future__ import annotations

import html
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from fonts import register_fonts

# Цветовая палитра
DARK_BLUE = colors.HexColor('#1A2E4A')
ACCENT = colors.HexColor('#2E86AB')
LIGHT_BG = colors.HexColor('#F0F4F8')
DIVIDER = colors.HexColor('#CBD5E0')
WHITE = colors.white
TEXT = colors.HexColor('#2D3748')
MUTED = colors.HexColor('#718096')

EMPTY_SECTION = "Нет данных"

#: Разделы отчёта: ключ в словаре, номер и заголовок.
SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("problems", "01", "Топ проблем"),
    ("features", "02", "Feature Requests"),
    ("sentiment", "03", "Тональность клиентов"),
)


def clean_markdown(text: str) -> str:
    """Убрать разметку Markdown и подготовить текст для Paragraph.

    reportlab разбирает текст абзаца как мини-HTML, поэтому символы `&`, `<`
    и `>` экранируются. Без этого фрагменты вида `<unknown>` молча выпадали
    из отчёта.
    """
    if text is None:
        return EMPTY_SECTION
    text = str(text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = html.escape(text, quote=False)
    return text.replace('\n\n', '<br/><br/>').replace('\n', '<br/>')


def make_styles(regular: str, bold: str) -> dict[str, ParagraphStyle]:
    return {
        'title': ParagraphStyle(
            'CustomTitle', fontName=bold, fontSize=28,
            textColor=WHITE, spaceAfter=8, leading=34,
        ),
        'subtitle': ParagraphStyle(
            'CustomSubtitle', fontName=regular, fontSize=13,
            textColor=colors.HexColor('#BEE3F8'), spaceAfter=0,
        ),
        'section': ParagraphStyle(
            'SectionTitle', fontName=bold, fontSize=18,
            textColor=DARK_BLUE, spaceBefore=6, spaceAfter=12, leading=24,
        ),
        'body': ParagraphStyle(
            'CustomBody', fontName=regular, fontSize=10,
            textColor=TEXT, leading=16, spaceAfter=6,
        ),
        'num': ParagraphStyle(
            'Num', fontName=bold, fontSize=36,
            textColor=LIGHT_BG, leading=40,
        ),
    }


def _title_page_painter(regular: str):
    def draw_title_page(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(DARK_BLUE)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, h * 0.38, w, 4, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor('#0F1E30'))
        canvas.rect(0, 0, w, h * 0.38, fill=1, stroke=0)
        canvas.setFont(regular, 10)
        canvas.setFillColor(MUTED)
        stamp = datetime.now().astimezone().strftime('%d.%m.%Y')
        canvas.drawString(20 * mm, 25 * mm, f"Сгенерировано: {stamp}")
        canvas.restoreState()

    return draw_title_page


def _page_number_painter(regular: str):
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont(regular, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 12 * mm, "AI Customer Support Intelligence")
        canvas.drawRightString(190 * mm, 12 * mm, f"Стр. {canvas.getPageNumber()}")
        canvas.setStrokeColor(DIVIDER)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
        canvas.restoreState()

    return add_page_number


def generate_report(report_data: dict, output_path: str = "report.pdf") -> str:
    """Собрать PDF и вернуть путь к нему."""
    fontset = register_fonts()
    styles = make_styles(fontset.regular, fontset.bold)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
        title="AI Customer Support Intelligence Report",
    )

    story = [
        Spacer(1, 60 * mm),
        Paragraph("AI Customer Support", styles['title']),
        Paragraph("Intelligence Report", styles['title']),
        Spacer(1, 6),
        Paragraph("Автоматический анализ тикетов поддержки", styles['subtitle']),
        PageBreak(),
    ]

    for position, (key, number, heading) in enumerate(SECTIONS):
        if position:
            story.append(PageBreak())
        body = report_data.get(key) or EMPTY_SECTION
        story += [
            Spacer(1, 8),
            Paragraph(number, styles['num']),
            Paragraph(heading, styles['section']),
            HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=14),
            Paragraph(clean_markdown(body), styles['body']),
        ]

    doc.build(
        story,
        onFirstPage=_title_page_painter(fontset.regular),
        onLaterPages=_page_number_painter(fontset.regular),
    )
    return output_path


if __name__ == "__main__":
    test_data = {
        "problems": "Основная проблема — невозможность входа в аккаунт.\n\n"
                    "Security Concern: 4 тикета.\nSubscription Cancellation: 5 тикетов.",
        "features": "Клиенты просят улучшить синхронизацию данных и упростить "
                    "восстановление пароля (Billing & Payments).",
        "sentiment": "Тональность в основном негативная. 14 из 20 тикетов "
                     "содержат выражение недовольства.",
    }
    path = generate_report(test_data, "test_report.pdf")
    print(f"PDF сохранён: {path}")
