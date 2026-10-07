"""Оркестратор: вызывает трёх агентов и собирает из их ответов отчёт.

Синтезатор просит модель выбирать инструмент в формате JSON, но не полагается
на её дисциплину: цикл ограничен по числу шагов, непонятный ответ не роняет
запуск, а любой раздел, который модель так и не заказала, добирается напрямую.
Поэтому функция всегда возвращает отчёт из трёх разделов либо падает с
понятной ошибкой сети/конфигурации.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable

from agent_analyst import analyze as analyze_problems
from agent_features import analyze as analyze_features
from agent_sentiment import analyze as analyze_sentiment
from base_agent import chat, settings

#: action из JSON -> (ключ раздела отчёта, функция агента)
AGENTS: dict[str, tuple[str, Callable[[str], str]]] = {
    "analyze_problems": ("problems", analyze_problems),
    "analyze_features": ("features", analyze_features),
    "analyze_sentiment": ("sentiment", analyze_sentiment),
}

SECTION_KEYS: tuple[str, ...] = tuple(key for key, _ in AGENTS.values())

SYSTEM_PROMPT = """Ты синтезатор мультиагентной ИИ-системы.

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

Не выдумывай данные. Используй только результаты инструментов."""


def _loads(candidate: str) -> dict | None:
    """json.loads, прощающий буквальные переводы строк внутри строковых значений."""
    for text in (candidate, candidate.replace("\r", "").replace("\n", "\\n")):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        return parsed if isinstance(parsed, dict) else None
    return None


def extract_json(text: str) -> dict | None:
    """Достать первый JSON-объект из ответа модели.

    Модель любит обёртывать JSON в ```-блоки и добавлять пояснения до и после,
    поэтому ищем сбалансированные фигурные скобки, а не парсим весь текст.
    """
    if not text:
        return None
    cleaned = text.replace("```json", "```").strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        cleaned = max(parts, key=len) if len(parts) > 1 else cleaned
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for position in range(start, len(cleaned)):
            char = cleaned[position]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start:position + 1]
                    parsed = _loads(candidate)
                    if parsed is None:
                        break
                    return parsed
        start = cleaned.find("{", start + 1)
    return None


def _note(progress: Callable[[str], None] | None, message: str) -> None:
    if progress is None:
        print(message)
    else:
        progress(message)


def _fill_missing(
    report: dict[str, str],
    question: str,
    progress: Callable[[str], None] | None,
) -> None:
    """Добрать разделы, которые оркестратор не заказал."""
    for action, (key, func) in AGENTS.items():
        if report.get(key):
            continue
        _note(progress, f">>> Добираю раздел напрямую: {action}")
        report[key] = func(question)


def missing_sections(report: dict[str, str]) -> Iterable[str]:
    return (key for key in SECTION_KEYS if not report.get(key))


def synthesize(
    question: str,
    *,
    max_steps: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, str]:
    """Собрать отчёт по вопросу. Всегда возвращает три раздела."""
    if not question or not question.strip():
        raise ValueError("Вопрос не может быть пустым.")

    steps = max_steps if max_steps is not None else settings().max_synth_steps
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    report: dict[str, str] = {}

    for _step in range(steps):
        text = chat(messages, what="синтезатор")
        _note(progress, f">>> Mistral говорит: {text[:500]}")
        messages.append({"role": "assistant", "content": text})

        data = extract_json(text)
        if data is None or "action" not in data:
            messages.append({
                "role": "user",
                "content": "Ответ не распознан. Пришли строго один JSON-объект "
                           'вида {"action": "...", "input": "..."} без пояснений.',
            })
            continue

        action = data.get("action")
        if action == "finish":
            break

        if action not in AGENTS:
            messages.append({
                "role": "user",
                "content": f"Инструмента {action!r} нет. Доступны: "
                           f"{', '.join(AGENTS)} и finish.",
            })
            continue

        key, func = AGENTS[action]
        if report.get(key):
            messages.append({
                "role": "user",
                "content": f"Инструмент {action} уже вызван, его результат у тебя есть. "
                           "Вызови следующий или finish.",
            })
            continue

        agent_input = str(data.get("input") or question)
        result = func(agent_input)
        report[key] = result
        messages.append({
            "role": "user",
            "content": f"Результат инструмента {action}: {result}",
        })

        if not list(missing_sections(report)):
            _note(progress, ">>> Все три агента отработали, собираю отчёт.")
            break
    else:
        _note(progress, f">>> Достигнут предел в {steps} шагов.")

    _fill_missing(report, question, progress)
    return report


if __name__ == "__main__":
    from report_generator import generate_report

    built = synthesize("сделай полный анализ проблем в категории авторизации")
    print(f"PDF сохранён: {generate_report(built, 'report.pdf')}")
    print("Готово!")
