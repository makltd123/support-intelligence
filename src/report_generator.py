from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import re

# Регистрируем шрифты
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))

# Цветовая палитра
DARK_BLUE = colors.HexColor('#1A2E4A')
ACCENT = colors.HexColor('#2E86AB')
LIGHT_BG = colors.HexColor('#F0F4F8')
DIVIDER = colors.HexColor('#CBD5E0')
WHITE = colors.white
TEXT = colors.HexColor('#2D3748')
MUTED = colors.HexColor('#718096')


def clean_markdown(text):
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = text.replace('\n\n', '<br/><br/>').replace('\n', '<br/>')
    return text


def make_styles():
    title_style = ParagraphStyle(
        'CustomTitle',
        fontName='Arial-Bold',
        fontSize=28,
        textColor=WHITE,
        spaceAfter=8,
        leading=34,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        fontName='Arial',
        fontSize=13,
        textColor=colors.HexColor('#BEE3F8'),
        spaceAfter=0,
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        fontName='Arial-Bold',
        fontSize=18,
        textColor=DARK_BLUE,
        spaceBefore=6,
        spaceAfter=12,
        leading=24,
    )
    body_style = ParagraphStyle(
        'CustomBody',
        fontName='Arial',
        fontSize=10,
        textColor=TEXT,
        leading=16,
        spaceAfter=6,
    )
    num_style = ParagraphStyle(
        'Num',
        fontName='Arial-Bold',
        fontSize=36,
        textColor=LIGHT_BG,
        leading=40,
    )
    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'section': section_title,
        'body': body_style,
        'num': num_style,
    }


def draw_title_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h * 0.38, w, 4, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#0F1E30'))
    canvas.rect(0, 0, w, h * 0.38, fill=1, stroke=0)
    canvas.setFont('Arial', 10)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 25 * mm, f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y')}")
    canvas.restoreState()


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Arial', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, "AI Customer Support Intelligence")
    canvas.drawRightString(190 * mm, 12 * mm, f"Стр. {canvas.getPageNumber()}")
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


def generate_report(report_data: dict, output_path: str = "report.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
    )

    styles = make_styles()
    story = []

    # Титульная страница
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("AI Customer Support", styles['title']))
    story.append(Paragraph("Intelligence Report", styles['title']))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Автоматический анализ тикетов поддержки", styles['subtitle']))
    story.append(PageBreak())

    # Топ проблем
    story.append(Spacer(1, 8))
    story.append(Paragraph("01", styles['num']))
    story.append(Paragraph("Топ проблем", styles['section']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=14))
    story.append(Paragraph(clean_markdown(report_data.get("problems", "Нет данных")), styles['body']))
    story.append(PageBreak())

    # Feature Requests
    story.append(Spacer(1, 8))
    story.append(Paragraph("02", styles['num']))
    story.append(Paragraph("Feature Requests", styles['section']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=14))
    story.append(Paragraph(clean_markdown(report_data.get("features", "Нет данных")), styles['body']))
    story.append(PageBreak())

    # Тональность
    story.append(Spacer(1, 8))
    story.append(Paragraph("03", styles['num']))
    story.append(Paragraph("Тональность клиентов", styles['section']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=14))
    story.append(Paragraph(clean_markdown(report_data.get("sentiment", "Нет данных")), styles['body']))

    doc.build(story, onFirstPage=draw_title_page, onLaterPages=add_page_number)
    print(f"PDF сохранён: {output_path}")


if __name__ == "__main__":
    test_data = {
        "problems": "Основная проблема — невозможность входа в аккаунт.\n\nSecurity Concern: 4 тикета.\nSubscription Cancellation: 5 тикетов.",
        "features": "Клиенты просят улучшить синхронизацию данных и упростить восстановление пароля.",
        "sentiment": "Тональность в основном негативная. 14 из 20 тикетов содержат выражение недовольства.",
    }
    generate_report(test_data, "test_report.pdf")