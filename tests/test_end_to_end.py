"""Сквозной прогон: CSV -> эмбеддинги -> Qdrant -> агенты -> PDF.

Mistral подменён детерминированным фейком, Qdrant поднят в памяти, поэтому
тест проверяет именно склейку модулей между собой, а не внешние сервисы.
"""

from __future__ import annotations

import hashlib

import pandas as pd
import pytest
from pypdf import PdfReader
from qdrant_client import QdrantClient

VECTOR_SIZE = 8

TICKETS = [
    ("Authorization", "Не могу войти в аккаунт", "Сбросили пароль", "Open", "High", 2),
    ("Authorization", "Не приходит код 2FA", "Эскалировали", "Closed", "Urgent", 1),
    ("Billing", "Списали дважды", "Оформили возврат", "Resolved", "High", 3),
    ("Feature Request", "Добавьте экспорт в Excel", "Передали продукту", "Open", "Low", 4),
]


def fake_vector(text: str) -> list[float]:
    """Устойчивый псевдо-эмбеддинг: одинаковый текст -> одинаковый вектор."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [digest[i] / 255.0 for i in range(VECTOR_SIZE)]


class FakeEmbeddings:
    def create(self, *, model, inputs):
        class Item:
            def __init__(self, embedding):
                self.embedding = embedding

        class Result:
            def __init__(self, data):
                self.data = data

        return Result([Item(fake_vector(text)) for text in inputs])


class FakeChat:
    """Отвечает как дисциплинированный синтезатор, затем как агент."""

    def __init__(self):
        self.script = [
            '{"action": "analyze_problems", "input": "проблемы авторизации"}',
            '{"action": "analyze_features", "input": "что просят клиенты"}',
            '{"action": "analyze_sentiment", "input": "тональность"}',
            '{"action": "finish", "answer": "готово"}',
        ]
        self.contexts = []

    def complete(self, *, model, messages):
        user = messages[-1]["content"]
        if "<тикет" in user:
            self.contexts.append(user)
            text = "Разбор по найденным тикетам (Тикет 1)."
        elif self.script:
            text = self.script.pop(0)
        else:
            text = '{"action": "finish"}'

        class Message:
            def __init__(self, content):
                self.content = content

        class Choice:
            def __init__(self, message):
                self.message = message

        class Response:
            def __init__(self, choices):
                self.choices = choices

        return Response([Choice(Message(text))])


class FakeMistral:
    def __init__(self):
        self.embeddings = FakeEmbeddings()
        self.chat = FakeChat()


@pytest.fixture
def pipeline(tmp_path, filled_env, monkeypatch):
    """Готовит коллекцию в памяти и подменяет клиентов во всех модулях."""
    import base_agent

    csv_path = tmp_path / "sample.csv"
    pd.DataFrame([
        {
            "category": c, "issue_description": d, "resolution_notes": r,
            "status": s, "priority": p, "customer_satisfaction_score": score,
        }
        for c, d, r, s, p, score in TICKETS
    ]).to_csv(csv_path, index=False)

    fake = FakeMistral()
    client = QdrantClient(":memory:")

    base_agent.settings.cache_clear()
    base_agent.mistral_client.cache_clear()
    base_agent.qdrant.cache_clear()
    monkeypatch.setattr(base_agent, "mistral_client", lambda: fake)
    monkeypatch.setattr(base_agent, "qdrant", lambda: client)

    monkeypatch.setenv("SAMPLE_PATH", str(csv_path))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(tmp_path / "emb.npy"))
    monkeypatch.setenv("EMBED_PAUSE_SECONDS", "0")
    monkeypatch.setenv("UPLOAD_PAUSE_SECONDS", "0")

    yield fake, client, tmp_path

    # mistral_client/qdrant возвращает monkeypatch, тут остаётся только настройки.
    base_agent.settings.cache_clear()


def test_full_pipeline_builds_a_report(pipeline, monkeypatch):
    import importlib

    import embeddings
    import qdrant_upload
    importlib.reload(embeddings)
    importlib.reload(qdrant_upload)
    monkeypatch.setattr(embeddings, "mistral_client", lambda: pipeline[0])
    monkeypatch.setattr(qdrant_upload, "qdrant", lambda: pipeline[1])

    assert embeddings.main() == 0
    assert qdrant_upload.main() == 0

    client = pipeline[1]
    assert client.count("support_tickets").count == len(TICKETS)

    from agent_synthesizer import synthesize
    from report_generator import generate_report

    report = synthesize("анализ проблем в авторизации", progress=lambda _m: None)
    assert set(report) == {"problems", "features", "sentiment"}
    assert all(report.values())

    # Агенты увидели реальный контекст из Qdrant, а не пустую строку.
    assert any("Не могу войти в аккаунт" in ctx for ctx in pipeline[0].chat.contexts)

    out = pipeline[2] / "report.pdf"
    generate_report(report, str(out))
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(out)).pages)
    assert "Топ проблем" in text and "Тональность клиентов" in text


def test_embeddings_resume_after_interruption(pipeline, monkeypatch):
    """Обрыв на середине не должен терять уже посчитанные векторы."""
    import importlib

    import numpy as np

    import embeddings
    importlib.reload(embeddings)
    monkeypatch.setattr(embeddings, "mistral_client", lambda: pipeline[0])
    monkeypatch.setattr(embeddings, "BATCH_SIZE", 2)

    calls = {"n": 0}
    real_embed = embeddings.embed_batch

    def flaky(texts):
        calls["n"] += 1
        if calls["n"] == 2:
            raise KeyboardInterrupt
        return real_embed(texts)

    monkeypatch.setattr(embeddings, "embed_batch", flaky)
    with pytest.raises(KeyboardInterrupt):
        embeddings.main()

    partial = np.load(embeddings.PARTIAL_PATH, allow_pickle=False)
    assert len(partial) == 2

    monkeypatch.setattr(embeddings, "embed_batch", real_embed)
    assert embeddings.main() == 0
    final = np.load(embeddings.EMBEDDINGS_PATH, allow_pickle=False)
    assert final.shape == (len(TICKETS), VECTOR_SIZE)
    assert not embeddings.PARTIAL_PATH.exists()
