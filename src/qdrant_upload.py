"""Загрузка векторов и payload-ов тикетов в Qdrant."""

from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from qdrant_client.models import Distance, PointStruct, VectorParams

from base_agent import qdrant, settings, with_retries

SAMPLE_PATH = Path(os.environ.get("SAMPLE_PATH", "data/sample_10k.csv"))
EMBEDDINGS_PATH = Path(os.environ.get("EMBEDDINGS_PATH", "data/embeddings.npy"))
BATCH_SIZE = int(os.environ.get("UPLOAD_BATCH_SIZE", "50"))
#: Если загрузка прервалась, укажи номер точки, с которой продолжить.
START_FROM = int(os.environ.get("UPLOAD_START_FROM", "0"))
PAUSE_SECONDS = float(os.environ.get("UPLOAD_PAUSE_SECONDS", "1"))

COLUMNS = [
    "issue_description",
    "category",
    "resolution_notes",
    "status",
    "priority",
    "customer_satisfaction_score",
]


def clean_value(value):
    """NaN и numpy-типы -> то, что корректно уедет в JSON payload Qdrant."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None
        return value
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def build_payload(row) -> dict:
    return {
        "text": clean_value(row["issue_description"]),
        "category": clean_value(row["category"]),
        "resolution_notes": clean_value(row["resolution_notes"]),
        "status": clean_value(row["status"]),
        "priority": clean_value(row["priority"]),
        "customer_satisfaction_score": clean_value(row["customer_satisfaction_score"]),
    }


def main() -> int:
    for path in (SAMPLE_PATH, EMBEDDINGS_PATH):
        if not path.is_file():
            print(
                f"Не найден {path}. Запусти src/prepare_dataset.py и src/embeddings.py.",
                file=sys.stderr,
            )
            return 1

    df = pd.read_csv(SAMPLE_PATH, usecols=COLUMNS)
    try:
        embeddings = np.load(EMBEDDINGS_PATH, allow_pickle=False)
    except ValueError:
        # Файлы, сохранённые старой версией скрипта, лежат как object-массив.
        print("Старый формат embeddings.npy (pickle), читаю с allow_pickle=True.")
        embeddings = np.asarray(
            list(np.load(EMBEDDINGS_PATH, allow_pickle=True)), dtype=np.float32
        )

    if len(embeddings) != len(df):
        print(
            f"Рассинхрон: {len(embeddings)} векторов против {len(df)} строк в CSV. "
            "Перегенерируй эмбеддинги для текущей выборки.",
            file=sys.stderr,
        )
        return 1

    client = qdrant()
    collection = settings().collection
    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(
                size=len(embeddings[0]), distance=Distance.COSINE
            ),
        )
        print(f"Коллекция {collection} создана.")

    for start in range(START_FROM, len(embeddings), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(embeddings))
        batch = [
            PointStruct(
                id=idx,
                vector=[float(x) for x in embeddings[idx]],
                payload=build_payload(df.iloc[idx]),
            )
            for idx in range(start, end)
        ]
        with_retries(
            lambda points=batch: client.upsert(collection_name=collection, points=points),
            what=f"upsert точек {start}-{end}",
        )
        print(f"Загружено: {end}/{len(embeddings)}")
        if end < len(embeddings) and PAUSE_SECONDS > 0:
            time.sleep(PAUSE_SECONDS)

    print("Загружено векторов:", len(embeddings) - START_FROM)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
