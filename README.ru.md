# AI Customer Support Intelligence

[English](README.md) | **Русский**

Мультиагентная RAG-система, которая анализирует тикеты службы поддержки и собирает PDF-отчёт из трёх разделов: главные проблемы, пожелания клиентов и тональность обращений.

## Как это работает

```
Вопрос ──► Синтезатор (Mistral) ──┬──► Агент «Проблемы»     ─┐
                                  ├──► Агент «Пожелания»    ─┼──► Qdrant: 20 похожих тикетов
                                  └──► Агент «Тональность»  ─┘    (эмбеддинги mistral-embed)
                                                │
                                                ▼
                                   PDF-отчёт + веб-интерфейс Gradio
```

- **Синтезатор** — LLM-оркестратор. Он в цикле выбирает, какой агент вызвать, и отвечает в формате JSON. Отчёт готов, когда отработали все три агента.
- **Агенты** ищут в векторной базе Qdrant 20 тикетов, ближайших к вопросу. Отвечают только по найденным тикетам и указывают их номера как источники.
- **Индекс** построен по случайной выборке из 10 000 тикетов.

## Стек

Python · Mistral AI (`mistral-small-2506`, `mistral-embed`) · Qdrant Cloud · Gradio · reportlab · pandas

## Пример отчёта

[docs/example_report.pdf](docs/example_report.pdf) — ответ на запрос «сделай полный анализ проблем в категории авторизации».

## Структура

| Файл | Что делает |
|---|---|
| `src/prepare_dataset.py` | Берёт случайные 10 000 тикетов из полного датасета |
| `src/embeddings.py` | Считает эмбеддинги текстов тикетов через `mistral-embed` |
| `src/qdrant_upload.py` | Создаёт коллекцию в Qdrant и загружает в неё векторы |
| `src/base_agent.py` | Общие функции: эмбеддинг вопроса, поиск в Qdrant, формирование контекста |
| `src/agent_analyst.py` | Агент «Проблемы» |
| `src/agent_features.py` | Агент «Пожелания» |
| `src/agent_sentiment.py` | Агент «Тональность» |
| `src/agent_synthesizer.py` | Оркестратор: вызывает агентов и собирает отчёт |
| `src/report_generator.py` | Генерирует PDF |
| `src/app.py` | Веб-интерфейс на Gradio |
| `experiments/` | Ранние скрипты: анализ одного тикета, первая версия RAG, проверка поиска |

## Запуск

Все команды выполняются из корня проекта.

**1. Зависимости**

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**2. Ключи.** Скопируй `.env.example` в `.env` и заполни:
- `MISTRAL_API_KEY` — ключ из [console.mistral.ai](https://console.mistral.ai);
- `QDRANT_URL` и `QDRANT_API_KEY` — адрес и ключ кластера в [Qdrant Cloud](https://cloud.qdrant.io) (бесплатного кластера хватает).

**3. Данные.** Датасет в репозиторий не входит (74 МБ). Подойдёт любой CSV с колонками `category`, `issue_description`, `resolution_notes`, `priority`, `status`, `customer_satisfaction_score`: положи его в папку `data/` под именем `customer_support_tickets_200k.csv`.

**4. Индекс** (один раз):

```bash
python src/prepare_dataset.py   # выборка 10 000 тикетов -> data/sample_10k.csv
python src/embeddings.py        # эмбеддинги -> data/embeddings.npy (около 10–15 минут)
python src/qdrant_upload.py     # загрузка в Qdrant
```

**5. Анализ**

```bash
python src/app.py               # веб-интерфейс на http://127.0.0.1:7860
python src/agent_synthesizer.py # или сразу отчёт report.pdf по запросу из кода
```

## Ограничения

- PDF использует шрифт Arial из `C:/Windows/Fonts`, поэтому отчёт собирается только на Windows. На другой системе поменяй пути к шрифтам в `src/report_generator.py`.
- Датасет синтетический: тексты собраны из шаблонов, поэтому многие тикеты совпадают дословно, а категория не всегда соответствует описанию. В примере отчёта у всех 20 найденных тикетов одинаковый текст.
- Синтезатор читает ответ модели как JSON. Если модель ответит в другом формате, запуск остановится с ошибкой.

## Лицензия

[MIT](LICENSE)

---

Автор: [Федор Маковский](https://fedor.alqira.ru), ИИ-разработчик. Услуги и проекты с цифрами качества: [fedor.alqira.ru](https://fedor.alqira.ru).
