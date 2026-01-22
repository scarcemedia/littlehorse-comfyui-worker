import pytest


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
