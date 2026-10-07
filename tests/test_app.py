import importlib


def test_import_does_not_start_server(filled_env, monkeypatch):
    """Регрессия: demo.launch() стоял на уровне модуля и запускался при импорте."""
    launched = []
    import gradio as gr
    monkeypatch.setattr(gr.Blocks, "launch", lambda self, *a, **k: launched.append(True))

    import app
    importlib.reload(app)
    assert launched == []
    assert callable(app.main)


def test_empty_question_is_rejected_without_api_calls(filled_env, monkeypatch):
    import app
    called = []
    monkeypatch.setattr(app, "synthesize", lambda *a, **k: called.append(True))
    problems, _f, _s, pdf = app.run_analysis("   ")
    assert "Введи вопрос" in problems
    assert pdf is None and called == []


def test_config_error_shown_in_ui(filled_env, monkeypatch):
    import app
    from config import ConfigError

    def boom(*_a, **_k):
        raise ConfigError("нет ключа MISTRAL_API_KEY")

    monkeypatch.setattr(app, "synthesize", boom)
    problems, _f, _s, pdf = app.run_analysis("вопрос")
    assert "MISTRAL_API_KEY" in problems and pdf is None


def test_unexpected_error_shown_in_ui(filled_env, monkeypatch):
    import app

    def boom(*_a, **_k):
        raise RuntimeError("qdrant недоступен")

    monkeypatch.setattr(app, "synthesize", boom)
    problems, _f, _s, pdf = app.run_analysis("вопрос")
    assert problems == app.ERROR_HINT and pdf is None


def test_each_run_writes_its_own_pdf(filled_env, monkeypatch, tmp_path):
    """Регрессия: все запуски писали в один report.pdf и перетирали друг друга."""
    monkeypatch.setenv("REPORT_DIR", str(tmp_path))
    import app
    importlib.reload(app)
    monkeypatch.setattr(app, "synthesize", lambda *a, **k: {
        "problems": "п", "features": "ф", "sentiment": "т"})

    paths = {app.run_analysis("вопрос")[3] for _ in range(3)}
    assert len(paths) == 3
    assert all(p.endswith(".pdf") for p in paths)
