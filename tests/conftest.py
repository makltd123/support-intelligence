"""Общие фикстуры. Тесты не ходят в сеть и не требуют реальных ключей."""

from __future__ import annotations

import pytest

ENV_KEYS = (
    "MISTRAL_API_KEY",
    "QDRANT_URL",
    "QDRANT_API_KEY",
    "MISTRAL_CHAT_MODEL",
    "MISTRAL_EMBED_MODEL",
    "QDRANT_COLLECTION",
    "RETRIEVAL_TOP_K",
    "MAX_SYNTH_STEPS",
    "REQUEST_RETRIES",
    "REPORT_FONT_REGULAR",
    "REPORT_FONT_BOLD",
)


@pytest.fixture
def clean_env(monkeypatch):
    """Пустое окружение: .env разработчика не должен влиять на тесты."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.fixture
def filled_env(clean_env):
    clean_env.setenv("MISTRAL_API_KEY", "test-mistral")
    clean_env.setenv("QDRANT_URL", "https://example.invalid")
    clean_env.setenv("QDRANT_API_KEY", "test-qdrant")
    return clean_env


class FakePoint:
    def __init__(self, payload):
        self.payload = payload


class FakeHits:
    def __init__(self, payloads):
        self.points = [FakePoint(p) for p in payloads]


@pytest.fixture
def hits_factory():
    return FakeHits
