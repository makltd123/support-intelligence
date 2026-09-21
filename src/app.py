import gradio as gr
from agent_synthesizer import synthesize
from report_generator import generate_report

def run_analysis(question):
    report = synthesize(question)
    generate_report(report, "report.pdf")
    return report.get("problems", ""), report.get("features", ""), report.get("sentiment", ""), "report.pdf"

with gr.Blocks(title="AI Customer Support Intelligence") as demo:
    gr.Markdown("# AI Customer Support Intelligence")
    gr.Markdown("Введи вопрос для анализа тикетов поддержки")
    
    question = gr.Textbox(label="Вопрос", placeholder="например: анализ проблем в категории Billing")
    btn = gr.Button("Запустить анализ", variant="primary")
    
    with gr.Row():
        problems = gr.Textbox(label="Топ проблем", lines=10)
        features = gr.Textbox(label="Feature Requests", lines=10)
    
    sentiment = gr.Textbox(label="Тональность клиентов", lines=6)
    pdf_output = gr.File(label="Скачать PDF отчёт")
    
    btn.click(fn=run_analysis, inputs=question, outputs=[problems, features, sentiment, pdf_output])

demo.launch()