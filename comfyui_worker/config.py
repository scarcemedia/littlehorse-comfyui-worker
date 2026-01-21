import logging
import os

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
    comfyui_output_dir: str = Field(..., min_length=1)
    comfyui_poll_interval_sec: int = Field(5, ge=1)
    comfyui_history_timeout_sec: int = Field(3600, ge=1)
    comfyui_http_timeout_sec: int = Field(30,  ge=1)
    comfyui_http_retries: int = Field(3, ge=0)

    @classmethod
    def from_env(cls: type["Settings"]) -> "Settings":
        logger.info("Loading settings from environment")
        comfyui_base_url = _get_required_env("COMFYUI_BASE_URL")
        comfyui_output_dir = _get_required_env("COMFYUI_OUTPUT_DIR")
        settings = cls(
            comfyui_base_url=comfyui_base_url,
            comfyui_output_dir=comfyui_output_dir,
            comfyui_poll_interval_sec=_get_int_env("COMFYUI_POLL_INTERVAL_SEC", 2),
            comfyui_history_timeout_sec=_get_int_env("COMFYUI_HISTORY_TIMEOUT_SEC", 600),
            comfyui_http_timeout_sec=_get_int_env("COMFYUI_HTTP_TIMEOUT_SEC", 30),
            comfyui_http_retries=_get_int_env("COMFYUI_HTTP_RETRIES", 3),
        )
        logger.info(
            "Loaded settings from environment",
            extra={"comfyui_base_url": comfyui_base_url, "comfyui_output_dir": comfyui_output_dir},
        )
        return settings


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer (got {value!r})") from exc


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"{name} must be set")
    return value
