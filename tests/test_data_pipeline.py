import importlib
import math

import numpy as np
import pandas as pd
import pytest

COLUMNS = [
    "issue_description", "category", "resolution_notes",
    "status", "priority", "customer_satisfaction_score",
]


def write_csv(path, rows):
    pd.DataFrame([
        {
            "issue_description": f"problem {i}",
            "category": "Billing",
            "resolution_notes": "fixed",
            "status": "Closed",
            "priority": "High",
            "customer_satisfaction_score": 4,
        }
        for i in range(rows)
    ]).to_csv(path, index=False)


def reload_prepare(monkeypatch, source, target, size=None):
    monkeypatch.setenv("DATASET_PATH", str(source))
    monkeypatch.setenv("SAMPLE_PATH", str(target))
    if size is not None:
        monkeypatch.setenv("SAMPLE_SIZE", str(size))
    import prepare_dataset
    return importlib.reload(prepare_dataset)


def test_sample_smaller_than_requested(tmp_path, monkeypatch, capsys):
    """Регрессия: df.sample(n=10000) падал на датасете меньше выборки."""
    source, target = tmp_path / "all.csv", tmp_path / "sample.csv"
    write_csv(source, 42)
    module = reload_prepare(monkeypatch, source, target, size=10000)
    assert module.main() == 0
    assert len(pd.read_csv(target)) == 42
    assert "беру их все" in capsys.readouterr().out


def test_sample_is_deterministic(tmp_path, monkeypatch):
    source, target = tmp_path / "all.csv", tmp_path / "s.csv"
    write_csv(source, 100)
    module = reload_prepare(monkeypatch, source, target, size=10)
    module.main()
    first = pd.read_csv(target)["issue_description"].tolist()
    module.main()
    assert pd.read_csv(target)["issue_description"].tolist() == first


def test_missing_source_reports_instead_of_traceback(tmp_path, monkeypatch, capsys):
    module = reload_prepare(monkeypatch, tmp_path / "nope.csv", tmp_path / "s.csv")
    assert module.main() == 1
    assert "Не найден датасет" in capsys.readouterr().err


def test_empty_source(tmp_path, monkeypatch, capsys):
    source = tmp_path / "all.csv"
    pd.DataFrame(columns=COLUMNS).to_csv(source, index=False)
    module = reload_prepare(monkeypatch, source, tmp_path / "s.csv")
    assert module.main() == 1
    assert "нет строк" in capsys.readouterr().err


# --- payload для Qdrant -------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    (math.nan, None),
    (np.float64("nan"), None),
    (None, None),
    (np.float64(4.0), 4.0),
    (np.int64(3), 3),
    ("Billing", "Billing"),
])
def test_clean_value(raw, expected, filled_env):
    import qdrant_upload
    assert qdrant_upload.clean_value(raw) == expected


def test_build_payload_drops_nan(filled_env):
    """Регрессия: NaN уезжал в payload как невалидный для JSON NaN."""
    import qdrant_upload
    row = pd.Series({
        "issue_description": "x", "category": "Auth", "resolution_notes": None,
        "status": "Open", "priority": "Low", "customer_satisfaction_score": math.nan,
    })
    payload = qdrant_upload.build_payload(row)
    assert payload["customer_satisfaction_score"] is None
    assert payload["resolution_notes"] is None
    assert payload["text"] == "x"
