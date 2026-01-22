import pytest
from _pytest.monkeypatch import MonkeyPatch


def test_config_requires_base_url() -> None:
    from pydantic import ValidationError

    from comfyui_worker.config import Settings

    with pytest.raises(ValidationError):
        Settings(comfyui_base_url=None)


def test_config_accepts_all_fields() -> None:
    from comfyui_worker.config import Settings

    settings = Settings(
        comfyui_base_url="http://localhost:8188",
        comfyui_output_dir="/outputs",
    )
    assert settings.comfyui_base_url == "http://localhost:8188"
    assert settings.comfyui_output_dir == "/outputs"
    assert settings.comfyui_poll_interval_sec == 2
    assert settings.comfyui_history_timeout_sec == 600
    assert settings.comfyui_http_timeout_sec == 30.0
    assert settings.comfyui_http_retries == 3


def test_config_requires_output_dir() -> None:
    from pydantic import ValidationError

    from comfyui_worker.config import Settings

    with pytest.raises(ValidationError):
        Settings(comfyui_base_url="http://localhost:8188", comfyui_output_dir=None)


def test_load_settings_reads_env(monkeypatch: MonkeyPatch) -> None:
    from comfyui_worker.config import load_settings

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://test:8188")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/test/output")
    monkeypatch.setenv("COMFYUI_POLL_INTERVAL_SEC", "5")

    settings = load_settings()

    assert settings.comfyui_base_url == "http://test:8188"
    assert settings.comfyui_output_dir == "/test/output"
    assert settings.comfyui_poll_interval_sec == 5


def test_load_settings_raises_without_required_env(monkeypatch: MonkeyPatch) -> None:
    from comfyui_worker.config import load_settings

    monkeypatch.delenv("COMFYUI_BASE_URL", raising=False)
    monkeypatch.delenv("COMFYUI_OUTPUT_DIR", raising=False)

    with pytest.raises(ValueError):
        load_settings()
