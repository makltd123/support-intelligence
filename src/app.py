"""Веб-интерфейс на Gradio."""

from __future__ import annotations

import os
import tempfile
import traceback
import uuid
from pathlib import Path

import gradio as gr

from agent_synthesizer import synthesize
from config import ConfigError
from report_generator import generate_report

ERROR_HINT = (
    "Анализ не удался. Проверь ключи в .env и то, что коллекция Qdrant заполнена "
    "(src/qdrant_upload.py). Подробности — в консоли."
)

#: Каждый запуск пишет свой PDF: иначе параллельные запросы перетирают файл друг друга.
OUTPUT_DIR = Path(os.environ.get("REPORT_DIR") or tempfile.gettempdir()) / "support-intelligence"


def run_analysis(question: str):
    """Обработчик кнопки. Ошибки показываем в интерфейсе, а не роняем сервер."""
    if not question or not question.strip():
        return "Введи вопрос для анализа.", "", "", None

    try:
        report = synthesize(question)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"report-{uuid.uuid4().hex[:8]}.pdf"
        generate_report(report, str(output_path))
    except ConfigError as exc:
        return str(exc), "", "", None
    except Exception:  # noqa: BLE001 - интерфейс не должен падать молча
        traceback.print_exc()
        return ERROR_HINT, "", "", None

    return (
        report.get("problems", ""),
        report.get("features", ""),
        report.get("sentiment", ""),
        str(output_path),
    )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Customer Support Intelligence") as demo:
        gr.Markdown("# AI Customer Support Intelligence")
        gr.Markdown("Введи вопрос для анализа тикетов поддержки")

        question = gr.Textbox(
            label="Вопрос",
            placeholder="например: анализ проблем в категории Billing",
        )
        btn = gr.Button("Запустить анализ", variant="primary")

        with gr.Row():
            problems = gr.Textbox(label="Топ проблем", lines=10)
            features = gr.Textbox(label="Feature Requests", lines=10)

        sentiment = gr.Textbox(label="Тональность клиентов", lines=6)
        pdf_output = gr.File(label="Скачать PDF отчёт")

        btn.click(
            fn=run_analysis,
            inputs=question,
            outputs=[problems, features, sentiment, pdf_output],
        )
    return demo


def main() -> None:
    build_ui().launch()


if __name__ == "__main__":
    main()
