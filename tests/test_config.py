import pytest

from config import ConfigError, load_settings


def test_missing_key_raises_readable_error(clean_env):
    with pytest.raises(ConfigError) as exc:
        load_settings()
    assert "MISTRAL_API_KEY" in str(exc.value)
    assert ".env" in str(exc.value)


def test_placeholder_value_is_rejected(filled_env):
    filled_env.setenv("QDRANT_API_KEY", "replace_me")
    with pytest.raises(ConfigError, match="QDRANT_API_KEY"):
        load_settings()


def test_defaults(filled_env):
    cfg = load_settings()
    assert cfg.collection == "support_tickets"
    assert cfg.top_k == 20
    assert cfg.chat_model == "mistral-small-2506"
    assert cfg.max_synth_steps >= 3


def test_overrides(filled_env):
    filled_env.setenv("QDRANT_COLLECTION", "other")
    filled_env.setenv("RETRIEVAL_TOP_K", "5")
    cfg = load_settings()
    assert cfg.collection == "other"
    assert cfg.top_k == 5


@pytest.mark.parametrize("value", ["abc", "0", "-3"])
def test_bad_top_k(filled_env, value):
    filled_env.setenv("RETRIEVAL_TOP_K", value)
    with pytest.raises(ConfigError, match="RETRIEVAL_TOP_K"):
        load_settings()
