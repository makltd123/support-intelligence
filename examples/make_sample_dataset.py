"""Сгенерировать небольшой синтетический датасет тикетов.

Нужен, чтобы прогнать весь конвейер (выборка → эмбеддинги → Qdrant), не
скачивая полный датасет на 74 МБ. Данные выдуманы этим скриптом, никаких
лицензионных ограничений на них нет.

    python examples/make_sample_dataset.py --rows 300 --out data/customer_support_tickets_200k.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

CATEGORIES = {
    "Authorization": [
        "Не могу войти в аккаунт, пароль точно верный",
        "После смены телефона не приходит код двухфакторной аутентификации",
        "Вход через Google перестал работать сегодня утром",
    ],
    "Billing": [
        "С карты списали дважды за один и тот же месяц",
        "Не приходит счёт на почту, нужен документ для бухгалтерии",
        "Хочу перейти на годовой тариф, но кнопка не работает",
    ],
    "Performance": [
        "Отчёты грузятся больше минуты, раньше было мгновенно",
        "Приложение зависает при загрузке файла больше 10 МБ",
        "Поиск по базе отваливается с таймаутом",
    ],
    "Data Sync": [
        "Данные с телефона не синхронизируются с веб-версией",
        "После обновления пропали последние три записи",
        "Синхронизация идёт только в одну сторону",
    ],
    "Feature Request": [
        "Добавьте, пожалуйста, экспорт в Excel",
        "Очень не хватает тёмной темы и уведомлений в Telegram",
        "Хочу массовое редактирование записей, по одной слишком долго",
    ],
}

RESOLUTIONS = [
    "Сбросили учётные данные, попросили войти заново",
    "Эскалировали в инженерный отдел, исправлено в последнем патче",
    "Объяснили расчёт стоимости, оформили возврат",
    "Передали пожелание продуктовой команде",
    "Перезапустили сервис синхронизации",
]

STATUSES = ["Open", "In Progress", "Pending Customer", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
COLUMNS = [
    "ticket_id", "category", "issue_description", "resolution_notes",
    "status", "priority", "customer_satisfaction_score",
]


def build_rows(rows: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for index in range(rows):
        category = rng.choice(list(CATEGORIES))
        out.append({
            "ticket_id": index + 1,
            "category": category,
            "issue_description": rng.choice(CATEGORIES[category]),
            "resolution_notes": rng.choice(RESOLUTIONS),
            "status": rng.choice(STATUSES),
            "priority": rng.choice(PRIORITIES),
            "customer_satisfaction_score": rng.choice([1, 2, 3, 4, 5, ""]),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data/customer_support_tickets_200k.csv")
    args = parser.parse_args()

    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(build_rows(args.rows, args.seed))

    print(f"Готово: {args.rows} тикетов -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
