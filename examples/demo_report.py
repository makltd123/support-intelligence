"""Собрать пример PDF-отчёта без ключей и без обращений к сети.

Нужен, чтобы посмотреть, как выглядит результат, до настройки Mistral и Qdrant:

    python examples/demo_report.py            # -> demo_report.pdf
    python examples/demo_report.py --out x.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from report_generator import generate_report  # noqa: E402

DEMO = {
    "problems": (
        "1. Вход в аккаунт\n"
        "- Клиенты не могут войти, несмотря на верный пароль (Тикеты 1, 4, 9, 12).\n"
        "- Не приходит код двухфакторной аутентификации после смены телефона "
        "(Тикеты 2, 7).\n\n"
        "2. Биллинг\n"
        "- Двойное списание за один период (Тикеты 3, 15).\n"
        "- Не приходит счёт для бухгалтерии (Тикет 8).\n\n"
        "3. Производительность\n"
        "- Отчёты грузятся дольше минуты (Тикеты 5, 11, 18)."
    ),
    "features": (
        "Экспорт в Excel — 4 упоминания (Тикеты 2, 6, 13, 19).\n"
        "Тёмная тема и уведомления в Telegram — 3 упоминания (Тикеты 1, 10, 17).\n"
        "Массовое редактирование записей — 2 упоминания (Тикеты 14, 20).\n"
        "Двусторонняя синхронизация — 2 упоминания (Тикеты 5, 16)."
    ),
    "sentiment": (
        "Негативный: 11 из 20 тикетов, в основном Authorization и Billing "
        "(Тикеты 1, 3, 4, 7, 9, 12, 15).\n"
        "Нейтральный: 6 тикетов, преимущественно Feature Request "
        "(Тикеты 2, 6, 13, 14, 19, 20).\n"
        "Позитивный: 3 тикета — благодарности после решения проблемы "
        "(Тикеты 8, 11, 18)."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="demo_report.pdf")
    args = parser.parse_args()
    print(f"PDF сохранён: {generate_report(DEMO, args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
