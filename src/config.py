"""Настройки проекта: читаются из переменных окружения или из файла .env.

Все значения берутся лениво, поэтому модули можно импортировать (и тестировать)
без настроенных ключей.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_HELP = (
    "Скопируй .env.example в .env и заполни ключи "
    "(см. раздел «Запуск» в README.md)."
)


class ConfigError(RuntimeError):
    """Не хватает обязательной переменной окружения или значение некорректно."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value == "replace_me":
        raise ConfigError(f"Переменная окружения {name} не задана. {_HELP}")
    return value


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} должно быть целым числом, получено {raw!r}.") from exc
    if value < minimum:
        raise ConfigError(f"{name} должно быть >= {minimum}, получено {value}.")
    return value


@dataclass(frozen=True)
class Settings:
    """Собранная конфигурация одного запуска."""

    mistral_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    chat_model: str
    embed_model: str
    collection: str
    top_k: int
    max_synth_steps: int
    request_retries: int


def load_settings() -> Settings:
    """Собрать настройки. Бросает ConfigError с понятным текстом, если чего-то нет."""
    return Settings(
        mistral_api_key=_require("MISTRAL_API_KEY"),
        qdrant_url=_require("QDRANT_URL"),
        qdrant_api_key=_require("QDRANT_API_KEY"),
        chat_model=os.environ.get("MISTRAL_CHAT_MODEL", "mistral-small-2506"),
        embed_model=os.environ.get("MISTRAL_EMBED_MODEL", "mistral-embed"),
        collection=os.environ.get("QDRANT_COLLECTION", "support_tickets"),
        top_k=_int_env("RETRIEVAL_TOP_K", 20),
        max_synth_steps=_int_env("MAX_SYNTH_STEPS", 8, minimum=3),
        request_retries=_int_env("REQUEST_RETRIES", 4),
    )
