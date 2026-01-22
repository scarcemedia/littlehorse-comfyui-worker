import logging
import os

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
    comfyui_output_dir: str = Field(..., min_length=1)
    comfyui_poll_interval_sec: int = Field(default=2, ge=1)
    comfyui_history_timeout_sec: int = Field(default=600, ge=1)
    comfyui_http_timeout_sec: float = Field(default=30.0, gt=0)
    comfyui_http_retries: int = Field(default=3, ge=0)


def load_settings() -> Settings:
    base_url = os.getenv("COMFYUI_BASE_URL")
    output_dir = os.getenv("COMFYUI_OUTPUT_DIR")

    if not base_url or not output_dir:
        raise ValueError("COMFYUI_BASE_URL and COMFYUI_OUTPUT_DIR must be set")

    return Settings(
        comfyui_base_url=base_url,
        comfyui_output_dir=output_dir,
        comfyui_poll_interval_sec=int(os.getenv("COMFYUI_POLL_INTERVAL_SEC", "2")),
        comfyui_history_timeout_sec=int(os.getenv("COMFYUI_HISTORY_TIMEOUT_SEC", "600")),
        comfyui_http_timeout_sec=float(os.getenv("COMFYUI_HTTP_TIMEOUT_SEC", "30.0")),
        comfyui_http_retries=int(os.getenv("COMFYUI_HTTP_RETRIES", "3")),
    )
