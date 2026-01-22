import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
    comfyui_output_dir: str = Field(..., min_length=1)
    comfyui_poll_interval_sec: int = Field(default=2, ge=1)
    comfyui_history_timeout_sec: int = Field(default=600, ge=1)
    comfyui_http_timeout_sec: float = Field(default=30.0, gt=0)
    comfyui_http_retries: int = Field(default=3, ge=0)
