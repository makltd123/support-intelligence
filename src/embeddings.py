"""Эмбеддинги текстов тикетов: data/sample_10k.csv -> data/embeddings.npy.

Считает батчами, умеет продолжить с места обрыва и сохраняет результат как
обычный двумерный массив float32 — без pickle, поэтому загружать его можно
с allow_pickle=False.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from base_agent import mistral_client, settings, with_retries

SAMPLE_PATH = Path(os.environ.get("SAMPLE_PATH", "data/sample_10k.csv"))
EMBEDDINGS_PATH = Path(os.environ.get("EMBEDDINGS_PATH", "data/embeddings.npy"))
PARTIAL_PATH = EMBEDDINGS_PATH.with_suffix(".partial.npy")
BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "50"))
PAUSE_SECONDS = float(os.environ.get("EMBED_PAUSE_SECONDS", "3"))


def embed_batch(texts: list[str]) -> list[list[float]]:
    cfg = settings()
    result = with_retries(
        lambda: mistral_client().embeddings.create(model=cfg.embed_model, inputs=texts),
        what=f"эмбеддинги батча из {len(texts)} текстов",
    )
    return [item.embedding for item in result.data]


def _load_partial() -> list[list[float]]:
    if not PARTIAL_PATH.is_file():
        return []
    done = np.load(PARTIAL_PATH, allow_pickle=False)
    print(f"Найден незаконченный прогон: {len(done)} векторов, продолжаю с него.")
    return [row.tolist() for row in done]


def main() -> int:
    if not SAMPLE_PATH.is_file():
        print(
            f"Не найден {SAMPLE_PATH}. Сначала запусти python src/prepare_dataset.py.",
            file=sys.stderr,
        )
        return 1

    df = pd.read_csv(SAMPLE_PATH, usecols=["issue_description"])
    texts = df["issue_description"].fillna("").astype(str).tolist()
    print(f"CSV загружен, строк: {len(texts)}")

    vectors = _load_partial()
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    while len(vectors) < len(texts):
        chunk = texts[len(vectors):len(vectors) + BATCH_SIZE]
        vectors.extend(embed_batch(chunk))
        # Промежуточное сохранение: обрыв на 9000-м векторе не стоит ещё 15 минут.
        PARTIAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.save(PARTIAL_PATH, np.asarray(vectors, dtype=np.float32))
        done_batches = (len(vectors) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Батч готов: {done_batches}/{total_batches} ({len(vectors)}/{len(texts)})")
        if len(vectors) < len(texts) and PAUSE_SECONDS > 0:
            time.sleep(PAUSE_SECONDS)

    array = np.asarray(vectors, dtype=np.float32)
    np.save(EMBEDDINGS_PATH, array)
    PARTIAL_PATH.unlink(missing_ok=True)
    print(f"Файл сохранён: {EMBEDDINGS_PATH}, форма {array.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
