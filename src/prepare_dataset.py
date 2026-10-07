"""Выборка тикетов из полного датасета: data/<источник> -> data/sample_10k.csv."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

COLUMNS = [
    "issue_description",
    "category",
    "resolution_notes",
    "status",
    "priority",
    "customer_satisfaction_score",
]

SOURCE = Path(os.environ.get("DATASET_PATH", "data/customer_support_tickets_200k.csv"))
TARGET = Path(os.environ.get("SAMPLE_PATH", "data/sample_10k.csv"))
SAMPLE_SIZE = int(os.environ.get("SAMPLE_SIZE", "10000"))
RANDOM_STATE = 42


def main() -> int:
    if not SOURCE.is_file():
        print(
            f"Не найден датасет {SOURCE}. Положи CSV с колонками "
            f"{', '.join(COLUMNS)} по этому пути или задай DATASET_PATH.",
            file=sys.stderr,
        )
        return 1

    df = pd.read_csv(SOURCE, usecols=COLUMNS)
    if df.empty:
        print(f"В файле {SOURCE} нет строк.", file=sys.stderr)
        return 1

    # sample(n=...) падает, если строк меньше, чем просят, - берём сколько есть.
    size = min(SAMPLE_SIZE, len(df))
    if size < SAMPLE_SIZE:
        print(f"В датасете только {len(df)} строк, беру их все вместо {SAMPLE_SIZE}.")
    sample_df = df.sample(n=size, random_state=RANDOM_STATE)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    sample_df.to_csv(TARGET, index=False, encoding="utf-8-sig")
    print(f"Количество строк: {len(sample_df)} -> {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
