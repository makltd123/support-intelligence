"""Тесты оркестратора. Все агенты и вызовы модели подменены — сети нет."""

import pytest

import agent_synthesizer as syn


@pytest.fixture(autouse=True)
def _env(filled_env):
    """synthesize() берёт предел шагов из настроек, поэтому ключи нужны даже офлайн."""
    import base_agent
    base_agent.settings.cache_clear()
    yield
    base_agent.settings.cache_clear()


@pytest.fixture
def fake_agents(monkeypatch):
    """Подменяет трёх агентов и считает вызовы."""
    calls = []

    def make(key):
        def agent(question):
            calls.append((key, question))
            return f"{key}:{question}"
        return agent

    monkeypatch.setattr(syn, "AGENTS", {
        "analyze_problems": ("problems", make("problems")),
        "analyze_features": ("features", make("features")),
        "analyze_sentiment": ("sentiment", make("sentiment")),
    })
    return calls


def scripted_chat(monkeypatch, replies):
    """Отдаёт заготовленные ответы модели по очереди."""
    queue = list(replies)
    seen = []

    def fake_chat(messages, what=""):
        seen.append(messages[-1]["content"])
        return queue.pop(0) if queue else '{"action": "finish"}'

    monkeypatch.setattr(syn, "chat", fake_chat)
    return seen


# --- разбор JSON ---------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ('{"action": "finish"}', {"action": "finish"}),
    ('```json\n{"action": "finish"}\n```', {"action": "finish"}),
    ('Вот ответ: {"action": "finish", "answer": "ок"} — всё', {"action": "finish", "answer": "ок"}),
    ('{"action": "finish", "answer": "строка с { и } внутри"}',
     {"action": "finish", "answer": "строка с { и } внутри"}),
    ('{"action": "finish", "answer": "а \\"б\\" в"}', {"action": "finish", "answer": 'а "б" в'}),
])
def test_extract_json_ok(raw, expected):
    assert syn.extract_json(raw) == expected


def test_extract_json_tolerates_literal_newlines():
    parsed = syn.extract_json('{"action": "finish", "answer": "строка1\nстрока2"}')
    assert parsed["answer"] == "строка1\nстрока2"


@pytest.mark.parametrize("raw", ["", "совсем не json", "{сломано", "[1, 2]", None])
def test_extract_json_returns_none(raw):
    assert syn.extract_json(raw) is None


# --- цикл синтезатора ---------------------------------------------------

def test_happy_path_calls_each_agent_once(fake_agents, monkeypatch):
    scripted_chat(monkeypatch, [
        '{"action": "analyze_problems", "input": "проблемы"}',
        '{"action": "analyze_features", "input": "пожелания"}',
        '{"action": "analyze_sentiment", "input": "тональность"}',
    ])
    report = syn.synthesize("вопрос", progress=lambda _m: None)
    assert set(report) == {"problems", "features", "sentiment"}
    assert [key for key, _ in fake_agents] == ["problems", "features", "sentiment"]


def test_unknown_action_does_not_crash(fake_agents, monkeypatch):
    """Регрессия: при неизвестном action падало NameError на необъявленном result."""
    scripted_chat(monkeypatch, [
        '{"action": "analyze_everything", "input": "x"}',
        '{"action": "analyze_problems", "input": "x"}',
        '{"action": "analyze_features", "input": "x"}',
        '{"action": "analyze_sentiment", "input": "x"}',
    ])
    report = syn.synthesize("вопрос", progress=lambda _m: None)
    assert all(report.get(k) for k in ("problems", "features", "sentiment"))


def test_garbage_reply_does_not_crash(fake_agents, monkeypatch):
    """Регрессия: не-JSON ответ модели ронял запуск через json.JSONDecodeError."""
    scripted_chat(monkeypatch, [
        "Привет! Сейчас подумаю, какой инструмент взять.",
        '{"action": "analyze_problems", "input": "x"}',
        '{"action": "analyze_features", "input": "x"}',
        '{"action": "analyze_sentiment", "input": "x"}',
    ])
    report = syn.synthesize("вопрос", progress=lambda _m: None)
    assert len(report) == 3


def test_early_finish_is_completed_directly(fake_agents, monkeypatch):
    """Если модель сказала finish раньше срока, разделы добираются напрямую."""
    scripted_chat(monkeypatch, ['{"action": "finish", "answer": "всё"}'])
    report = syn.synthesize("вопрос", progress=lambda _m: None)
    assert set(report) == {"problems", "features", "sentiment"}
    assert len(fake_agents) == 3


def test_loop_is_bounded(fake_agents, monkeypatch):
    """Регрессия: while True без ограничения мог жечь токены бесконечно."""
    seen = scripted_chat(monkeypatch, ["не json"] * 50)
    report = syn.synthesize("вопрос", max_steps=4, progress=lambda _m: None)
    assert len(seen) == 4
    assert len(report) == 3


def test_repeated_tool_call_is_not_paid_for_twice(fake_agents, monkeypatch):
    scripted_chat(monkeypatch, [
        '{"action": "analyze_problems", "input": "a"}',
        '{"action": "analyze_problems", "input": "a"}',
        '{"action": "analyze_features", "input": "b"}',
        '{"action": "analyze_sentiment", "input": "c"}',
    ])
    syn.synthesize("вопрос", progress=lambda _m: None)
    assert [key for key, _ in fake_agents].count("problems") == 1


def test_agent_input_defaults_to_question(fake_agents, monkeypatch):
    scripted_chat(monkeypatch, ['{"action": "analyze_problems"}'])
    syn.synthesize("исходный вопрос", progress=lambda _m: None)
    assert fake_agents[0] == ("problems", "исходный вопрос")


@pytest.mark.parametrize("question", ["", "   ", None])
def test_empty_question_rejected(question):
    with pytest.raises(ValueError):
        syn.synthesize(question)


def test_progress_callback_receives_messages(fake_agents, monkeypatch):
    scripted_chat(monkeypatch, ['{"action": "finish"}'])
    notes = []
    syn.synthesize("вопрос", progress=notes.append)
    assert notes and any("Добираю" in n for n in notes)
