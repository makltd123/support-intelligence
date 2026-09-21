from agent_analyst import analyze as analyze_problems
from agent_features import analyze as analyze_features
from agent_sentiment import analyze as analyze_sentiment
from base_agent import get_embedding, text_vectors, format_context, client
import json
from report_generator import generate_report


def synthesize(question):
    messages = [
        {"role": "system", "content": """Ты синтезатор мультиагентной ИИ-системы.

У тебя есть следующие инструменты:
- analyze_problems: анализирует топ проблем из тикетов
- analyze_features: извлекает что клиенты просят улучшить
- analyze_sentiment: анализирует тональность клиентов по категориям
Ты ОБЯЗАН использовать все эти инструменты по порядку!
Только после всех трёх — вызови finish
Не переходи к finish пока не получил результаты всех трёх инструментов.
Когда ты уже вызвал analyze_problems, analyze_features И analyze_sentiment — 
НЕМЕДЛЕННО вызови finish. Больше никаких инструментов не вызывай.

Отвечай только в JSON на русском. Два возможных формата:

Когда нужен инструмент:
{"action": "analyze_problems", "input": "твой вопрос"}

Когда готов дать финальный ответ:
{"action": "finish", "answer": "финальный отчёт..."}

Не выдумывай данные. Используй только результаты инструментов."""},
        {"role": "user", "content": question}
    ]
    report={}
    while True:
        response = client.chat.complete(
        model="mistral-small-2506",
        messages=messages
        )
        text = response.choices[0].message.content
        print(">>> Mistral говорит:", text)
        clean = text.replace("```json", "").replace("```", "").strip()
        clean = clean.replace('\n', ' ').replace('\r', ' ')
        data = json.loads(clean)
        if data["action"] == "finish":
            return report
        
        if data["action"] == "analyze_problems":
            result = analyze_problems(data["input"])
            report["problems"] = result
        elif data["action"] == "analyze_features":
            result = analyze_features(data["input"])
            report["features"] = result
        elif data["action"] == "analyze_sentiment":
            result = analyze_sentiment(data["input"])
            report["sentiment"] = result
        
        messages.append({"role": "assistant", "content": text})  # ответ модели
        messages.append({"role": "user", "content": f"Результат инструмента {data['action']}: {result}"})  # результат

if __name__ == "__main__":
    report = synthesize("сделай полный анализ проблем в категории авторизации")
    generate_report(report, "report.pdf")
    print("Готово!")