from typing import cast

import pytest


def test_config_requires_base_url() -> None:
    from pydantic import ValidationError

    from comfyui_worker.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            comfyui_base_url=cast(str, None),
            comfyui_output_dir="/outputs",
            comfyui_poll_interval_sec=2,
            comfyui_history_timeout_sec=600,
            comfyui_http_timeout_sec=30,
            comfyui_http_retries=3,
        )


def test_settings_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    from comfyui_worker.config import Settings

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    settings = Settings.from_env()
    assert settings.comfyui_base_url == "http://comfy"
    assert settings.comfyui_output_dir == "/outputs"
    assert settings.comfyui_poll_interval_sec == 2
    assert settings.comfyui_history_timeout_sec == 600
    assert settings.comfyui_http_timeout_sec == 30
    assert settings.comfyui_http_retries == 3


def test_settings_from_env_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from comfyui_worker.config import Settings

    monkeypatch.delenv("COMFYUI_BASE_URL", raising=False)
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    with pytest.raises(ValueError, match="COMFYUI_BASE_URL"):
        Settings.from_env()


def test_settings_from_env_requires_output_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    from comfyui_worker.config import Settings

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.delenv("COMFYUI_OUTPUT_DIR", raising=False)

    with pytest.raises(ValueError, match="COMFYUI_OUTPUT_DIR"):
        Settings.from_env()


def test_settings_from_env_rejects_invalid_int(monkeypatch: pytest.MonkeyPatch) -> None:
    from comfyui_worker.config import Settings

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")
    monkeypatch.setenv("COMFYUI_POLL_INTERVAL_SEC", "nope")

    with pytest.raises(ValueError, match="COMFYUI_POLL_INTERVAL_SEC"):
        Settings.from_env()
