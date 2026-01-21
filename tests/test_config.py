import pytest


def test_config_requires_base_url() -> None:
    from pydantic import ValidationError

    from comfyui_worker.config import Settings

    with pytest.raises(ValidationError):
        Settings(comfyui_base_url=None)
