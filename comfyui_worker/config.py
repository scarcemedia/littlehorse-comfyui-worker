import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
